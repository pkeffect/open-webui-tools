# 🔔 Notification Example Test

A simple Open WebUI extension that demonstrates different notification types with customizable messages.

## 📋 Overview

Notification Example Test is a developer utility that showcases the four main notification styles available in Open WebUI. It's perfect for:

- Learning how to implement notifications in your own Open WebUI extensions
- Testing how notifications appear in your current Open WebUI setup
- Demonstrating the notification system to others

## ✨ Features

- 🟢 **Success Notifications** - Green-styled positive confirmations
- 🔴 **Error Notifications** - Red-styled error alerts
- 🔵 **Default Notifications** - Blue-styled standard messages
- 🟠 **Warning Notifications** - Yellow/orange-styled warning alerts
- 🔢 **Sequential IDs** - Each notification is numbered sequentially
- ✏️ **Customizable Messages** - Edit the content of each notification type
- ⏱️ **Timing Controls** - Adjust the delay between notifications
- 🔄 **Auto-Close** - Automatically close the output panel when finished

## ⚙️ Configuration Options

You can customize the behavior of the Notification Example Test through the following settings:

| Setting | Description | Default Value |
|---------|-------------|---------------|
| `success_message` | Content for the Success notification | "[SUCCESS] ✅ Success Notification: Demonstrates a success message, typically displayed in green." |
| `error_message` | Content for the Error notification | "[ERROR] ❌ Error Notification: Demonstrates an error message, typically displayed in red." |
| `default_message` | Content for the Default (Blue) notification | "[BLUE-DEFAULT] 📰 Default Notification: Demonstrates the default notification style, typically displayed in blue." |
| `warning_message` | Content for the Warning notification | "[WARNING-TYPE] ⚠️ Warning Notification: Demonstrates a warning message, typically displayed in yellow/orange." |
| `wait_duration` | Seconds to wait between each notification display | `1` |
| `auto_close_delay` | Seconds to wait before automatically closing the notification output (set to 0 to disable auto-close) | `3` |
| `AUTO_CLOSE_OUTPUT` | Whether to automatically close/collapse output when finished | `True` |

## 📦 Installation

1. In Open WebUI, navigate to the Extensions panel
2. Find "Notification Example Test" in the community extensions
3. Click "Install"
4. The tool will now appear in your toolbar for easy access

## 🚀 Usage

1. Simply click the Notification Example Test button in Open WebUI
2. Watch as each notification type appears in sequence
3. Note the different styling for each notification type:
   - Success notifications (green)
   - Error notifications (red)
   - Default notifications (blue)
   - Warning notifications (yellow/orange)
4. Each notification will have a sequential ID (e.g., #001, #002, etc.)

## 💻 Technical Details

The extension demonstrates how to create notifications in Open WebUI by:

1. Creating notification events with the appropriate `type` parameter
2. Setting the notification content and style
3. Managing the display timing with `asyncio.sleep()`
4. Adding automatic cleanup with the `close_emitter_output()` function

## 📊 Notification Types

Here's a summary of the notification types demonstrated:

| Type | Style | Purpose |
|------|-------|---------|
| `success` | Green | Positive confirmation messages |
| `error` | Red | Error or failure messages |
| (default) | Blue | Standard informational messages |
| `warning` | Yellow/Orange | Warning or caution messages |

## 📝 Changelog

- **0.0.2** - Added customizable messages via Valves
- **0.0.1** - Initial version

## 👨‍💻 Author

Developed by [pkeffect](https://github.com/pkeffect/)

## 🔗 Links

- [Project Repository](https://github.com/pkeffect/open-webui-tools/tree/main/notifications_example_test)
- [Open WebUI](https://github.com/open-webui)

## 📄 License

This project is licensed under the MIT License

---

**Required Open WebUI Version:** 0.6.0 or higher
