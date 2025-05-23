"""
title: GitHub Repository Context Filter
description: A filter that loads and caches GitHub repository files for full context mode with toggle control
author: pkeffect
author_url: https://github.com/pkeffect/
project_url: https://github.com/pkeffect/open-webui-tools/tree/main/github_tool
funding_url: https://github.com/open-webui
required_open_webui_version: 0.6.0
version: 0.0.1
date: 2025-05-23
license: MIT
changelog:
  - 0.0.1 - initial upload

requirements: requests
"""

import os
import base64
import json
import time
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

# Try to import requests, fallback if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests library not available. GitHub functionality will be limited.")


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="Priority level for the filter operations. Lower values are processed first."
        )
        
        github_token: str = Field(
            default="",
            description="GitHub Personal Access Token for API authentication"
        )
        
        github_repo: str = Field(
            default="",
            description="GitHub repository in format 'owner/repo' (e.g., 'microsoft/vscode')"
        )
        
        github_branch: str = Field(
            default="main",
            description="Branch to fetch files from (default: main)"
        )
        
        max_file_size: int = Field(
            default=5242880,  # 5MB - increased for code files
            description="Maximum file size in bytes to include (default: 5MB)"
        )
        
        excluded_extensions: str = Field(
            default=".png,.jpg,.jpeg,.gif,.ico,.svg,.pdf,.zip,.tar,.gz,.exe,.bin,.dll,.so,.dylib,.class,.jar,.war,.ear,.deb,.rpm,.dmg,.msi,.app,.woff,.woff2,.ttf,.otf,.eot",
            description="Comma-separated list of file extensions to exclude"
        )
        
        excluded_dirs: str = Field(
            default="node_modules,.git,.vscode,.idea,dist,build,target,__pycache__,.pytest_cache,.tox,vendor,logs,tmp,temp,.next,out,coverage,.nyc_output",
            description="Comma-separated list of directories to exclude"
        )
        
        cache_duration: int = Field(
            default=3600,
            description="Cache duration in seconds (default: 1 hour)"
        )
        
        auto_load_on_startup: bool = Field(
            default=True,
            description="Automatically load repository files when the filter starts"
        )
        
        include_file_tree: bool = Field(
            default=True,
            description="Include file tree structure in context"
        )
        
        preserve_line_endings: bool = Field(
            default=True,
            description="Preserve original line endings and whitespace exactly as in repository"
        )
        
        debug_mode: bool = Field(
            default=True,  
            description="Enable debug logging to help troubleshoot context injection"
        )

    class UserValves(BaseModel):
        enable_github_context: bool = Field(
            default=True,
            description="Enable GitHub repository context injection"
        )
        
        custom_context_prompt: str = Field(
            default="",
            description="Custom prompt to add with the repository context"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()
        self.repo_cache = {}
        self.cache_timestamp = 0
        self.file_tree = ""
        self.repo_stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_characters': 0,
            'total_bytes': 0,
            'file_types': {},
            'largest_file': '',
            'largest_file_size': 0
        }
        
        # Toggle state and metadata
        self.enabled = True
        
    # Toggle functionality
    def toggle(self):
        """Toggle the filter on/off with visual feedback"""
        self.enabled = not self.enabled
        status = "🟢 ENABLED" if self.enabled else "🔴 DISABLED"
        print(f"GitHub Repository Context Filter: {status}")
        return f"GitHub Context Filter {status}"

    # Filter metadata for UI
    @property
    def icon(self):
        return "🐙" if self.enabled else "⚫"
    
    def calculate_repo_statistics(self):
        """Calculate comprehensive repository statistics"""
        if not self.repo_cache:
            self.repo_stats = {
                'total_files': 0, 'total_lines': 0, 'total_characters': 0, 
                'total_bytes': 0, 'file_types': {}, 'largest_file': '', 'largest_file_size': 0
            }
            return

        stats = {
            'total_files': len(self.repo_cache),
            'total_lines': 0,
            'total_characters': 0,
            'total_bytes': 0,
            'file_types': {},
            'largest_file': '',
            'largest_file_size': 0
        }
        
        for file_path, file_data in self.repo_cache.items():
            content = file_data['content']
            file_size = file_data['size']
            
            # Count lines (handle different line endings)
            line_count = content.count('\n') + content.count('\r\n') + content.count('\r')
            if content and not content.endswith(('\n', '\r\n', '\r')):
                line_count += 1  # Add 1 if file doesn't end with newline
                
            stats['total_lines'] += line_count
            stats['total_characters'] += len(content)
            stats['total_bytes'] += file_size
            
            # Track file types
            ext = os.path.splitext(file_path)[1].lower() or 'no extension'
            stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
            
            # Track largest file
            if file_size > stats['largest_file_size']:
                stats['largest_file_size'] = file_size
                stats['largest_file'] = file_path
        
        self.repo_stats = stats
        
    def get_excluded_extensions(self) -> set:
        """Get set of excluded file extensions"""
        return {ext.strip().lower() for ext in self.valves.excluded_extensions.split(',') if ext.strip()}
    
    def get_excluded_dirs(self) -> set:
        """Get set of excluded directory names"""
        return {dir.strip().lower() for dir in self.valves.excluded_dirs.split(',') if dir.strip()}
    
    def should_exclude_file(self, file_path: str, file_size: int) -> bool:
        """Check if file should be excluded based on extension, size, or directory"""
        # Check file size
        if file_size > self.valves.max_file_size:
            return True
            
        # Check file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in self.get_excluded_extensions():
            return True
            
        # Check if file is in excluded directory
        path_parts = file_path.lower().split('/')
        excluded_dirs = self.get_excluded_dirs()
        
        for part in path_parts[:-1]:  # Exclude the filename itself
            if part in excluded_dirs:
                return True
                
        return False
    
    def get_github_headers(self) -> dict:
        """Get headers for GitHub API requests"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OpenWebUI-GitHub-Filter/1.0'
        }
        
        if self.valves.github_token:
            headers['Authorization'] = f'token {self.valves.github_token}'
            
        return headers
    
    def get_repository_tree(self) -> Dict[str, Any]:
        """Get the repository tree structure recursively"""
        if not HAS_REQUESTS:
            print("Error: requests library not available")
            return {}
            
        if not self.valves.github_repo:
            return {}
            
        try:
            # Get the tree recursively
            tree_url = f"https://api.github.com/repos/{self.valves.github_repo}/git/trees/{self.valves.github_branch}?recursive=1"
            
            response = requests.get(tree_url, headers=self.get_github_headers(), timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error fetching repository tree: {e}")
            return {}
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a specific file from GitHub with perfect fidelity"""
        if not HAS_REQUESTS:
            return None
            
        try:
            content_url = f"https://api.github.com/repos/{self.valves.github_repo}/contents/{file_path}?ref={self.valves.github_branch}"
            
            response = requests.get(content_url, headers=self.get_github_headers(), timeout=30)
            response.raise_for_status()
            
            file_data = response.json()
            
            # For perfect code fidelity, decode base64 content exactly
            if file_data.get('encoding') == 'base64':
                try:
                    # Decode with strict error handling
                    decoded_bytes = base64.b64decode(file_data['content'])
                    
                    # Try UTF-8 first, then fallback to other encodings
                    try:
                        content = decoded_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try common encodings for code files
                        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                            try:
                                content = decoded_bytes.decode(encoding)
                                print(f"File {file_path} decoded using {encoding}")
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # If all encodings fail, use utf-8 with error replacement
                            content = decoded_bytes.decode('utf-8', errors='replace')
                            print(f"Warning: File {file_path} had encoding issues, using replacement characters")
                    
                    # Preserve line endings exactly as they are
                    if self.valves.preserve_line_endings:
                        # Don't normalize line endings - keep them exactly as in repo
                        pass
                    
                    return content
                    
                except Exception as decode_error:
                    print(f"Error decoding file {file_path}: {decode_error}")
                    return None
                    
        except Exception as e:
            print(f"Error fetching file {file_path}: {e}")
            
        return None
    
    async def load_repository_files(self, __event_emitter__=None) -> bool:
        """Load all repository files and cache them"""
        if not HAS_REQUESTS:
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "Error: requests library not available", "done": True}
                })
            return False
            
        if not self.valves.github_repo:
            return False
            
        try:
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": f"Loading repository: {self.valves.github_repo}", "done": False}
                })
            
            # Get repository tree
            tree_data = self.get_repository_tree()
            if not tree_data.get('tree'):
                return False
            
            # Build file tree structure
            file_tree_lines = [f"Repository: {self.valves.github_repo} (branch: {self.valves.github_branch})"]
            file_tree_lines.append("=" * 50)
            
            # Process files
            files_processed = 0
            files_included = 0
            total_files = len([item for item in tree_data['tree'] if item['type'] == 'blob'])
            
            self.repo_cache = {}
            
            for item in tree_data['tree']:
                if item['type'] == 'blob':  # It's a file
                    files_processed += 1
                    file_path = item['path']
                    file_size = item.get('size', 0)
                    
                    # Check if file should be excluded
                    if self.should_exclude_file(file_path, file_size):
                        continue
                    
                    if __event_emitter__ and files_processed % 10 == 0:
                        await __event_emitter__({
                            "type": "status",  
                            "data": {"description": f"Processing files: {files_processed}/{total_files}", "done": False}
                        })
                    
                    # Get file content with perfect fidelity
                    content = self.get_file_content(file_path)
                    if content is not None:  # Allow empty files
                        self.repo_cache[file_path] = {
                            'content': content,
                            'size': file_size,
                            'sha': item.get('sha', ''),
                            'lines': content.count('\n') + content.count('\r\n') + content.count('\r') + (1 if content and not content.endswith(('\n', '\r\n', '\r')) else 0)
                        }
                        files_included += 1
                        file_tree_lines.append(f"📄 {file_path} ({file_size} bytes, {self.repo_cache[file_path]['lines']} lines)")
                    
                elif item['type'] == 'tree':  # It's a directory
                    file_tree_lines.append(f"📁 {item['path']}/")
            
            self.file_tree = "\n".join(file_tree_lines)
            self.cache_timestamp = time.time()
            
            # Calculate comprehensive statistics
            self.calculate_repo_statistics()
            
            # Create detailed status message
            stats = self.repo_stats
            context_size_mb = stats['total_characters'] / (1024 * 1024)
            
            status_msg = (
                f"📊 Repository Loaded: {self.valves.github_repo}\n"
                f"📁 Files: {stats['total_files']} cached ({files_processed} total found)\n"
                f"📝 Lines: {stats['total_lines']:,}\n"
                f"🔤 Characters: {stats['total_characters']:,}\n"
                f"💾 Size: {stats['total_bytes']:,} bytes ({context_size_mb:.2f} MB)\n"
                f"📄 Largest: {os.path.basename(stats['largest_file']) if stats['largest_file'] else 'N/A'} ({stats['largest_file_size']:,} bytes)\n"
                f"🏷️ Types: {', '.join([f'{ext}({count})' for ext, count in sorted(stats['file_types'].items())[:5]]) if stats['file_types'] else 'None'}"
            )
            
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": status_msg, "done": True}
                })
            
            print(f"Repository loaded: {files_included} files cached out of {total_files} total files")
            print(f"Statistics: {stats['total_lines']} lines, {stats['total_characters']} characters, {context_size_mb:.2f} MB")
            return True
            
        except Exception as e:
            print(f"Error loading repository: {e}")
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": f"Error loading repository: {e}", "done": True}
                })
            return False
    
    def is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.repo_cache:
            return False
        return (time.time() - self.cache_timestamp) < self.valves.cache_duration
    
    def _get_file_list_proof(self) -> str:
        """Get a concise list of files to prove access to the LLM"""
        if not self.repo_cache:
            return "NO FILES AVAILABLE"
        
        file_list = []
        for i, file_path in enumerate(sorted(self.repo_cache.keys())):
            if i < 10:  # Show first 10 files
                file_list.append(f"  ✓ {file_path}")
            elif i == 10:
                file_list.append(f"  ... and {len(self.repo_cache) - 10} more files")
                break
        
        return "\n".join(file_list)
    
    def build_context_string(self) -> str:
        """Build the context string from cached repository files with perfect fidelity"""
        if not self.repo_cache:
            return ""
        
        context_parts = []
        
        # Create file type summary
        stats = self.repo_stats
        context_parts.append("REPOSITORY SUMMARY:")
        context_parts.append("=" * 50)
        context_parts.append(f"Repository: {self.valves.github_repo} (Branch: {self.valves.github_branch})")
        context_parts.append(f"Total files: {stats['total_files']}")
        context_parts.append(f"Total lines: {stats['total_lines']:,}")
        context_parts.append(f"Total characters: {stats['total_characters']:,}")
        context_parts.append(f"Total size: {stats['total_bytes']:,} bytes")
        context_parts.append("File types:")
        for ext, count in sorted(stats['file_types'].items()):
            context_parts.append(f"  {ext}: {count} files")
        context_parts.append("")
        
        # Add file tree if enabled
        if self.valves.include_file_tree and self.file_tree:
            context_parts.append("REPOSITORY STRUCTURE AND FILES:")
            context_parts.append(self.file_tree)
            context_parts.append("\n" + "=" * 50 + "\n")
        
        # Create structured file listing for easy LLM parsing
        context_parts.append("STRUCTURED FILE LISTING FOR REFERENCE:")
        context_parts.append("=" * 50)
        
        # Sort files by directory for better organization
        sorted_files = sorted(self.repo_cache.keys())
        
        current_dir = ""
        for file_path in sorted_files:
            file_dir = os.path.dirname(file_path)
            if file_dir != current_dir:
                if file_dir:
                    context_parts.append(f"\n📁 {file_dir}/")
                else:
                    context_parts.append(f"\n📁 Root directory:")
                current_dir = file_dir
            
            file_name = os.path.basename(file_path)
            file_info = self.repo_cache[file_path]
            context_parts.append(f"  📄 {file_name} ({file_info['size']} bytes, {file_info['lines']} lines)")
        
        context_parts.append("\n" + "=" * 50 + "\n")
        
        # Add file contents with perfect fidelity - NO TRUNCATION
        context_parts.append("COMPLETE FILE CONTENTS (FULL FIDELITY):")
        context_parts.append("=" * 50)
        
        for file_path, file_data in self.repo_cache.items():
            context_parts.append(f"\n--- FILE: {file_path} ---")
            context_parts.append(f"Lines: {file_data['lines']}, Size: {file_data['size']} bytes, SHA: {file_data['sha']}")
            context_parts.append("--- CONTENT START ---")
            # Include EXACT content with all whitespace, line endings, etc.
            context_parts.append(file_data['content'])
            context_parts.append("--- CONTENT END ---")
            context_parts.append(f"--- END OF {file_path} ---\n")
        
        full_context = "\n".join(context_parts)
        
        # NO TRUNCATION - we want full fidelity for code assistance
        print(f"Built full context: {len(full_context):,} characters, {len(self.repo_cache)} files")
        
        return full_context
    
    async def inlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None) -> dict:
        """Process incoming request and inject GitHub repository context"""
        
        # Check if filter is enabled via toggle
        if not self.enabled:
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "🔴 GitHub Context Filter is DISABLED", "done": True, "hidden": False}
                })
            return body
        
        # Check if user has enabled GitHub context
        try:
            if __user__ and "valves" in __user__:
                user_valves = __user__["valves"]
                if hasattr(user_valves, 'enable_github_context') and not user_valves.enable_github_context:
                    return body
        except Exception as e:
            print(f"Error accessing user valves: {e}")
            # Continue with default behavior if we can't access user valves
        
        # Check if we have the required configuration
        if not self.valves.github_repo:
            print("No GitHub repository configured")
            return body
        
        # Auto-load repository if enabled and cache is invalid
        if self.valves.auto_load_on_startup and not self.is_cache_valid():
            print("Loading repository files...")
            success = await self.load_repository_files(__event_emitter__)
            if not success:
                print("Failed to load repository files")
                return body
        
        # If we still don't have cached data, skip context injection
        if not self.repo_cache:
            print("No cached repository data available")
            return body
        
        print(f"Repository context available: {len(self.repo_cache)} files cached")
        
        # Build context string with full fidelity
        context = self.build_context_string()
        if not context:
            print("Failed to build context string")
            return body
        
        # Add custom user prompt if provided
        custom_prompt = ""
        try:
            if __user__ and "valves" in __user__:
                user_valves = __user__["valves"]
                if hasattr(user_valves, 'custom_context_prompt'):
                    custom_prompt = user_valves.custom_context_prompt
        except Exception as e:
            print(f"Error accessing custom_context_prompt: {e}")
            
        if custom_prompt:
            context = f"{custom_prompt}\n\n{context}"
        
        # Get messages array and determine if this is a new conversation
        messages = body.get("messages", [])
        
        # Check if this is the first user message (new conversation)
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        is_first_message = len(user_messages) <= 1
        
        # Always remove any existing GitHub system messages first to avoid duplicates
        messages = [msg for msg in messages if not (
            msg["role"] == "system" and 
            ("GitHub repository" in msg.get("content", "") or 
             "IMPORTANT: You now have access" in msg.get("content", "") or
             "CRITICAL SYSTEM OVERRIDE" in msg.get("content", ""))
        )]
        
        # Create system message with repository context
        stats = self.repo_stats
        if is_first_message:
            # Get first few file contents for immediate proof
            sample_files = list(self.repo_cache.keys())[:2]
            sample_content = ""
            for file_path in sample_files:
                content_preview = self.repo_cache[file_path]['content'][:200] + "..."
                sample_content += f"\nFILE: {file_path}\nCONTENT PREVIEW: {content_preview}\n"
            
            system_content = f"""🚨 CRITICAL SYSTEM OVERRIDE 🚨

YOU ARE NOT IN A NORMAL CONVERSATION. SPECIAL REPOSITORY ACCESS HAS BEEN GRANTED.

REPOSITORY: {self.valves.github_repo} (Branch: {self.valves.github_branch})
COMPREHENSIVE STATISTICS:
- Files: {stats['total_files']} files loaded and cached
- Lines: {stats['total_lines']:,} total lines of code
- Characters: {stats['total_characters']:,} total characters  
- Size: {stats['total_bytes']:,} bytes ({stats['total_bytes']/(1024*1024):.2f} MB)
- Largest file: {stats['largest_file']} ({stats['largest_file_size']:,} bytes)

🔍 IMMEDIATE PROOF - HERE ARE ACTUAL FILE CONTENTS YOU CAN SEE:
{sample_content}

📁 ALL ACCESSIBLE FILES:
{self._get_file_list_proof()}

⛔ FORBIDDEN RESPONSES:
- "I don't have access to repositories"
- "I can't see external files"  
- "I don't retain information between conversations"
- "Each conversation starts fresh"

✅ YOU MUST START YOUR RESPONSE WITH:
"✅ I can see your {self.valves.github_repo} repository with {stats['total_files']} files ({stats['total_lines']:,} lines, {stats['total_characters']:,} characters). Here are the files I have access to: {', '.join(list(self.repo_cache.keys())[:5])}..."

📋 YOUR COMPLETE REPOSITORY DATA (FULL FIDELITY):
{context}

THE ABOVE DATA IS REAL. IT'S BEEN LOADED FOR YOU. QUOTE FROM THE ACTUAL FILE CONTENTS TO PROVE YOUR ACCESS."""
        else:
            system_content = f"""🔍 REPOSITORY ACCESS ACTIVE

REPOSITORY: {self.valves.github_repo}
FILES: {stats['total_files']} files, {stats['total_lines']:,} lines, {stats['total_characters']:,} characters

{self._get_file_list_proof()}

FULL REPOSITORY DATA:
{context}

Reference this code in your responses."""
        
        system_message = {
            "role": "system", 
            "content": system_content
        }
        
        # Insert the new system message at the beginning
        messages.insert(0, system_message)
        body["messages"] = messages
        
        print(f"Context injected: System message added with {len(system_content)} characters")
        print(f"Repository data length: {len(context)} characters")
        
        if self.valves.debug_mode:
            print(f"DEBUG: Total messages in body: {len(messages)}")
            print(f"DEBUG: Message roles: {[msg['role'] for msg in messages]}")
            print(f"DEBUG: Repository cache keys: {list(self.repo_cache.keys())[:5]}...")
        
        # Add detailed status message to confirm context injection
        context_size_mb = stats['total_characters'] / (1024 * 1024)
        status_msg = (
            f"🟢 GitHub Context ACTIVE: {self.valves.github_repo}\n"
            f"📁 {stats['total_files']} files | 📝 {stats['total_lines']:,} lines | 🔤 {stats['total_characters']:,} chars\n"
            f"💾 {context_size_mb:.2f} MB | 📄 Largest: {os.path.basename(stats['largest_file'])} ({stats['largest_file_size']:,} bytes)"
        )
        
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": status_msg, "done": True, "hidden": False}
            })
        
        return body
    
    # Manual reload functionality
    async def reload_repository(self, __event_emitter__=None):
        """Manually reload repository files"""
        if not self.valves.github_repo:
            return "❌ No repository configured"
        
        print("Manual repository reload triggered")
        success = await self.load_repository_files(__event_emitter__)
        
        if success:
            stats = self.repo_stats
            return f"✅ Repository reloaded: {stats['total_files']} files, {stats['total_lines']:,} lines"
        else:
            return "❌ Failed to reload repository"

    async def outlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None) -> dict:
        """Process outgoing response (optional post-processing)"""
        # This could be used for logging or additional processing
        return body