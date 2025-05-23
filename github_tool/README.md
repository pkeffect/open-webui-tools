# 🐙 GitHub Repository Context Filter for Open WebUI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open WebUI](https://img.shields.io/badge/Open%20WebUI-Compatible-blue.svg)](https://github.com/open-webui/open-webui)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)

> 🚀 **Transform your LLM into a code-aware assistant with complete repository context!**

This powerful Open WebUI filter plugin automatically loads and caches your entire GitHub repository, providing your LLM with **perfect fidelity access** to every file, line, and character in your codebase. No more "I don't have access to your repository" responses!

---

## ✨ Key Features

### 🎯 **Perfect Code Fidelity**
- 📄 **Zero truncation** - Complete files preserved exactly as they are
- 🔤 **Perfect whitespace** - All spaces, tabs, and indentation maintained
- 📝 **Exact line endings** - Preserves `\n`, `\r\n`, `\r` as-is in repository
- 🌐 **Multi-encoding support** - UTF-8, Latin-1, CP1252, and more
- 📦 **Large file support** - Up to 5MB per file (configurable)

### 🔄 **Easy Toggle Control**
- 🐙 **Visual toggle** - Easy on/off switch with emoji indicators
- ⚫ **Status display** - Clear enabled/disabled state
- 🔄 **Instant control** - No restart required
- 📊 **Real-time feedback** - Status updates in chat interface

### 📊 **Comprehensive Statistics**
- 📁 **File counts** - Total files cached vs found
- 📝 **Line metrics** - Exact line counts across repository  
- 🔤 **Character stats** - Total characters and size in MB
- 📄 **File analysis** - Largest files and type breakdown
- 🏷️ **Type distribution** - Files by extension with counts

### 🚀 **Advanced Features**
- ⚡ **Smart caching** - Configurable cache duration
- 🔍 **Intelligent filtering** - Skip binaries, build folders, etc.
- 🌳 **File tree display** - Complete repository structure
- 🎛️ **User controls** - Per-user enable/disable options
- 🐛 **Debug mode** - Comprehensive logging for troubleshooting

---

## 🚀 Quick Start

### 1. 📥 Installation

1. **Download the filter** - Copy the complete Python code
2. **Save as `.py` file** in your Open WebUI functions directory
3. **Install dependencies** - Only `requests` is required (auto-installed)
4. **Enable in Open WebUI** - Go to Functions menu and enable the filter

### 2. 🔧 Basic Configuration

Navigate to **Admin Panel > Functions > GitHub Repository Context Filter**:

```yaml
# Required Settings
github_token: "ghp_your_personal_access_token_here"
github_repo: "owner/repository-name"
github_branch: "main"
```

### 3. 🎯 Generate GitHub Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click **"Generate new token (fine-grained)"**
3. Select your repository
4. Grant **"Contents: Read"** permission
5. Copy the token to the `github_token` valve

### 4. ✅ Test the Setup

Start a new chat and send any message. You should see:

```
🟢 GitHub Context ACTIVE: owner/repository-name
📁 21 files | 📝 2,847 lines | 🔤 156,892 chars
💾 0.46 MB | 📄 Largest: main.js (45,231 bytes)
```

---

## ⚙️ Configuration Reference

### 🔧 **Core Settings (Valves)**

| Setting | Default | Description |
|---------|---------|-------------|
| `github_token` | `""` | 🔑 GitHub Personal Access Token |
| `github_repo` | `""` | 📁 Repository in format "owner/repo" |
| `github_branch` | `"main"` | 🌿 Branch to fetch from |
| `max_file_size` | `5242880` | 📦 Max file size (5MB) |
| `cache_duration` | `3600` | ⏰ Cache duration in seconds |
| `auto_load_on_startup` | `true` | 🚀 Auto-load files on conversation start |

### 🎛️ **Filter Controls**

| Setting | Default | Description |
|---------|---------|-------------|
| `excluded_extensions` | `.png,.jpg,...` | 🚫 File extensions to skip |
| `excluded_dirs` | `node_modules,.git,...` | 📂 Directories to exclude |
| `include_file_tree` | `true` | 🌳 Show repository structure |
| `preserve_line_endings` | `true` | 📝 Keep exact line endings |
| `debug_mode` | `true` | 🐛 Enable debug logging |

