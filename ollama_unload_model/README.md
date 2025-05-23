# 🚀 Ollama Model Unloader

![Ollama Model Unloader](https://raw.githubusercontent.com/pkeffect/open-webui-tools/main/ollama_unload_model/icon.png)

A powerful Open WebUI extension that helps you free up system resources by unloading Ollama models when they're not in use.

## 📋 Overview

Ollama Model Unloader is a simple but effective tool that allows you to unload AI models from memory with just a click. This is particularly useful when:

- You need to free up RAM or VRAM on your system
- You want to switch between different models without restarting Ollama
- You're experiencing system slowdowns due to multiple loaded models

## ✨ Features

- 🖥️ Works with both local and remote Ollama hosts
- 🔍 Automatically searches multiple locations for Ollama servers
- 🔌 Supports custom port configurations
- 📊 Displays real-time progress and results
- 🔄 Automatically collapses output panel when finished (configurable)
- 🛡️ Robust error handling for a smooth experience

## ⚙️ Configuration Options

You can customize the behavior of the Ollama Model Unloader through the following settings:

| Setting | Description | Default Value |
|---------|-------------|---------------|
| `OLLAMA_HOSTS` | List of Ollama host IPs or hostnames to connect to | `["localhost", "127.0.0.1", "ollama", "host.docker.internal"]` |
| `OLLAMA_PORT` | Port number for Ollama API | `11434` |
| `WAIT_BETWEEN_UNLOADS` | Seconds to wait between model unloads | `0` |
| `AUTO_CLOSE_OUTPUT` | Whether to automatically close/collapse output when finished | `True` |
| `AUTO_CLOSE_DELAY` | Seconds to wait before automatically closing output | `3` |

## ⚠️ Important Notes

- Unloading models might not instantly release system RAM if models have spilled over from VRAM. Monitor your system resources.
- High CPU usage might persist temporarily after unloading if system RAM is heavily utilized.
- Avoid unloading models while they are actively generating text to prevent potential issues.
- If issues persist after unloading, consider restarting your Ollama service manually.
- For remote Ollama instances, ensure the Ollama API is accessible over your network and that any necessary firewalls are configured to allow connections.

## 📦 Installation

1. In Open WebUI, navigate to the Extensions panel
2. Find "Ollama Model Unloader" in the community extensions
3. Click "Install"
4. The tool will now appear in your toolbar for easy access

## 📝 Changelog

- **0.0.5** - Added more error handling and support for remote Ollama servers
- **0.0.4** - Refactor
- **0.0.3** - Added error reporting and better checks
- **0.0.2** - Added status and progress
- **0.0.1** - Initial upload to openwebui community

## 🔧 How It Works

When activated, the tool:

1. Searches for Ollama servers on the configured hosts and port
2. Gets a list of all currently running models
3. Sends an API request to unload each model by setting `keep_alive` to 0
4. Verifies that models are properly unloaded
5. Provides status updates throughout the process

## 💻 Technical Details

The unloader works by making HTTP requests to the Ollama API. Specifically, it:

- Uses `GET /api/ps` to find running models
- Uses `POST /api/generate` with `keep_alive: 0` to unload models
- Includes comprehensive error handling for network issues, API errors, and unexpected scenarios

## 📞 Support

- 📧 **Email**: pkeffect [at] gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/pkeffect/open-webui-tools/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/pkeffect/open-webui-tools/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/pkeffect/open-webui-tools/wiki)

## 👨‍💻 Author

Developed by [pkeffect](https://github.com/pkeffect/)

## 🔗 Links

- [Project Repository](https://github.com/pkeffect/open-webui-tools/tree/main/ollama_unload_model)
- [Open WebUI](https://github.com/open-webui)

## 📄 License

This project is licensed under the MIT License

---

**Required Open WebUI Version:** 0.6.0 or higher
