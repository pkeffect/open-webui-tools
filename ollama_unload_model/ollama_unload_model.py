"""
title: Ollama Model Unloader
description: Ollama Model Unloader Button
author: pkeffect
author_url: https://github.com/pkeffect/open-webui-tools
funding_url: https://github.com/open-webui
required_open_webui_version: 0.6.0
version: 0.0.5
date: 2025-04-12
license: MIT
changelog:
  - 0.0.5 - Added more error handling and support for remote Ollama servers
  - 0.0.4 - Refactor
  - 0.0.3 - Added error reporting and better checks
  - 0.0.2 - Added status and progress
  - 0.0.1 - Initial upload to openwebui community.
features:
  - For local and remote Ollama hosts and custom ports (editable in valves)
  - Searches multiple locations for Ollama servers (automatic)
  - Displays progress and results
important:
  - Unloading models might not instantly release system RAM if models have spilled over from VRAM. Monitor your system resources
  - High CPU usage might persist temporarily after unloading if system RAM is heavily utilized
  - Avoid unloading models while they are actively generating text to prevent potential issues
  - If issues persist after unloading, consider restarting your Ollama service manually
  - For remote Ollama instances, ensure the Ollama API is accessible over your network and that any necessary firewalls are configured to allow connections

icon_url: data:image/svg+xml;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAs/AAALPwFJxTL7AAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAL5JREFUOI21kS0KQkEUhb8n+rpZxCQIWsVgdR8m3yIEV2CyG92BQQwGm8FmNrgBQZOicCxXkGGezjzwwmVgOH8zB/4xgobgLrgIzoKT4CiYuthyjkYfSG0BqnauQhPMBHJ2GfOEnUN+Cjqh5FRwcwTmMe5dj3stD1/y3PU8mLW1MAlJsPB8oKzSeojAQJDZ7j8Esp9kj9jWyBtBEksuCa7WSKuIe9vcx9FkExgKDoLKN5yvxvc0gVECj0IJQucFVwxtUwOOoygAAAAASUVORK5CYII=
requirements:
"""

import requests
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field
from typing import Callable, Any, Dict, List
import threading
import json

# Constants
TIMEOUT = 15
DEFAULT_OLLAMA_HOSTS = ["localhost", "127.0.0.1", "ollama", "host.docker.internal"]
DEFAULT_OLLAMA_PORT = 11434
requests.adapters.DEFAULT_TIMEOUT = TIMEOUT


class OllamaAPIClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def get_running_models(self) -> List[Dict]:
        try:
            response = requests.get(f"{self.base_url}/api/ps", timeout=TIMEOUT)
            response.raise_for_status()
            return (
                response.json().get("models", []) if response.status_code == 200 else []
            )
        except requests.exceptions.RequestException as e:
            print(f"Request error during get_running_models: {e}")
            return []
        except json.JSONDecodeError as e:
            print(
                f"JSON decode error during get_running_models: {e}, Response text: {response.text if 'response' in locals() else 'No response'}"
            )
            return []
        except Exception as e:
            print(f"Unexpected error during get_running_models: {e}")
            return []

    def unload_model(self, model_name: str) -> Dict:
        result = {"success": False, "model": model_name, "message": ""}
        try:
            if not any(m.get("model") == model_name for m in self.get_running_models()):
                result["message"] = "Model not found in running models list."
                return result

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": model_name, "prompt": " ", "keep_alive": 0},
                timeout=TIMEOUT,
            )
            response.raise_for_status()

            if response.status_code in [200, 204]:
                time.sleep(2)
                if not any(
                    m.get("model") == model_name for m in self.get_running_models()
                ):
                    result["success"] = True
                else:
                    result["success"] = False
                    result["message"] = "Model still running after unload attempt."
            else:
                result["message"] = (
                    f"Unload request failed with status code: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            result["message"] = f"Request error during unload_model: {e}"
            print(f"Request error during unload_model for {model_name}: {e}")
        except json.JSONDecodeError as e:
            result["message"] = (
                f"JSON decode error during unload_model: {e}, Response text: {response.text if 'response' in locals() else 'No response'}"
            )
            print(
                f"JSON decode error during unload_model for {model_name}: {e}, Response text: {response.text if 'response' in locals() else 'No response'}"
            )
        except Exception as e:
            result["message"] = f"Unexpected error during unload_model: {e}"
            print(f"Unexpected error during unload_model for {model_name}: {e}")
        return result


class OllamaUnloader:
    @staticmethod
    def run_stop_command(
        status_callback=None, ollama_hosts=None, ollama_port=DEFAULT_OLLAMA_PORT
    ) -> str:
        ollama_hosts = ollama_hosts or DEFAULT_OLLAMA_HOSTS
        total_unloaded = 0
        total_failed = 0
        all_errors = []

        for host in ollama_hosts:
            if status_callback:
                status_callback(f"Connecting to Ollama at {host}:{ollama_port}...")

            try:
                api_client = OllamaAPIClient(f"http://{host}:{ollama_port}")
                running_models = api_client.get_running_models()

                if not running_models:
                    if status_callback:
                        status_callback(
                            f"No running models found on {host}:{ollama_port}"
                        )
                    continue

                if status_callback:
                    status_callback(
                        f"Found {len(running_models)} running models on {host}:{ollama_port}"
                    )

                for model_info in running_models:
                    model_name = model_info.get("model")
                    if not model_name:
                        continue

                    if status_callback:
                        status_callback(f"Attempting to unload model: {model_name}")

                    unload_result = api_client.unload_model(model_name)
                    if unload_result["success"]:
                        total_unloaded += 1
                        if status_callback:
                            status_callback(
                                f"Successfully unloaded model: {model_name}"
                            )
                    else:
                        total_failed += 1
                        error_message = unload_result.get("message", "Unknown error")
                        all_errors.append(
                            f"Failed to unload model '{model_name}': {error_message}"
                        )
                        if status_callback:
                            status_callback(
                                f"Failed to unload model: {model_name} - {error_message}"
                            )

            except requests.exceptions.ConnectionError as e:
                error_msg = f"Connection error to Ollama at {host}:{ollama_port}: {e}"
                all_errors.append(error_msg)
                if status_callback:
                    status_callback(error_msg)
                continue
            except Exception as e:
                error_msg = (
                    f"Unexpected error while processing host {host}:{ollama_port}: {e}"
                )
                all_errors.append(error_msg)
                if status_callback:
                    status_callback(error_msg)
                continue

        if total_unloaded > 0 and total_failed == 0:
            return f"Successfully unloaded {total_unloaded} Ollama models."
        elif total_unloaded > 0:
            error_summary = "\n".join(all_errors)
            return f"Partially successful: Unloaded {total_unloaded} models, failed to unload {total_failed} models.\nErrors:\n{error_summary}"
        elif total_failed > 0:
            error_summary = "\n".join(all_errors)
            return f"Failed to unload {total_failed} models.\nErrors:\n{error_summary}"
        return "No running models found to unload across specified Ollama hosts."


class Action:
    class Valves(BaseModel):
        OLLAMA_HOSTS: List[str] = Field(
            default=DEFAULT_OLLAMA_HOSTS,
            description="List of Ollama host IPs or **hostnames** to connect to.  Supports both local addresses (localhost, 127.0.0.1, ollama) and remote addresses (e.g., 192.168.1.100, my-ollama-server.com).",  # Updated description for remote hosts
        )
        OLLAMA_PORT: int = Field(
            default=DEFAULT_OLLAMA_PORT,
            description="Port number for Ollama API (default: 11434)",
        )
        WAIT_BETWEEN_UNLOADS: int = Field(
            default=0, description="Seconds to wait between model unloads (default: 0)"
        )
        AUTO_CLOSE_OUTPUT: bool = Field(
            default=True,
            description="Whether to automatically close/collapse output when finished",
        )
        AUTO_CLOSE_DELAY: int = Field(
            default=3,
            description="Seconds to wait before automatically closing output (default: 3)",
        )

    def __init__(self):
        self.valves = self.Valves()
        # For tracking output closure
        self.close_task = None
        # For tracking event emitter
        self.event_emitter = None
        # For tracking operations
        self.is_operation_complete = False
        # For thread safety
        self.lock = threading.Lock()

    def create_message(
        self, type_name, description="", status="in_progress", done=False, close=False
    ):
        """Create a unified message structure for the event emitter"""
        message_id = f"msg_{int(time.time() * 1000)}"
        message = {
            "type": type_name,
            "message_id": message_id,
            "data": {
                "status": status,
                "description": description,
                "done": done,
                "close": close,
                "message_id": message_id,
            },
        }
        return message

    async def close_emitter_output(self):
        """Send a final message to close/collapse the output"""
        await asyncio.sleep(self.valves.AUTO_CLOSE_DELAY)

        if self.event_emitter and self.is_operation_complete:
            # Try several different approaches to signal completion:
            # 1. Send a special close message
            close_msg = self.create_message(
                "status", description="", status="complete", done=True, close=True
            )
            await self.event_emitter(close_msg)

            # 2. Send an empty message to signal end of stream (works in some systems)
            await self.event_emitter({})

            # 3. Try a close_output event type (might work in some implementations)
            await self.event_emitter(
                {"type": "close_output", "data": {"force_close": True}}
            )

            # 4. Try to clear all messages
            await self.event_emitter(
                {"type": "clear_all", "data": {"force_clear": True}}
            )

    async def action(
        self,
        body: dict,
        user: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
        __event_call__: Callable[[dict], Any] = None,
    ) -> None:
        if not __event_emitter__:
            return

        # Store the event emitter for later use
        self.event_emitter = __event_emitter__
        self.is_operation_complete = False

        try:
            # Initial status with warning about active generation
            initial_message = self.create_message(
                "status",
                "Starting Ollama model unloader...\n**Please ensure no models are actively generating text to avoid potential issues.**\n**For remote hosts, ensure network accessibility and firewall rules are configured correctly.**",
            )  # Added network/firewall warning for remote hosts
            await __event_emitter__(initial_message)

            status_updates = {}

            def status_callback(text):
                status_updates["current"] = text

            def run_unloader():
                try:
                    result = OllamaUnloader.run_stop_command(
                        status_callback=status_callback,
                        ollama_hosts=self.valves.OLLAMA_HOSTS,
                        ollama_port=self.valves.OLLAMA_PORT,
                    )
                    status_updates["final_result"] = result
                    return result
                except Exception as e:
                    error_msg = f"Error in unloader thread: {str(e)}"
                    status_updates["final_result"] = error_msg
                    return error_msg

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_unloader)
                last_status = None

                while not future.done():
                    if "current" in status_updates:
                        current_status = status_updates["current"]
                        if current_status != last_status:
                            await __event_emitter__(
                                self.create_message("status", current_status)
                            )
                            last_status = current_status
                    await asyncio.sleep(0.5)

            # Final status
            final_result = status_updates.get("final_result", future.result())
            status_type = (
                "warning"
                if any(
                    x in final_result
                    for x in ["Failed", "Error", "Partially successful"]
                )
                else "complete"
            )

            # Send final status with done=True
            final_message = self.create_message(
                "status", description=final_result, status=status_type, done=True
            )
            await __event_emitter__(final_message)

            # Mark operation as complete
            self.is_operation_complete = True

            # Schedule auto-close if enabled
            if self.valves.AUTO_CLOSE_OUTPUT:
                # Create a task to close the output after a delay
                self.close_task = asyncio.create_task(self.close_emitter_output())

        except Exception as e:
            # Error message
            error_message = self.create_message(
                "status", description=f"Error: {str(e)}", status="error", done=True
            )
            await __event_emitter__(error_message)

            # Mark operation as complete even on error
            self.is_operation_complete = True

            # Schedule auto-close on error too
            if self.valves.AUTO_CLOSE_OUTPUT:
                self.close_task = asyncio.create_task(self.close_emitter_output())
