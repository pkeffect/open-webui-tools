"""
title: On-Demand & Auto Summarizer
author: pkeffect
author_url: https://github.com/pkeffect
funding_url: https://github.com/openwebui
version: 0.3.0
description: Summarizes recent conversation history either on-demand via a command (e.g., !summarize) or automatically after a set number of turns.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Callable, Any
import re
import time
import asyncio
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Represents a complete conversation turn (user message + assistant response)"""
    user_message: Dict
    assistant_message: Optional[Dict] = None
    is_complete: bool = False

class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )
        enabled: bool = Field(
            default=True, description="Enable/disable the summarization filter."
        )
        keyword_prefix: str = Field(
            default="!",
            description="Prefix character(s) that trigger commands (e.g., '!summarize')."
        )
        summary_command_keyword: str = Field(
            default="summarize",
            description="Keyword (without prefix) to trigger on-demand summarization."
        )
        case_sensitive_commands: bool = Field(
            default=False, description="Whether command matching is case-sensitive."
        )
        past_turns_to_summarize: int = Field(
            default=5,
            description="Number of recent past conversation turns to include in the summary."
        )
        summary_instruction_template_on_demand: str = Field(
            default=(
                "Please provide a concise summary of the key points from the following "
                "conversation history. Focus on the main topics, decisions, and questions. "
                "Present the summary clearly under a '### Conversation Summary' heading.\n\n"
                "--- BEGIN CONVERSATION HISTORY TO SUMMARIZE ---\n"
                "{history_snippet}\n"
                "--- END CONVERSATION HISTORY TO SUMMARIZE ---"
            ),
            description="Template for instructing the LLM for on-demand summarization. Use {history_snippet} as a placeholder."
        )
        summary_instruction_template_auto: str = Field(
            default=(
                "Before addressing the user's latest query, please first provide a concise summary "
                "of the key points from our recent conversation history. This summary will help maintain context. "
                "Present the summary clearly under a '### Recent Context Summary' heading.\n\n"
                "--- BEGIN RECENT HISTORY TO SUMMARIZE ---\n"
                "{history_snippet}\n"
                "--- END RECENT HISTORY TO SUMMARIZE ---\n\n"
                "After providing the summary, then address the user's latest message:\n"
            ),
            description="Template for instructing the LLM for automatic summarization. Use {history_snippet} as a placeholder."
        )
        auto_summarize_enabled: bool = Field(
            default=False,
            description="Enable automatic summarization after a certain number of turns."
        )
        auto_summarize_after_turns: int = Field(
            default=5,
            description="Number of completed conversation turns before automatic summarization is triggered."
        )
        show_status_messages: bool = Field(
            default=True,
            description="Show UI status messages for summarization actions."
        )
        status_message_timeout_ms: int = Field(
            default=3000,
            description="Timeout in milliseconds for status messages."
        )
        max_history_messages: int = Field(
            default=100,
            description="Maximum number of messages to process for efficiency."
        )

        @validator('past_turns_to_summarize')
        def validate_past_turns(cls, v):
            if v < 1:
                raise ValueError("past_turns_to_summarize must be at least 1")
            if v > 20:
                raise ValueError("past_turns_to_summarize should not exceed 20 for performance")
            return v

        @validator('auto_summarize_after_turns')
        def validate_auto_turns(cls, v):
            if v < 1:
                raise ValueError("auto_summarize_after_turns must be at least 1")
            return v

        @validator('keyword_prefix')
        def validate_prefix(cls, v):
            if not v or len(v.strip()) == 0:
                raise ValueError("keyword_prefix cannot be empty")
            return v

        @validator('summary_command_keyword')
        def validate_command(cls, v):
            if not v or len(v.strip()) == 0:
                raise ValueError("summary_command_keyword cannot be empty")
            return v

    def __init__(self):
        self.valves = self.Valves()
        self.toggle = True
        self.icon = "📄"
        
        # Compile command pattern once
        self._command_pattern = None
        self._compile_command_pattern()
        
        # Track active tasks for cleanup
        self._active_tasks = set()

    def _compile_command_pattern(self):
        """Compile the regex pattern for the summary command."""
        try:
            prefix = re.escape(self.valves.keyword_prefix)
            command = re.escape(self.valves.summary_command_keyword)
            flags = 0 if self.valves.case_sensitive_commands else re.IGNORECASE
            
            self._command_pattern = re.compile(
                rf"^{prefix}{command}\b\s*",
                flags
            )
            logger.debug(f"Compiled command pattern: {self._command_pattern.pattern}")
        except Exception as e:
            logger.error(f"Error compiling command pattern: {e}")
            self._command_pattern = None

    def _extract_conversation_turns(self, messages: List[Dict]) -> List[ConversationTurn]:
        """Extract conversation turns from message history, handling various patterns."""
        turns = []
        current_turn = None
        
        # Filter out system messages and limit history for performance
        user_assistant_messages = [
            msg for msg in messages[-self.valves.max_history_messages:] 
            if msg.get("role") in ["user", "assistant"]
        ]
        
        for message in user_assistant_messages:
            role = message.get("role")
            
            if role == "user":
                # Start new turn or replace incomplete turn
                current_turn = ConversationTurn(user_message=message)
            elif role == "assistant" and current_turn is not None:
                # Complete the current turn
                current_turn.assistant_message = message
                current_turn.is_complete = True
                turns.append(current_turn)
                current_turn = None
        
        # Add incomplete turn if exists
        if current_turn is not None:
            turns.append(current_turn)
        
        return turns

    def _get_completed_turns_count(self, messages: List[Dict], exclude_last: int = 0) -> int:
        """Count completed conversation turns, optionally excluding last N messages."""
        if exclude_last > 0:
            messages = messages[:-exclude_last]
        
        turns = self._extract_conversation_turns(messages)
        return sum(1 for turn in turns if turn.is_complete)

    def _get_history_for_summary(self, messages: List[Dict], exclude_last: int = 0) -> List[Dict]:
        """Get recent history messages for summarization."""
        if exclude_last > 0:
            messages = messages[:-exclude_last]
        
        turns = self._extract_conversation_turns(messages)
        completed_turns = [turn for turn in turns if turn.is_complete]
        
        # Take the most recent completed turns
        turns_to_include = completed_turns[-self.valves.past_turns_to_summarize:]
        
        # Flatten back to message list
        history_messages = []
        for turn in turns_to_include:
            history_messages.append(turn.user_message)
            if turn.assistant_message:
                history_messages.append(turn.assistant_message)
        
        return history_messages

    def _format_message_content(self, content) -> str:
        """Safely extract text content from various message formats."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle multimodal content
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return " ".join(text_parts) if text_parts else "[Non-text content]"
        else:
            return str(content) if content else ""

    def _format_messages_to_text(self, messages: List[Dict]) -> str:
        """Format messages to readable text efficiently."""
        if not messages:
            return ""
        
        formatted_parts = []
        for msg in messages:
            role = msg.get("role", "unknown").capitalize()
            content = self._format_message_content(msg.get("content", ""))
            if content.strip():  # Only include non-empty content
                formatted_parts.append(f"{role}: {content}")
        
        return "\n".join(formatted_parts)

    @asynccontextmanager
    async def _managed_task(self, coro):
        """Context manager for tracking and cleaning up async tasks."""
        task = asyncio.create_task(coro)
        self._active_tasks.add(task)
        try:
            yield task
            await task
        except asyncio.CancelledError:
            logger.debug("Task was cancelled")
        except Exception as e:
            logger.error(f"Task failed: {e}")
        finally:
            self._active_tasks.discard(task)

    async def _emit_status_message(
        self,
        emitter: Optional[Callable[[dict], Any]],
        description: str,
        status_type: str = "info"
    ):
        """Emit a simple status message without complex tracking."""
        if not emitter or not self.valves.show_status_messages:
            return

        message_id = f"summarizer_{int(time.time() * 1000)}"
        status_message = {
            "type": "status",
            "message_id": message_id,
            "data": {
                "status": status_type,
                "description": description,
                "timeout": self.valves.status_message_timeout_ms,
            },
        }
        
        try:
            await emitter(status_message)
        except Exception as e:
            logger.error(f"Error emitting status message: {e}")

    def _is_summary_command(self, content: str) -> bool:
        """Check if message content is a summary command."""
        if not isinstance(content, str) or not self._command_pattern:
            return False
        return bool(self._command_pattern.match(content.strip()))

    async def inlet(self, body: dict, __event_emitter__: Optional[Callable[[dict], Any]] = None, __user__: Optional[dict] = None) -> dict:
        if not self.valves.enabled or not self.toggle:
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        last_message = messages[-1]
        last_content = last_message.get("content", "")

        # Handle on-demand summarization command
        if self._is_summary_command(last_content):
            logger.info("Processing on-demand summary command")
            await self._emit_status_message(__event_emitter__, "⏳ Preparing summary...")

            history_messages = self._get_history_for_summary(messages, exclude_last=1)
            
            if not history_messages:
                await self._emit_status_message(__event_emitter__, "⚠️ No history to summarize", "warning")
                messages[-1]["content"] = "There is no prior conversation history available to summarize."
                return body

            history_text = self._format_messages_to_text(history_messages)
            summary_instruction = self.valves.summary_instruction_template_on_demand.format(
                history_snippet=history_text
            )
            
            messages[-1]["content"] = summary_instruction
            await self._emit_status_message(__event_emitter__, "✅ Summary request prepared", "success")
            return body

        # Handle automatic summarization
        if self.valves.auto_summarize_enabled:
            completed_turns = self._get_completed_turns_count(messages, exclude_last=1)
            
            if completed_turns >= self.valves.auto_summarize_after_turns:
                logger.info(f"Triggering auto-summary after {completed_turns} completed turns")
                await self._emit_status_message(__event_emitter__, "⏳ Adding context summary...")
                
                history_messages = self._get_history_for_summary(messages, exclude_last=1)
                
                if history_messages:
                    history_text = self._format_messages_to_text(history_messages)
                    summary_prefix = self.valves.summary_instruction_template_auto.format(
                        history_snippet=history_text
                    )
                    
                    original_content = self._format_message_content(last_content)
                    messages[-1]["content"] = f"{summary_prefix}{original_content}"
                    await self._emit_status_message(__event_emitter__, "✅ Context summary added", "success")

        return body

    async def outlet(self, body: dict, __event_emitter__: Optional[Callable[[dict], Any]] = None, __user__: Optional[dict] = None) -> dict:
        # Clean implementation - just pass through
        return body

    def __del__(self):
        """Cleanup any remaining tasks on destruction."""
        for task in self._active_tasks:
            if not task.done():
                task.cancel()