### 👤 **User Settings (UserValves)**

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_github_context` | `true` | ✅ Per-user enable/disable |
| `custom_context_prompt` | `""` | 💬 Custom prompt to add |

---

## 🎮 Using the Toggle Feature

### 🔄 **Quick Toggle**

The filter includes an easy toggle control:

- **🐙 Enabled** - Filter is active and injecting context
- **⚫ Disabled** - Filter is inactive, normal LLM behavior

### 📱 **Toggle Interface**

In Open WebUI, you'll see the filter with visual indicators:

```
🐙 GitHub Repository Context Filter  [Toggle]
```

Click the toggle to switch states instantly!

### 🎯 **Status Messages**

When toggling, you'll see confirmation:

```bash
✅ GitHub Context Filter 🟢 ENABLED
❌ GitHub Context Filter 🔴 DISABLED
```

---

## 📊 Repository Statistics

The filter provides comprehensive statistics about your repository:

### 📈 **Loading Statistics**

```
📊 Repository Loaded: microsoft/vscode
📁 Files: 21 cached (45 total found) 
📝 Lines: 2,847
🔤 Characters: 156,892
💾 Size: 487,234 bytes (0.46 MB)
📄 Largest: main.js (45,231 bytes)
🏷️ Types: .js(8), .py(5), .md(3), .json(2), .yml(1)
```

### 🔍 **Active Context Display**

```
🟢 GitHub Context ACTIVE: owner/repository
📁 21 files | 📝 2,847 lines | 🔤 156,892 chars
💾 0.46 MB | 📄 Largest: main.js (45,231 bytes)
```

### 📋 **What Statistics Mean**

- **📁 Files cached vs found** - How many files were loaded vs total discovered
- **📝 Lines** - Total lines of code across all files
- **🔤 Characters** - Total character count (exact)
- **💾 Size** - Total repository size in bytes and MB
- **📄 Largest file** - Biggest file by size
- **🏷️ File types** - Breakdown by extension

---

## 🛠️ Advanced Usage

### 🎯 **Perfect for Code Tasks**

With complete repository context, your LLM can now:

#### 🔍 **Code Analysis**
```
"Analyze the authentication flow in this codebase"
"Find all functions that handle user input validation" 
"Show me the database schema definitions"
```

#### 🐛 **Debugging**
```
"There's an error on line 42 of api/users.js, help me debug it"
"Why is the login function failing?"
"Find potential security vulnerabilities"
```

#### 🔄 **Refactoring**
```
"Help me refactor the user service to use async/await"
"Suggest improvements to the database queries"
"How can I optimize this component?"
```

#### 📚 **Documentation**
```
"Generate API documentation for all endpoints"
"Create a README for the authentication module"
"Document the database schema"
```

### 🎛️ **Custom Context Prompts**

Add specific instructions via UserValves:

```
Custom Context Prompt: "You are a senior developer reviewing this codebase for security vulnerabilities. Focus on input validation and authentication."
```

### 🔄 **Manual Reload**

Force refresh the repository cache:

```python
await reload_repository()
```

---

## 🔧 Troubleshooting

### ❌ **Common Issues**

#### **"Repository loaded: 0 files cached"**
- ✅ Check your GitHub token has `Contents: Read` permission
- ✅ Verify repository name format: `owner/repo`
- ✅ Ensure branch exists and is accessible
- ✅ Check if all files are being excluded by filters

#### **"I don't have access to repositories"**
- ✅ Confirm the toggle is **enabled** (🐙 icon)
- ✅ Check UserValves `enable_github_context` is `true`
- ✅ Verify repository loaded successfully in logs
- ✅ Try a new conversation to trigger first-message detection

#### **"Context truncated due to length limit"**
- ✅ This message was removed - full context is now always preserved
- ✅ Large repositories may hit LLM token limits
- ✅ Consider using more targeted queries
- ✅ Adjust file exclusion filters if needed

### 🐛 **Debug Mode**

Enable `debug_mode` in valves for detailed logging:

```python
DEBUG: Total messages in body: 3
DEBUG: Message roles: ['system', 'user', 'assistant']
DEBUG: Repository cache keys: ['src/main.js', 'README.md', ...]
```

### 📊 **Performance Tips**

- **📁 Exclude unnecessary directories** - `node_modules`, `dist`, `build`
- **🚫 Skip binary files** - Images, executables, archives
- **⏰ Adjust cache duration** - Longer for stable repos
- **📦 Monitor file sizes** - Large files may slow loading

---

## 🔒 Security & Privacy

### 🛡️ **Token Security**

- 🔑 **Fine-grained tokens** - Use minimal required permissions
- ⏰ **Token expiration** - Set reasonable expiry dates
- 🔒 **Private repositories** - Token must have access
- 🚫 **Never share tokens** - Keep them secure

### 🔐 **Data Handling**

- 💾 **Local caching** - Files cached in memory only
- ⏰ **Temporary storage** - Cache expires based on settings
- 🚫 **No external transmission** - Data stays in your Open WebUI instance
- 🔄 **Manual control** - Toggle off anytime

### 🔍 **Access Control**

- 👤 **User-level controls** - Each user can enable/disable
- 🎛️ **Admin configuration** - Centralized settings management
- 🔄 **Real-time toggle** - Instant enable/disable

---

## 🎯 Best Practices

### 📋 **Repository Preparation**

1. **🧹 Clean up your repo** - Remove unnecessary files
2. **📝 Update documentation** - Ensure README and docs are current
3. **🏷️ Use .gitignore** - Exclude build artifacts and dependencies
4. **📦 Organize structure** - Clear folder hierarchy helps LLM understanding

### 🎛️ **Configuration Optimization**

1. **🔧 Tune exclusions** - Skip irrelevant file types
2. **⏰ Set appropriate cache** - Balance freshness vs performance
3. **📊 Monitor statistics** - Watch for excessive file counts
4. **🐛 Enable debug mode** - For initial setup and troubleshooting

### 💬 **Effective Prompting**

1. **🎯 Be specific** - Reference exact files or functions
2. **📍 Use line numbers** - "Line 42 in src/api.js"
3. **🔍 Ask for analysis** - "Analyze the error handling pattern"
4. **📚 Request documentation** - "Document this API endpoint"

---

## 🔧 Technical Details

### 📋 **Requirements**

- 🐍 **Python 3.8+**
- 📦 **requests library** (auto-installed)
- 🌐 **Internet access** for GitHub API
- 🔑 **GitHub Personal Access Token**

### 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Message  │───▶│  Filter (Inlet)  │───▶│   LLM + Context │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  GitHub API      │
                       │  Repository      │
                       │  File Cache      │
                       └──────────────────┘
```

