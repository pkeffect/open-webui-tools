"""
title: Notification Example Test
author: pkeffect
author_url: https://github.com/pkeffect
funding_url: https://github.com/open-webui
required_open_webui_version: 0.6.0
version: 0.0.2
date: 2025-03-15
license: MIT
description: Demonstrates Success, Error, Default (Blue), and Warning notifications with sequentially numbered IDs, now with customizable messages via Valves.
features:
  - Customizable notification messages via Valves for each notification type.
"""

import asyncio
import time
from typing import Callable, Any, Dict
from pydantic import BaseModel, Field
import threading


class Action:
    class Valves(BaseModel):
        success_message: str = Field(
            default="[SUCCESS] ✅ Success Notification: Demonstrates a success message, typically displayed in green.",
            description="Content for the Success notification.",
        )
        error_message: str = Field(
            default="[ERROR] ❌ Error Notification: Demonstrates an error message, typically displayed in red.",
            description="Content for the Error notification.",
        )
        default_message: str = Field(
            default="[BLUE-DEFAULT] 📰 Default Notification: Demonstrates the default notification style, typically displayed in blue.",
            description="Content for the Default (Blue) notification.",
        )
        warning_message: str = Field(
            default="[WARNING-TYPE] ⚠️ Warning Notification: Demonstrates a warning message, typically displayed in yellow/orange.",
            description="Content for the Warning notification.",
        )
        wait_duration: int = Field(
            default=1,
            description="Seconds to wait between each notification display.",
        )
        auto_close_delay: int = Field(
            default=3,
            description="Seconds to wait before automatically closing the notification output (set to 0 to disable auto-close).",
        )
        AUTO_CLOSE_OUTPUT: bool = Field(
            default=True,
            description="Whether to automatically close/collapse output when finished",
        )

    def __init__(self):
        self.valves = self.Valves()
        # For tracking output closure
        self.close_task = None
        # For tracking event emitter
        self.event_emitter = None
        # For tracking operations
        self.is_operation_complete = False
        # For thread safety (though not strictly needed in this example, good practice)
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
        await asyncio.sleep(self.valves.auto_close_delay)

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

        notification_counter = 1  # Initialize a counter for notification IDs

        try:
            # --- Success Notification (Green - type=success) - #001 ---
            notification_id = f"#{notification_counter:03d}"
            notification_counter += 1
            await __event_emitter__(
                {
                    "type": "notification",
                    "data": {
                        "content": f"{notification_id} {self.valves.success_message}",
                        "type": "success",
                    },
                }
            )
            await asyncio.sleep(self.valves.wait_duration)

            # --- Error Notification (Red - type=error) - #002 ---
            notification_id = f"#{notification_counter:03d}"
            notification_counter += 1
            await __event_emitter__(
                {
                    "type": "notification",
                    "data": {
                        "content": f"{notification_id} {self.valves.error_message}",
                        "type": "error",
                    },
                }
            )
            await asyncio.sleep(self.valves.wait_duration)

            # --- Default Notification (Blue Style) - #003 ---
            notification_id = f"#{notification_counter:03d}"
            notification_counter += 1
            await __event_emitter__(
                {
                    "type": "notification",
                    "data": {
                        "content": f"{notification_id} {self.valves.default_message}",
                    },
                }
            )
            await asyncio.sleep(self.valves.wait_duration)

            # --- Warning Notification (type=warning) - #004 ---
            notification_id = f"#{notification_counter:03d}"
            notification_counter += 1
            await __event_emitter__(
                {
                    "type": "notification",
                    "data": {
                        "content": f"{notification_id} {self.valves.warning_message}",
                        "type": "warning",
                    },
                }
            )
            await asyncio.sleep(self.valves.wait_duration)

            # Final success status
            final_message = self.create_message(
                "status",
                description="Notification tests completed successfully: Demonstrated Success, Error, Default, and Warning notifications.",
                status="complete",
                done=True,
            )
            await __event_emitter__(final_message)

            # Mark operation as complete
            self.is_operation_complete = True

            # Schedule auto-close if enabled
            if self.valves.AUTO_CLOSE_OUTPUT and self.valves.auto_close_delay > 0:
                # Create a task to close the output after a delay
                self.close_task = asyncio.create_task(self.close_emitter_output())

        except Exception as e:
            # Handle any exceptions and send an error status
            error_message = self.create_message(
                "status", description=f"Error: {str(e)}", status="error", done=True
            )
            await __event_emitter__(error_message)

            # Mark operation as complete even on error
            self.is_operation_complete = True

            # Schedule auto-close on error too if enabled
            if self.valves.AUTO_CLOSE_OUTPUT and self.valves.auto_close_delay > 0:
                self.close_task = asyncio.create_task(self.close_emitter_output())
