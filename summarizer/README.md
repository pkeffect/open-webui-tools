# 📄 Conversation Summarizer

> **Intelligent conversation summarization for OpenWebUI with on-demand and automatic modes**

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/your-repo/conversation-summarizer)
[![OpenWebUI](https://img.shields.io/badge/OpenWebUI-Compatible-green.svg)](https://github.com/open-webui/open-webui)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🌟 Overview

**Conversation Summarizer** is a production-ready OpenWebUI filter that provides intelligent conversation summarization with both on-demand commands and automatic context management. Built with robust conversation analysis, efficient resource management, and enterprise-grade reliability.

### ✨ Key Features

- 📝 **Smart Summarization** - Intelligent conversation turn detection and context extraction
- ⚡ **Dual Modes** - On-demand commands (`!summarize`) and automatic context injection
- 🔧 **Robust Architecture** - Professional error handling, async task management, and memory safety
- 🎯 **Conversation Analysis** - Accurate turn counting that handles complex conversation patterns
- 🛡️ **Resource Protection** - Configurable limits, efficient processing, and memory leak prevention
- 📊 **Performance Optimized** - Smart caching, minimal overhead, and scalable design
- 🎨 **Customizable Templates** - Flexible prompt templates for different summarization styles
- 💾 **Enterprise Ready** - Comprehensive logging, validation, and production safeguards

---

## 🚨 Important: Key Concepts

> **💡 UNDERSTANDING TURNS:** The system intelligently tracks conversation "turns" (user message + assistant response pairs) rather than just counting individual messages. This provides accurate context assessment even with complex conversation patterns.

---

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [🏗️ Installation](#️-installation)
- [🎯 Core Concepts](#-core-concepts)
  - [Conversation Turn Detection](#conversation-turn-detection)
  - [Summarization Modes](#summarization-modes)
  - [Template System](#template-system)
- [⚙️ Configuration](#️-configuration)
  - [Basic Settings](#basic-settings)
  - [Advanced Options](#advanced-options)
  - [Performance Tuning](#performance-tuning)
- [💡 Usage Guide](#-usage-guide)
  - [On-Demand Summarization](#on-demand-summarization)
  - [Automatic Summarization](#automatic-summarization)
  - [Template Customization](#template-customization)
- [🏗️ System Architecture](#️-system-architecture)
  - [Turn Detection Logic](#turn-detection-logic)
  - [Resource Management](#resource-management)
  - [Error Handling](#error-handling)
- [🔧 Troubleshooting](#-troubleshooting)
- [🚀 Advanced Features](#-advanced-features)
- [🤝 Contributing](#-contributing)

---

## 🚀 Quick Start

### 1️⃣ Install the Filter
1. Copy the complete filter code from the repository
2. Add as a new filter in OpenWebUI Admin Panel
3. Enable the filter in your settings

### 2️⃣ Try On-Demand Summarization
```
!summarize
```
Generates a summary of your recent conversation history.

### 3️⃣ Enable Automatic Mode (Optional)
1. Go to Filter Settings → Conversation Summarizer
2. Enable `auto_summarize_enabled`
3. Set `auto_summarize_after_turns` (default: 5)
4. Automatic summaries will be injected as context

### 4️⃣ Customize Templates (Optional)
Modify the summary instruction templates to match your preferred style and format.

---

## 🏗️ Installation

### Prerequisites
- OpenWebUI instance with filter support
- Administrator access to manage filters
- Python environment with required dependencies

### Step-by-Step Installation

1. **Access Filter Management**
   - Navigate to OpenWebUI Settings
   - Go to Admin Panel → Filters
   - Click "Add Filter"

2. **Install Conversation Summarizer**
   - Copy the complete filter code
   - Paste into the filter editor
   - Set filter name: "Conversation Summarizer"
   - Save and enable the filter

3. **Initial Configuration**
   - Review default settings in the Valves section
   - Adjust `keyword_prefix` if desired (default: `!`)
   - Configure `past_turns_to_summarize` (default: 5)
   - Set `auto_summarize_after_turns` if using automatic mode

4. **Test Installation**
   ```
   !summarize
   ```
   If you see "No history to summarize", the installation is working correctly.

---

## 🎯 Core Concepts

### Conversation Turn Detection

The **Conversation Turn System** is the foundation of accurate summarization:

#### 🔄 What is a Turn?
- **Complete Turn**: User message → Assistant response
- **Incomplete Turn**: User message without assistant response
- **Complex Patterns**: Handles multiple consecutive messages, interruptions, and system messages

#### 🧠 Smart Detection
```python
@dataclass
class ConversationTurn:
    user_message: Dict
    assistant_message: Optional[Dict] = None
    is_complete: bool = False
```

#### 🎯 Why This Matters
- **Accurate Context**: Only complete exchanges provide meaningful context
- **Robust Counting**: Works with various conversation patterns
- **Efficient Processing**: Focuses on meaningful conversation units

### Summarization Modes

#### 📝 On-Demand Mode
```
!summarize
```
- **Trigger**: Manual command
- **Scope**: Last N completed turns (configurable)
- **Output**: Dedicated summary response
- **Use Case**: Periodic review, meeting notes, context refresh

#### ⚡ Automatic Mode
- **Trigger**: After N completed turns
- **Scope**: Recent conversation history
- **Output**: Context prefix + original query
- **Use Case**: Long conversations, context maintenance, seamless experience

### Template System

#### 🎨 Customizable Prompts
**On-Demand Template**
```
Please provide a concise summary of the key points from the following 
conversation history. Focus on the main topics, decisions, and questions. 
Present the summary clearly under a '### Conversation Summary' heading.

--- BEGIN CONVERSATION HISTORY TO SUMMARIZE ---
{history_snippet}
--- END CONVERSATION HISTORY TO SUMMARIZE ---
```

**Automatic Template**
```
Before addressing the user's latest query, please first provide a concise summary 
of the key points from our recent conversation history. This summary will help maintain context. 
Present the summary clearly under a '### Recent Context Summary' heading.

--- BEGIN RECENT HISTORY TO SUMMARIZE ---
{history_snippet}
--- END RECENT HISTORY TO SUMMARIZE ---

After providing the summary, then address the user's latest message:
```

---

## ⚙️ Configuration

### Basic Settings

#### 🎛️ Core Configuration
| Setting | Default | Description |
|---------|---------|-------------|
| `enabled` | `true` | Enable/disable the summarization filter |
| `keyword_prefix` | `!` | Command prefix for summarization trigger |
| `summary_command_keyword` | `summarize` | Command word for on-demand summarization |
| `case_sensitive_commands` | `false` | Whether commands are case-sensitive |

#### 📊 Summarization Control
| Setting | Default | Description |
|---------|---------|-------------|
| `past_turns_to_summarize` | `5` | Number of recent turns to include in summary |
| `auto_summarize_enabled` | `false` | Enable automatic summarization |
| `auto_summarize_after_turns` | `5` | Turns before automatic summarization triggers |

### Advanced Options

#### 🛡️ Resource Protection
```python
max_history_messages = 100        # Limit processed messages for performance
status_message_timeout_ms = 3000  # UI notification timeout
show_status_messages = true       # Enable/disable UI feedback
```

#### 📝 Template Customization
```python
summary_instruction_template_on_demand = """
Your custom on-demand summary template with {history_snippet} placeholder
"""

summary_instruction_template_auto = """
Your custom automatic summary template with {history_snippet} placeholder
"""
```

### Performance Tuning

#### ⚡ Optimization Settings
- **Message Limiting**: `max_history_messages` prevents processing excessive history
- **Efficient Filtering**: Only processes user/assistant messages
- **Smart Caching**: Regex patterns compiled once at initialization
- **Resource Cleanup**: Automatic async task management

#### 📊 Memory Management
- **Bounded Processing**: Configurable limits on conversation size
- **Async Safety**: Proper task lifecycle management
- **Resource Cleanup**: Automatic cleanup on filter destruction

---

## 💡 Usage Guide

### On-Demand Summarization

#### 📝 Basic Command
```
!summarize
```

#### 🔍 What Happens
1. **History Analysis**: Extracts last N completed conversation turns
2. **Context Formatting**: Converts messages to readable text format
3. **Template Application**: Applies on-demand summary template
4. **LLM Processing**: Sends formatted request to language model
5. **Summary Generation**: Returns structured summary response

#### 💬 Example Flow
```
User: How do I optimize database queries?
Assistant: [Detailed response about database optimization]

User: What about indexing strategies?
Assistant: [Response about indexing]

User: !summarize
Assistant: ### Conversation Summary

We discussed database optimization techniques, focusing on:
- Query optimization fundamentals and best practices
- Indexing strategies for improved performance
- Specific recommendations for your use case
```

### Automatic Summarization

#### ⚡ Configuration
```python
auto_summarize_enabled = true
auto_summarize_after_turns = 5
past_turns_to_summarize = 3
```

#### 🔄 Automatic Flow
1. **Turn Monitoring**: Tracks completed conversation turns
2. **Threshold Check**: Triggers when configured turn count reached
3. **Context Injection**: Prepends summary to user's query
4. **Seamless Experience**: User sees enhanced response with context

#### 💬 Example Flow
After 5+ completed turns:
```
User: What's the latest best practice for this?
Assistant: ### Recent Context Summary

Based on our recent discussion about database optimization:
- We covered query optimization and indexing strategies
- Discussed performance monitoring tools
- Explored caching mechanisms

Now addressing your question about latest best practices:
[Response to actual query]
```

### Template Customization

#### 🎨 Custom Formats
**Executive Summary Style**
```python
summary_instruction_template_on_demand = """
Provide an executive summary of our conversation in the following format:

## Executive Summary
**Key Topics:** [List main topics]
**Decisions Made:** [List any decisions or conclusions]
**Action Items:** [List any next steps or recommendations]
**Questions Remaining:** [List unresolved questions]

{history_snippet}
"""
```

**Technical Documentation Style**
```python
summary_instruction_template_on_demand = """
Generate technical documentation for our discussion:

### Technical Discussion Summary
1. **Problem Statement**: [What problem was addressed]
2. **Solutions Discussed**: [Technical solutions covered]
3. **Implementation Details**: [Specific technical details]
4. **Recommendations**: [Final recommendations]

{history_snippet}
"""
```

---

## 🏗️ System Architecture

### Turn Detection Logic

#### 🧠 Intelligent Parsing
```python
def _extract_conversation_turns(self, messages: List[Dict]) -> List[ConversationTurn]:
    """Extract conversation turns from message history, handling various patterns."""
    turns = []
    current_turn = None
    
    # Filter and process messages
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
    
    return turns
```

#### 🎯 Pattern Handling
- **Sequential Conversations**: Standard user/assistant alternation
- **Multiple User Messages**: Handles consecutive user inputs
- **System Interruptions**: Filters out system messages
- **Incomplete Turns**: Manages partial conversations gracefully

### Resource Management

#### 🛡️ Memory Protection
```python
@asynccontextmanager
async def _managed_task(self, coro):
    """Context manager for tracking and cleaning up async tasks."""
    task = asyncio.create_task(coro)
    self._active_tasks.add(task)
    try:
        yield task
        await task
    finally:
        self._active_tasks.discard(task)
```

#### ⚡ Performance Features
- **Bounded Processing**: `max_history_messages` limit
- **Efficient Filtering**: Early termination on limits
- **Smart Compilation**: Regex patterns compiled once
- **Task Tracking**: Async task lifecycle management

### Error Handling

#### 🔒 Comprehensive Safety
- **Input Validation**: Pydantic validators for all settings
- **Graceful Degradation**: Continues operation on non-critical errors
- **Resource Cleanup**: Ensures no resource leaks
- **Logging Integration**: Structured error reporting

#### 🛠️ Recovery Mechanisms
- **Configuration Validation**: Prevents invalid settings
- **Safe Defaults**: Fallback to working configurations
- **Error Isolation**: Errors don't break entire system
- **Status Reporting**: Clear error communication to users

---

## 🔧 Troubleshooting

### Common Issues

#### ❌ "No history to summarize"
**Problem**: `!summarize` returns no history message
```
Diagnosis:
- Check if you have completed conversation turns
- Verify past_turns_to_summarize setting
- Ensure you have actual user/assistant exchanges

Solution:
- Have at least one complete conversation turn
- Adjust past_turns_to_summarize if needed
- Check that filter is processing messages correctly
```

#### ❌ Commands not recognized
**Problem**: `!summarize` doesn't trigger summarization
```
Diagnosis:
- Check keyword_prefix setting (default: "!")
- Verify summary_command_keyword setting
- Ensure case_sensitive_commands matches usage
- Confirm filter is enabled

Solution:
- Verify configuration: keyword_prefix = "!"
- Check command: summary_command_keyword = "summarize"
- Test with exact case if case_sensitive_commands = true
- Enable filter in OpenWebUI settings
```

#### ❌ Automatic summarization not working
**Problem**: Auto-summary doesn't trigger after expected turns
```
Diagnosis:
- Check auto_summarize_enabled = true
- Verify auto_summarize_after_turns setting
- Count actual completed turns (user + assistant pairs)
- Check conversation pattern

Solution:
- Enable: auto_summarize_enabled = true
- Set appropriate: auto_summarize_after_turns = 5
- Ensure you have complete conversation turns
- Review conversation structure for interruptions
```

### Debug Mode

#### 🐛 Enable Detailed Logging
```python
# In filter configuration
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 📊 Monitoring Information
- **Turn Detection**: Detailed turn parsing logs
- **Configuration**: Setting validation messages
- **Performance**: Processing timing information
- **Error Context**: Comprehensive error details

### Recovery Procedures

#### 🔄 Reset Configuration
1. **Disable Filter**: Turn off in OpenWebUI settings
2. **Check Logs**: Review any error messages
3. **Reset Settings**: Return to default configuration
4. **Re-enable**: Activate filter with fresh settings

#### 🛠️ Manual Intervention
1. **Validate Settings**: Use Pydantic validators
2. **Test Commands**: Try basic `!summarize`
3. **Check Permissions**: Ensure proper filter access
4. **Review Integration**: Verify OpenWebUI compatibility

---

## 🚀 Advanced Features

### Custom Turn Detection

#### 🎯 Specialized Patterns
For specific conversation patterns, you can extend the turn detection logic:

```python
# Custom turn detection for specialized use cases
def _custom_turn_detection(self, messages: List[Dict]) -> List[ConversationTurn]:
    # Implement specialized logic for your conversation patterns
    pass
```

### Integration Patterns

#### 🔗 Workflow Integration
- **Meeting Summaries**: Periodic summarization during long discussions
- **Research Sessions**: Context maintenance across multiple topics
- **Teaching/Learning**: Progress tracking and knowledge retention
- **Project Management**: Decision tracking and action item extraction

#### 📊 Analytics Integration
- **Conversation Metrics**: Track summary frequency and effectiveness
- **Context Analysis**: Monitor conversation complexity and patterns
- **Performance Monitoring**: Resource usage and processing efficiency

### Custom Templates

#### 📝 Domain-Specific Formats
**Medical/Clinical Style**
```python
summary_template = """
## Clinical Discussion Summary
**Chief Concerns:** [Primary issues discussed]
**Assessment:** [Key findings and analysis]
**Plan:** [Recommended actions]
**Follow-up:** [Next steps or monitoring]

{history_snippet}
"""
```

**Legal/Compliance Style**
```python
summary_template = """
## Legal Discussion Summary
**Matter:** [Case or issue discussed]
**Key Points:** [Important legal considerations]
**Precedents:** [Relevant cases or regulations cited]
**Recommendations:** [Legal advice or next steps]

{history_snippet}
"""
```

---

## 🤝 Contributing

### Development Setup

#### 🛠️ Local Development
1. **Fork Repository** - Create your development copy
2. **Install Dependencies** - Set up Python environment
3. **Test Environment** - Use OpenWebUI test instance
4. **Follow Standards** - Use provided code style

### Code Standards

#### 📋 Development Guidelines
- **Type Hints**: Use comprehensive type annotations
- **Error Handling**: Implement proper exception management
- **Logging**: Use structured logging instead of print statements
- **Testing**: Include unit tests for new functionality
- **Documentation**: Update README and inline documentation

#### 🧪 Testing Requirements
- **Unit Tests**: Cover core functionality
- **Integration Tests**: Test with OpenWebUI
- **Performance Tests**: Verify resource usage
- **Edge Cases**: Handle unusual conversation patterns

### Bug Reports

#### 🐛 Reporting Issues
Include the following information:
- **OpenWebUI Version**: Your OpenWebUI version
- **Filter Configuration**: Relevant valve settings
- **Conversation Context**: Pattern that caused the issue
- **Error Messages**: Complete error logs
- **Expected Behavior**: What should happen instead
- **Reproduction Steps**: How to recreate the issue

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenWebUI Team** - For the excellent platform and filter system
- **Community Contributors** - For feedback and suggestions
- **Beta Testers** - For identifying edge cases and improvements

---

## 📞 Support

- **GitHub Issues** - [Report bugs and request features](https://github.com/your-repo/conversation-summarizer/issues)
- **Discussions** - [Community support and questions](https://github.com/your-repo/conversation-summarizer/discussions)
- **Documentation** - This README and comprehensive inline documentation

---

<div align="center">

**📄 Enhance your OpenWebUI conversations with intelligent summarization!**

*Smart turn detection • Dual operation modes • Enterprise-grade reliability*

[⭐ Star on GitHub](https://github.com/your-repo/conversation-summarizer) • [🐛 Report Bug](https://github.com/your-repo/conversation-summarizer/issues) • [💡 Request Feature](https://github.com/your-repo/conversation-summarizer/issues)

</div>