### ⚡ **Performance**

- **🚀 Smart caching** - Files loaded once per cache duration
- **🔄 Incremental loading** - Progress updates during load
- **💾 Memory efficient** - Files stored in compressed format
- **⏱️ Async operations** - Non-blocking repository loading

### 🔍 **API Usage**

The filter uses these GitHub API endpoints:

- **Tree API** - `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1`
- **Contents API** - `GET /repos/{owner}/{repo}/contents/{path}?ref={branch}`

Rate limits apply based on your GitHub token type.

---

## 🤝 Contributing

### 🛠️ **Development**

1. **🍴 Fork the repository**
2. **🌿 Create a feature branch**
3. **✨ Make improvements**
4. **🧪 Test thoroughly**
5. **📤 Submit a pull request**

### 🐛 **Bug Reports**

Please include:

- 📋 **Open WebUI version**
- 🐍 **Python version**
- 🔧 **Filter configuration** (without sensitive tokens)
- 📊 **Debug logs** (if available)
- 🔄 **Steps to reproduce**

### 💡 **Feature Requests**

We welcome suggestions for:

- 🚀 **Performance improvements**
- 🎯 **New filtering options**
- 📊 **Additional statistics**
- 🎛️ **UI enhancements**
- 🔧 **Configuration options**

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 GitHub Repository Context Filter

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 Acknowledgments

- 🌟 **Open WebUI Team** - For the amazing platform
- 🐙 **GitHub** - For the comprehensive API
- 👥 **Community Contributors** - For feedback and improvements
- 🚀 **You** - For using this filter to enhance your development workflow!

---

## 📞 Support

- 📧 **Email**: pkeffect [at] gmail.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/pkeffect/open-webui-tools/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/pkeffect/open-webui-tools/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/pkeffect/open-webui-tools/wiki)

---

<div align="center">

### 🚀 **Transform your LLM into a code-aware assistant today!**

**Give your AI perfect repository context and watch your development productivity soar!** 🌟

[![Open WebUI](https://img.shields.io/badge/Compatible-Open%20WebUI-blue.svg)](https://github.com/open-webui/open-webui)
[![GitHub](https://img.shields.io/badge/View%20on-GitHub-black.svg)](https://github.com)

</div>

---

*Made with ❤️ for the Open WebUI community*
