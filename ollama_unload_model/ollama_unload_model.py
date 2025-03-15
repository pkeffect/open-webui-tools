"""
title: Ollama Model Unloader
author: pkeffect
author_url: https://github.com/pkeffect
funding_url: https://github.com/open-webui
required_open_webui_version: 0.5.20
version: 0.0.5
date: 2025-03-14
license: MIT
description: Adds Ollama Model Unloader to UI Extras with API-based model management
requirements:
"""

import requests
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field
from typing import Callable, Any, Dict, List

# Constants
TIMEOUT = 15
DEFAULT_OLLAMA_HOSTS = ["localhost", "127.0.0.1", "ollama", "host.docker.internal"]
requests.adapters.DEFAULT_TIMEOUT = TIMEOUT


class OllamaAPIClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def get_running_models(self) -> List[Dict]:
        try:
            response = requests.get(f"{self.base_url}/api/ps", timeout=TIMEOUT)
            return (
                response.json().get("models", []) if response.status_code == 200 else []
            )
        except:
            return []

    def unload_model(self, model_name: str) -> Dict:
        result = {"success": False, "model": model_name, "message": ""}
        try:
            if not any(m.get("model") == model_name for m in self.get_running_models()):
                return result

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": model_name, "prompt": " ", "keep_alive": 0},
                timeout=TIMEOUT,
            )

            if response.status_code in [200, 204]:
                time.sleep(2)
                result["success"] = not any(
                    m.get("model") == model_name for m in self.get_running_models()
                )
        except:
            pass
        return result


class OllamaUnloader:
    @staticmethod
    def run_stop_command(status_callback=None, ollama_hosts=None) -> str:
        ollama_hosts = ollama_hosts or DEFAULT_OLLAMA_HOSTS
        total_unloaded = total_failed = 0

        for host in ollama_hosts:
            if status_callback:
                status_callback(f"Connecting to Ollama at {host}...")

            try:
                api_client = OllamaAPIClient(f"http://{host}:11434")
                running_models = api_client.get_running_models()

                if not running_models:
                    continue

                for model_info in running_models:
                    model_name = model_info.get("model")
                    if not model_name:
                        continue

                    if status_callback:
                        status_callback(f"Unloading model: {model_name}")

                    unload_result = api_client.unload_model(model_name)
                    total_unloaded += 1 if unload_result["success"] else 0
                    total_failed += 0 if unload_result["success"] else 1
            except:
                continue

        if total_unloaded > 0 and total_failed == 0:
            return f"Successfully unloaded {total_unloaded} Ollama models"
        elif total_unloaded > 0:
            return f"Partially successful: Unloaded {total_unloaded} models, failed to unload {total_failed} models"
        elif total_failed > 0:
            return f"Failed to unload {total_failed} models"
        return "No running models found to unload"


class Action:
    class Valves(BaseModel):
        OLLAMA_HOSTS: List[str] = Field(
            default=DEFAULT_OLLAMA_HOSTS,
            description="List of Ollama host IPs to connect to",
        )
        WAIT_BETWEEN_UNLOADS: int = Field(
            default=0, description="Seconds to wait between model unloads (default: 0)"
        )

    def __init__(self):
        self.valves = self.Valves()

    def status_object(
        self, description="Processing", status="in_progress", done=False
    ) -> Dict:
        return {
            "type": "status",
            "data": {"status": status, "description": description, "done": done},
        }

    async def action(
        self,
        body: dict,
        user: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
        __event_call__: Callable[[dict], Any] = None,
    ) -> None:
        try:
            if __event_emitter__:
                await __event_emitter__(
                    self.status_object("Initializing Ollama model unloader...")
                )

            status_updates = {}

            def status_callback(text):
                status_updates["current"] = text

            def run_unloader():
                try:
                    result = OllamaUnloader.run_stop_command(
                        status_callback=status_callback,
                        ollama_hosts=self.valves.OLLAMA_HOSTS,
                    )
                    status_updates["final_result"] = result
                    return result
                except Exception:
                    error_msg = "Error in unloader thread"
                    status_updates["final_result"] = error_msg
                    return error_msg

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_unloader)
                while not future.done():
                    if "current" in status_updates and __event_emitter__:
                        await __event_emitter__(
                            self.status_object(status_updates["current"])
                        )
                    await asyncio.sleep(0.5)

            if __event_emitter__:
                final_message = status_updates.get("final_result", future.result())
                status = (
                    "warning"
                    if any(x in final_message for x in ["Failed", "Error"])
                    else "complete"
                )
                await __event_emitter__(
                    self.status_object(final_message, status=status, done=True)
                )

        except Exception:
            if __event_emitter__:
                await __event_emitter__(
                    self.status_object(
                        "Error in action method", status="error", done=True
                    )
                )
