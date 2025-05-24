"""
title: Advanced GitHub Repository RAG Filter
author: pkeffect
author_url: https://github.com/pkeffect
funding_url: https://github.com/open-webui
version: 2.1
license: MIT
description: Precision GitHub repository filter with character-perfect reproduction and detailed metadata
requirements: requests, sentence-transformers, scikit-learn, numpy
"""

import os
import base64
import json
import time
import hashlib
import pickle
import tempfile
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from pydantic import BaseModel, Field
import asyncio
import re

# Try to import required libraries with fallbacks
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests library not available")

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("Warning: embedding libraries not available - semantic search disabled")


class Filter:
    class Valves(BaseModel):
        # GitHub Configuration
        github_token: str = Field(
            default="",
            description="GitHub Personal Access Token for API authentication",
        )

        github_repo: str = Field(
            default="",
            description="GitHub repository in format 'owner/repo' (e.g., 'microsoft/vscode')",
        )

        github_branch: str = Field(
            default="main", description="Branch to fetch files from"
        )

        # File Processing
        max_file_size: int = Field(
            default=2097152, description="Maximum file size in bytes to include"  # 2MB
        )

        chunk_size: int = Field(
            default=1500,
            description="Size of text chunks for better context management",
        )

        chunk_overlap: int = Field(
            default=200, description="Overlap between chunks to maintain context"
        )

        # File Filtering
        included_extensions: str = Field(
            default=".py,.js,.ts,.jsx,.tsx,.md,.txt,.json,.yaml,.yml,.toml,.cfg,.ini,.sh,.bash,.sql,.html,.css,.scss,.less,.vue,.svelte,.go,.rs,.java,.cpp,.c,.h,.php,.rb,.swift,.kt,.scala,.clj,.hs,.ml,.fs,.r,.m,.pl,.lua,.dart,.ex,.exs,.xml,.csv,.env,.gitignore,.dockerfile,.makefile,.cmake,.gradle,.pom,.config,.conf,.properties",
            description="Comma-separated list of file extensions to include",
        )

        excluded_extensions: str = Field(
            default=".png,.jpg,.jpeg,.gif,.ico,.svg,.pdf,.zip,.tar,.gz,.bz2,.xz,.7z,.rar,.exe,.bin,.dll,.so,.dylib,.class,.jar,.war,.ear,.deb,.rpm,.dmg,.msi,.app,.lock,.log,.cache,.tmp,.temp,.backup,.bak,.swp,.swo,.DS_Store,.thumbs.db,.pyc,.pyo,.pyd,.o,.obj,.lib,.a,.la,.lo,.gcda,.gcno",
            description="Comma-separated list of file extensions to exclude",
        )

        excluded_dirs: str = Field(
            default="node_modules,.git,.vscode,.idea,dist,build,target,__pycache__,.pytest_cache,.tox,vendor,logs,tmp,temp,.next,coverage,.nyc_output,public/assets,static/assets,.sass-cache,.gradle,bin,obj,.vs,.vscode-test,.dart_tool,packages,.pub-cache,.flutter-plugins,.flutter-plugins-dependencies,Pods,DerivedData,.build,.swiftpm",
            description="Comma-separated list of directories to exclude",
        )

        # RAG Configuration
        enable_semantic_search: bool = Field(
            default=True, description="Enable semantic search using embeddings"
        )

        top_k_results: int = Field(
            default=10,
            description="Number of most relevant chunks to include in context",
        )

        similarity_threshold: float = Field(
            default=0.05, description="Minimum similarity score for chunks (0.0-1.0)"
        )

        # Context Management
        max_context_length: int = Field(
            default=150000,
            description="Maximum context length in characters (set high for full reproduction)",
        )

        context_mode: str = Field(
            default="smart",
            description="Context injection mode: 'full' (all files), 'smart' (query-based), 'query-only' (only on questions)",
        )

        preserve_exact_formatting: bool = Field(
            default=True,
            description="Preserve exact whitespace, tabs, and formatting for character-perfect reproduction",
        )

        # Cache Management
        cache_duration: int = Field(
            default=7200, description="Cache duration in seconds"  # 2 hours
        )

        persistent_cache: bool = Field(
            default=True, description="Enable persistent cache storage"
        )

        # Performance
        auto_load_on_startup: bool = Field(
            default=False, description="Automatically load repository on filter startup"
        )

        rate_limit_delay: float = Field(
            default=0.05, description="Delay between GitHub API calls in seconds"
        )

        # UI/UX
        show_detailed_file_tree: bool = Field(
            default=True, description="Show detailed file tree with complete metadata"
        )

        show_loading_status: bool = Field(
            default=True, description="Show detailed loading progress in chat"
        )

        debug_mode: bool = Field(
            default=False, description="Enable detailed debug logging"
        )

        # Manual Cache Control
        enable_manual_purge: bool = Field(
            default=True,
            description="Enable manual cache purging via 'purge cache' or 'purge context' commands",
        )

    class UserValves(BaseModel):
        enable_github_context: bool = Field(
            default=True, description="Enable GitHub repository context injection"
        )

        auto_trigger_phrases: str = Field(
            default="analyze code,review repository,explain codebase,show me files,repo analysis,code review,examine code,inspect files,repository overview,codebase analysis",
            description="Comma-separated phrases that auto-trigger repository loading",
        )

        custom_system_prompt: str = Field(
            default="",
            description="Custom system prompt to add with repository context",
        )

        preferred_context_mode: str = Field(
            default="auto",
            description="User's preferred context mode: 'auto', 'always', 'never', 'on-request'",
        )

        show_file_metadata: bool = Field(
            default=True,
            description="Show detailed file metadata (size, lines, characters, etc.)",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()

        # Repository cache structure with detailed metadata
        self.repo_cache = {}
        self.embeddings_cache = {}
        self.file_tree_cache = ""
        self.detailed_tree_cache = ""
        self.cache_timestamp = 0
        self.repo_metadata = {}

        # Embedding model (lazy loaded)
        self.embeddings_model = None
        self.embedding_dimension = 384  # all-MiniLM-L6-v2 dimension

        # Cache file path
        self.cache_dir = os.path.join(tempfile.gettempdir(), "openwebui_github_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Load persistent cache if enabled
        if self.valves.persistent_cache:
            self._load_persistent_cache()

    def _get_cache_key(self) -> str:
        """Generate cache key for current repository configuration"""
        return hashlib.md5(
            f"{self.valves.github_repo}#{self.valves.github_branch}#{self.valves.chunk_size}".encode()
        ).hexdigest()

    def _load_persistent_cache(self):
        """Load cache from disk if available"""
        if not self.valves.persistent_cache:
            return

        try:
            cache_key = self._get_cache_key() if self.valves.github_repo else None
            if not cache_key:
                return

            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")

            if os.path.exists(cache_file):
                with open(cache_file, "rb") as f:
                    cached_data = pickle.load(f)

                # Check if cache is still valid
                if (
                    time.time() - cached_data.get("timestamp", 0)
                    < self.valves.cache_duration
                ):
                    self.repo_cache = cached_data.get("repo_cache", {})
                    self.embeddings_cache = cached_data.get("embeddings_cache", {})
                    self.file_tree_cache = cached_data.get("file_tree_cache", "")
                    self.detailed_tree_cache = cached_data.get(
                        "detailed_tree_cache", ""
                    )
                    self.repo_metadata = cached_data.get("repo_metadata", {})
                    self.cache_timestamp = cached_data.get("timestamp", 0)

                    if self.valves.debug_mode:
                        print(f"Loaded persistent cache: {len(self.repo_cache)} files")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"Error loading persistent cache: {e}")

    def _save_persistent_cache(self):
        """Save cache to disk"""
        if not self.valves.persistent_cache:
            return

        try:
            cache_key = self._get_cache_key()
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")

            cached_data = {
                "repo_cache": self.repo_cache,
                "embeddings_cache": self.embeddings_cache,
                "file_tree_cache": self.file_tree_cache,
                "detailed_tree_cache": self.detailed_tree_cache,
                "repo_metadata": self.repo_metadata,
                "timestamp": self.cache_timestamp,
            }

            with open(cache_file, "wb") as f:
                pickle.dump(cached_data, f)

            if self.valves.debug_mode:
                print(f"Saved persistent cache: {len(self.repo_cache)} files")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"Error saving persistent cache: {e}")

    def _get_embeddings_model(self):
        """Lazy load embeddings model"""
        if not HAS_EMBEDDINGS or not self.valves.enable_semantic_search:
            return None

        if self.embeddings_model is None:
            try:
                self.embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
                if self.valves.debug_mode:
                    print("Loaded embeddings model: all-MiniLM-L6-v2")
            except Exception as e:
                print(f"Error loading embeddings model: {e}")
                return None

        return self.embeddings_model

    def _get_file_extensions(self, extension_string: str) -> set:
        """Parse comma-separated extension string into set"""
        return {
            ext.strip().lower() for ext in extension_string.split(",") if ext.strip()
        }

    def _get_excluded_dirs(self) -> set:
        """Get set of excluded directory names"""
        return {
            dir.strip().lower()
            for dir in self.valves.excluded_dirs.split(",")
            if dir.strip()
        }

    def _should_include_file(self, file_path: str, file_size: int) -> bool:
        """Advanced file filtering logic"""
        # Check file size
        if file_size > self.valves.max_file_size:
            return False

        # Get file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        filename_lower = os.path.basename(file_path).lower()

        # Special handling for extensionless files
        extensionless_files = {
            "dockerfile",
            "makefile",
            "rakefile",
            "gemfile",
            "procfile",
            "vagrantfile",
            "jenkinsfile",
            "gulpfile",
            "gruntfile",
        }

        # Check if explicitly excluded
        excluded_exts = self._get_file_extensions(self.valves.excluded_extensions)
        if file_ext in excluded_exts:
            return False

        # Check if explicitly included
        included_exts = self._get_file_extensions(self.valves.included_extensions)
        if included_exts:
            # Include if extension matches OR if it's a special extensionless file
            if (
                file_ext not in included_exts
                and filename_lower not in extensionless_files
            ):
                return False

        # Check directory exclusions
        path_parts = [part.lower() for part in file_path.split("/")[:-1]]
        excluded_dirs = self._get_excluded_dirs()

        for part in path_parts:
            if part in excluded_dirs:
                return False

        # Additional smart filtering for common unwanted files
        skip_patterns = [
            "package-lock.json",
            "yarn.lock",
            "composer.lock",
            "gemfile.lock",
            "pipfile.lock",
            "poetry.lock",
            ".eslintcache",
            ".stylelintcache",
            "npm-debug.log",
            "yarn-debug.log",
            "yarn-error.log",
            ".env.local",
            ".env.development.local",
            ".env.test.local",
            ".env.production.local",
        ]

        for pattern in skip_patterns:
            if pattern in filename_lower:
                return False

        return True

    def _get_github_headers(self) -> dict:
        """Get headers for GitHub API requests"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OpenWebUI-GitHub-RAG-Filter/2.1",
        }

        if self.valves.github_token:
            headers["Authorization"] = f"token {self.valves.github_token}"

        return headers

    def _analyze_file_content(self, content: str, file_path: str) -> Dict:
        """Analyze file content for detailed metadata"""
        lines = content.split("\n")

        # Character analysis
        char_count = len(content)
        char_count_no_whitespace = len(re.sub(r"\s", "", content))
        line_count = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])

        # Line length analysis
        line_lengths = [len(line) for line in lines]
        max_line_length = max(line_lengths) if line_lengths else 0
        avg_line_length = sum(line_lengths) / len(line_lengths) if line_lengths else 0

        # Indentation analysis
        indented_lines = len([line for line in lines if line.startswith((" ", "\t"))])
        tab_lines = len([line for line in lines if "\t" in line])
        space_lines = len([line for line in lines if line.startswith(" ")])

        # Content type detection
        file_ext = os.path.splitext(file_path)[1].lower()

        # Language-specific analysis
        analysis = {
            "char_count": char_count,
            "char_count_no_whitespace": char_count_no_whitespace,
            "line_count": line_count,
            "non_empty_lines": non_empty_lines,
            "empty_lines": line_count - non_empty_lines,
            "max_line_length": max_line_length,
            "avg_line_length": round(avg_line_length, 1),
            "indented_lines": indented_lines,
            "tab_lines": tab_lines,
            "space_lines": space_lines,
            "whitespace_ratio": (
                round((char_count - char_count_no_whitespace) / char_count * 100, 1)
                if char_count > 0
                else 0
            ),
            "file_extension": file_ext,
            "estimated_encoding": "utf-8",  # GitHub API provides UTF-8
        }

        # Language-specific metrics
        if file_ext in [".py", ".pyx", ".pyi"]:
            analysis["language"] = "Python"
            analysis["import_lines"] = len(
                [
                    line
                    for line in lines
                    if line.strip().startswith(("import ", "from "))
                ]
            )
            analysis["comment_lines"] = len(
                [line for line in lines if line.strip().startswith("#")]
            )
            analysis["docstring_lines"] = len(
                [line for line in lines if '"""' in line or "'''" in line]
            )
        elif file_ext in [".js", ".jsx", ".ts", ".tsx"]:
            analysis["language"] = "JavaScript/TypeScript"
            analysis["import_lines"] = len(
                [line for line in lines if "import " in line or "require(" in line]
            )
            analysis["comment_lines"] = len(
                [line for line in lines if line.strip().startswith("//")]
            )
            analysis["function_lines"] = len(
                [line for line in lines if "function " in line or "=>" in line]
            )
        elif file_ext in [".java", ".scala", ".kt"]:
            analysis["language"] = "JVM Language"
            analysis["import_lines"] = len(
                [line for line in lines if line.strip().startswith("import ")]
            )
            analysis["comment_lines"] = len(
                [line for line in lines if line.strip().startswith("//")]
            )
            analysis["class_lines"] = len([line for line in lines if "class " in line])
        elif file_ext in [".go"]:
            analysis["language"] = "Go"
            analysis["import_lines"] = len(
                [line for line in lines if line.strip().startswith("import ")]
            )
            analysis["comment_lines"] = len(
                [line for line in lines if line.strip().startswith("//")]
            )
            analysis["func_lines"] = len(
                [line for line in lines if line.strip().startswith("func ")]
            )
        elif file_ext in [".rs"]:
            analysis["language"] = "Rust"
            analysis["use_lines"] = len(
                [line for line in lines if line.strip().startswith("use ")]
            )
            analysis["comment_lines"] = len(
                [line for line in lines if line.strip().startswith("//")]
            )
            analysis["fn_lines"] = len([line for line in lines if "fn " in line])
        elif file_ext in [".md"]:
            analysis["language"] = "Markdown"
            analysis["header_lines"] = len(
                [line for line in lines if line.strip().startswith("#")]
            )
            analysis["code_block_lines"] = len(
                [line for line in lines if line.strip().startswith("```")]
            )
            analysis["link_lines"] = len(
                [line for line in lines if "[" in line and "](" in line]
            )

        return analysis

    def _chunk_text(self, text: str, file_path: str) -> List[Dict]:
        """Advanced text chunking with overlap and precise metadata"""
        chunks = []
        lines = text.split("\n")

        current_chunk = []
        current_size = 0
        start_line = 1

        for i, line in enumerate(lines, 1):
            current_chunk.append(line)
            current_size += len(line) + 1  # +1 for newline

            # Create chunk when size limit reached
            if current_size >= self.valves.chunk_size or i == len(lines):
                if current_chunk:  # Only add non-empty chunks
                    chunk_text = "\n".join(current_chunk)

                    chunks.append(
                        {
                            "file_path": file_path,
                            "content": chunk_text,
                            "start_line": start_line,
                            "end_line": i,
                            "size": len(chunk_text),
                            "line_count": len(current_chunk),
                            "char_count": len(chunk_text),
                            "id": f"{file_path}:{start_line}-{i}",
                            "chunk_index": len(chunks),
                        }
                    )

                # Handle overlap for next chunk
                if i < len(lines) and self.valves.chunk_overlap > 0:
                    overlap_lines = []
                    overlap_size = 0

                    # Take last few lines for overlap
                    for j in range(len(current_chunk) - 1, -1, -1):
                        line = current_chunk[j]
                        if overlap_size + len(line) <= self.valves.chunk_overlap:
                            overlap_lines.insert(0, line)
                            overlap_size += len(line) + 1
                        else:
                            break

                    current_chunk = overlap_lines
                    current_size = overlap_size
                    start_line = i - len(overlap_lines) + 1
                else:
                    current_chunk = []
                    current_size = 0
                    start_line = i + 1

        return chunks

    async def _get_repository_tree(self, __event_emitter__=None) -> Dict[str, Any]:
        """Get repository tree with progress updates"""
        if not HAS_REQUESTS or not self.valves.github_repo:
            return {}

        try:
            if __event_emitter__ and self.valves.show_loading_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"📡 Fetching repository tree: {self.valves.github_repo}",
                            "done": False,
                        },
                    }
                )

            tree_url = f"https://api.github.com/repos/{self.valves.github_repo}/git/trees/{self.valves.github_branch}?recursive=1"

            response = requests.get(
                tree_url, headers=self._get_github_headers(), timeout=30
            )
            response.raise_for_status()

            tree_data = response.json()

            if __event_emitter__ and self.valves.show_loading_status:
                total_items = len(tree_data.get("tree", []))
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"📊 Found {total_items} items in repository tree",
                            "done": False,
                        },
                    }
                )

            return tree_data

        except Exception as e:
            error_msg = f"❌ Error fetching repository tree: {e}"
            print(error_msg)

            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )

            return {}

    async def _get_file_content(self, file_path: str) -> Optional[str]:
        """Get file content from GitHub API with rate limiting and precise handling"""
        if not HAS_REQUESTS:
            return None

        try:
            # Rate limiting
            if self.valves.rate_limit_delay > 0:
                await asyncio.sleep(self.valves.rate_limit_delay)

            content_url = f"https://api.github.com/repos/{self.valves.github_repo}/contents/{file_path}?ref={self.valves.github_branch}"

            response = requests.get(
                content_url, headers=self._get_github_headers(), timeout=30
            )
            response.raise_for_status()

            file_data = response.json()

            if file_data.get("encoding") == "base64":
                # Decode with precise handling to preserve all characters
                content_bytes = base64.b64decode(file_data["content"])

                # Try UTF-8 first, then fall back to other encodings
                try:
                    content = content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        content = content_bytes.decode("latin-1")
                    except UnicodeDecodeError:
                        content = content_bytes.decode("utf-8", errors="replace")

                # Preserve exact formatting if enabled
                if self.valves.preserve_exact_formatting:
                    # Don't strip or modify whitespace
                    return content
                else:
                    return content

        except Exception as e:
            if self.valves.debug_mode:
                print(f"❌ Error fetching file {file_path}: {e}")

        return None

    def _build_detailed_directory_tree(self, tree_data: Dict) -> str:
        """Build extremely detailed directory tree with full metadata"""
        if not tree_data.get("tree"):
            return ""

        # Organize by directory structure
        dirs = {}
        files = {}

        # Separate directories and files
        for item in tree_data["tree"]:
            if item["type"] == "tree":
                dirs[item["path"]] = item
            elif item["type"] == "blob":
                dir_path = os.path.dirname(item["path"])
                if dir_path not in files:
                    files[dir_path] = []
                files[dir_path].append(item)

        tree_lines = []
        tree_lines.append("📁 DETAILED REPOSITORY DIRECTORY STRUCTURE")
        tree_lines.append("═" * 80)
        tree_lines.append(f"Repository: {self.valves.github_repo}")
        tree_lines.append(f"Branch: {self.valves.github_branch}")
        tree_lines.append(f"Total Directories: {len(dirs)}")
        tree_lines.append(
            f"Total Files: {sum(len(file_list) for file_list in files.values())}"
        )
        tree_lines.append("")

        # Build hierarchical tree
        all_paths = sorted(set(list(dirs.keys()) + list(files.keys())))

        for path in all_paths:
            if path == "":  # Root directory
                tree_lines.append("📂 ROOT/")
                if "" in files:
                    for file_item in sorted(files[""], key=lambda x: x["path"]):
                        file_path = file_item["path"]
                        file_size = file_item.get("size", 0)
                        file_ext = os.path.splitext(file_path)[1] or "no-ext"

                        # Add file metadata from cache if available
                        metadata_str = f"({file_size:,} bytes, {file_ext})"
                        if file_path in self.repo_cache:
                            file_data = self.repo_cache[file_path]
                            analysis = file_data.get("analysis", {})
                            if analysis:
                                line_count = analysis.get("line_count", 0)
                                char_count = analysis.get("char_count", 0)
                                metadata_str = f"({file_size:,} bytes, {line_count:,} lines, {char_count:,} chars, {file_ext})"

                        tree_lines.append(f"  ├── 📄 {file_path} {metadata_str}")

                        # Show included/excluded status
                        if self._should_include_file(file_path, file_size):
                            tree_lines.append(f"      ✅ INCLUDED in context")
                        else:
                            tree_lines.append(f"      ❌ EXCLUDED from context")
            else:
                # Directory
                depth = len(path.split("/"))
                indent = "  " * depth
                tree_lines.append(f"{indent}📂 {os.path.basename(path)}/")

                # Add files in this directory
                if path in files:
                    for file_item in sorted(files[path], key=lambda x: x["path"]):
                        file_path = file_item["path"]
                        file_name = os.path.basename(file_path)
                        file_size = file_item.get("size", 0)
                        file_ext = os.path.splitext(file_path)[1] or "no-ext"

                        # Add detailed metadata from cache if available
                        metadata_str = f"({file_size:,} bytes, {file_ext})"
                        if file_path in self.repo_cache:
                            file_data = self.repo_cache[file_path]
                            analysis = file_data.get("analysis", {})
                            if analysis:
                                line_count = analysis.get("line_count", 0)
                                char_count = analysis.get("char_count", 0)
                                chunks = analysis.get("chunks", 0)
                                language = analysis.get("language", "Unknown")
                                metadata_str = f"({file_size:,} bytes, {line_count:,} lines, {char_count:,} chars, {chunks} chunks, {language}, {file_ext})"

                        tree_lines.append(
                            f"{indent}  ├── 📄 {file_name} {metadata_str}"
                        )

                        # Show SHA and inclusion status
                        sha = file_item.get("sha", "")[:8]
                        if sha:
                            tree_lines.append(f"{indent}      🔗 SHA: {sha}")

                        if self._should_include_file(file_path, file_size):
                            tree_lines.append(f"{indent}      ✅ INCLUDED in context")
                        else:
                            reason = (
                                "size"
                                if file_size > self.valves.max_file_size
                                else "filtered"
                            )
                            tree_lines.append(
                                f"{indent}      ❌ EXCLUDED from context ({reason})"
                            )

        return "\n".join(tree_lines)

    def _generate_file_summary_table(self) -> str:
        """Generate detailed file summary table"""
        if not self.repo_cache:
            return ""

        lines = []
        lines.append("📊 FILE ANALYSIS SUMMARY TABLE")
        lines.append("═" * 120)
        lines.append(
            "| FILE PATH | SIZE | LINES | CHARS | CHUNKS | LANGUAGE | EXTENSION | ENCODING |"
        )
        lines.append(
            "|-----------|------|-------|-------|--------|----------|-----------|----------|"
        )

        for file_path in sorted(self.repo_cache.keys()):
            file_data = self.repo_cache[file_path]
            analysis = file_data.get("analysis", {})

            size_str = f"{file_data['size']:,} bytes"
            lines_str = f"{analysis.get('line_count', 0):,}"
            chars_str = f"{analysis.get('char_count', 0):,}"
            chunks_str = f"{file_data.get('chunks', 0)}"
            lang_str = analysis.get("language", "Unknown")[:10]
            ext_str = analysis.get("file_extension", "none")
            enc_str = analysis.get("estimated_encoding", "utf-8")

            # Truncate file path if too long
            display_path = (
                file_path if len(file_path) <= 40 else f"...{file_path[-37:]}"
            )

            lines.append(
                f"| {display_path:<40} | {size_str:<8} | {lines_str:<5} | {chars_str:<8} | {chunks_str:<6} | {lang_str:<8} | {ext_str:<9} | {enc_str:<8} |"
            )

        lines.append("")
        lines.append(
            f"TOTALS: {len(self.repo_cache)} files, {sum(f['size'] for f in self.repo_cache.values()):,} bytes, {sum(f.get('analysis', {}).get('line_count', 0) for f in self.repo_cache.values()):,} lines"
        )

        return "\n".join(lines)

    async def _generate_embeddings(self, chunks: List[Dict], __event_emitter__=None):
        """Generate embeddings for chunks with precise progress"""
        if not self.valves.enable_semantic_search or not HAS_EMBEDDINGS:
            return

        model = self._get_embeddings_model()
        if not model:
            return

        try:
            if __event_emitter__ and self.valves.show_loading_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"🧠 Generating embeddings for {len(chunks):,} chunks",
                            "done": False,
                        },
                    }
                )

            # Prepare texts for embedding
            chunk_texts = []
            for chunk in chunks:
                # Create rich context for embedding
                context_text = f"File: {chunk['file_path']}\nLines: {chunk['start_line']}-{chunk['end_line']}\n\n{chunk['content']}"
                chunk_texts.append(context_text)

            # Generate embeddings in batches
            batch_size = 16  # Smaller batches for better progress reporting
            all_embeddings = []

            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i : i + batch_size]
                batch_embeddings = model.encode(batch, show_progress_bar=False)
                all_embeddings.extend(batch_embeddings)

                # Progress update
                if __event_emitter__ and self.valves.show_loading_status:
                    progress = min(100, int((i + len(batch)) / len(chunk_texts) * 100))
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"🧠 Generating embeddings: {progress}% ({i + len(batch):,}/{len(chunk_texts):,})",
                                "done": False,
                            },
                        }
                    )

            # Store embeddings with metadata
            for i, chunk in enumerate(chunks):
                self.embeddings_cache[chunk["id"]] = {
                    "embedding": all_embeddings[i].tolist(),
                    "file_path": chunk["file_path"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "size": chunk["size"],
                    "generated_at": datetime.now().isoformat(),
                }

            if self.valves.debug_mode:
                print(f"✅ Generated embeddings for {len(chunks):,} chunks")

        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")

    async def load_repository(self, __event_emitter__=None, force_reload=False) -> bool:
        """Load repository with comprehensive progress updates and detailed metadata"""
        if not self.valves.github_repo:
            return False

        # Check if we need to reload
        if not force_reload and self._is_cache_valid():
            if self.valves.debug_mode:
                print("✅ Using cached repository data")
            return True

        try:
            start_time = time.time()

            if __event_emitter__ and self.valves.show_loading_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"🚀 Loading repository: {self.valves.github_repo}",
                            "done": False,
                        },
                    }
                )

            # Get repository tree
            tree_data = await self._get_repository_tree(__event_emitter__)
            if not tree_data.get("tree"):
                return False

            # Build detailed tree first
            self.detailed_tree_cache = self._build_detailed_directory_tree(tree_data)

            # Process files with detailed progress
            total_files = len(
                [item for item in tree_data["tree"] if item["type"] == "blob"]
            )
            files_processed = 0
            files_included = 0
            files_excluded = 0
            total_bytes = 0
            total_lines = 0
            total_chars = 0
            all_chunks = []

            # Clear existing cache
            self.repo_cache = {}
            self.embeddings_cache = {}

            if __event_emitter__ and self.valves.show_loading_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"📋 Processing {total_files:,} files",
                            "done": False,
                        },
                    }
                )

            # Process files
            for item in tree_data["tree"]:
                if item["type"] == "blob":
                    files_processed += 1
                    file_path = item["path"]
                    file_size = item.get("size", 0)

                    # Progress update every 10 files
                    if (
                        __event_emitter__
                        and self.valves.show_loading_status
                        and files_processed % 10 == 0
                    ):
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": f"📄 Processing files: {files_processed:,}/{total_files:,} ({files_included:,} included, {files_excluded:,} excluded)",
                                    "done": False,
                                },
                            }
                        )

                    # Check if file should be included
                    if not self._should_include_file(file_path, file_size):
                        files_excluded += 1
                        continue

                    # Get file content
                    content = await self._get_file_content(file_path)
                    if not content:
                        files_excluded += 1
                        continue

                    # Analyze file content in detail
                    analysis = self._analyze_file_content(content, file_path)

                    # Create chunks
                    chunks = self._chunk_text(content, file_path)
                    all_chunks.extend(chunks)

                    # Store file data with comprehensive metadata
                    self.repo_cache[file_path] = {
                        "content": content,  # Exact character-perfect content
                        "size": file_size,
                        "chunks": len(chunks),
                        "sha": item.get("sha", ""),
                        "last_updated": datetime.now().isoformat(),
                        "analysis": analysis,
                        "github_url": f"https://github.com/{self.valves.github_repo}/blob/{self.valves.github_branch}/{file_path}",
                        "raw_url": f"https://raw.githubusercontent.com/{self.valves.github_repo}/{self.valves.github_branch}/{file_path}",
                    }

                    files_included += 1
                    total_bytes += file_size
                    total_lines += analysis.get("line_count", 0)
                    total_chars += analysis.get("char_count", 0)

            # Generate embeddings with progress
            if all_chunks and self.valves.enable_semantic_search:
                await self._generate_embeddings(all_chunks, __event_emitter__)

            # Build simple file tree for backward compatibility
            file_tree_lines = [
                f"Repository: {self.valves.github_repo} (branch: {self.valves.github_branch})"
            ]
            file_tree_lines.append("═" * 80)

            for file_path in sorted(self.repo_cache.keys()):
                file_data = self.repo_cache[file_path]
                analysis = file_data.get("analysis", {})
                line_count = analysis.get("line_count", 0)
                char_count = analysis.get("char_count", 0)
                chunks = file_data.get("chunks", 0)
                file_tree_lines.append(
                    f"📄 {file_path} ({file_data['size']:,} bytes, {line_count:,} lines, {char_count:,} chars, {chunks} chunks)"
                )

            self.file_tree_cache = "\n".join(file_tree_lines)

            # Store comprehensive metadata
            load_time = time.time() - start_time
            self.repo_metadata = {
                "repo_url": self.valves.github_repo,
                "branch": self.valves.github_branch,
                "total_files_processed": files_processed,
                "total_files_included": files_included,
                "total_files_excluded": files_excluded,
                "total_chunks": len(all_chunks),
                "total_bytes": total_bytes,
                "total_lines": total_lines,
                "total_characters": total_chars,
                "load_time_seconds": round(load_time, 2),
                "files_per_second": (
                    round(files_processed / load_time, 1) if load_time > 0 else 0
                ),
                "bytes_per_second": (
                    round(total_bytes / load_time, 0) if load_time > 0 else 0
                ),
                "last_updated": datetime.now().isoformat(),
                "embeddings_enabled": self.valves.enable_semantic_search
                and HAS_EMBEDDINGS,
                "total_embeddings": len(self.embeddings_cache),
                "cache_key": self._get_cache_key(),
            }

            self.cache_timestamp = time.time()

            # Save persistent cache
            self._save_persistent_cache()

            # Final comprehensive status update
            if __event_emitter__ and self.valves.show_loading_status:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"✅ Repository loaded: {files_included:,} files ({total_bytes:,} bytes, {total_lines:,} lines, {len(all_chunks):,} chunks) in {load_time:.1f}s",
                            "done": True,
                        },
                    }
                )

            print(
                f"✅ Repository loaded successfully: {files_included:,} files, {len(all_chunks):,} chunks, {total_bytes:,} bytes"
            )
            return True

        except Exception as e:
            error_msg = f"❌ Error loading repository: {e}"
            print(error_msg)

            if __event_emitter__:
                await __event_emitter__(
                    {"type": "status", "data": {"description": error_msg, "done": True}}
                )

            return False

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.repo_cache:
            return False
        return (time.time() - self.cache_timestamp) < self.valves.cache_duration

    def _semantic_search(self, query: str) -> List[Dict]:
        """Perform semantic search on repository chunks with detailed results"""
        if (
            not self.valves.enable_semantic_search
            or not HAS_EMBEDDINGS
            or not self.embeddings_cache
        ):
            return []

        model = self._get_embeddings_model()
        if not model:
            return []

        try:
            # Generate query embedding
            query_embedding = model.encode([query])

            # Get all chunk embeddings
            chunk_ids = list(self.embeddings_cache.keys())
            chunk_embeddings = np.array(
                [self.embeddings_cache[chunk_id]["embedding"] for chunk_id in chunk_ids]
            )

            # Calculate similarities
            similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]

            # Get top-k results above threshold
            results = []
            for i, similarity in enumerate(similarities):
                if similarity >= self.valves.similarity_threshold:
                    chunk_id = chunk_ids[i]
                    chunk_data = self.embeddings_cache[chunk_id]

                    results.append(
                        {
                            "chunk_id": chunk_id,
                            "file_path": chunk_data["file_path"],
                            "start_line": chunk_data["start_line"],
                            "end_line": chunk_data["end_line"],
                            "similarity": float(similarity),
                            "content": self._get_chunk_content(chunk_id),
                            "size": chunk_data["size"],
                            "line_count": chunk_data["end_line"]
                            - chunk_data["start_line"]
                            + 1,
                        }
                    )

            # Sort by similarity and return top-k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[: self.valves.top_k_results]

        except Exception as e:
            if self.valves.debug_mode:
                print(f"❌ Error in semantic search: {e}")
            return []

    def _get_chunk_content(self, chunk_id: str) -> str:
        """Get content for a specific chunk with precise line extraction"""
        try:
            file_path, line_range = chunk_id.split(":")
            start_line, end_line = map(int, line_range.split("-"))

            if file_path in self.repo_cache:
                content = self.repo_cache[file_path]["content"]
                lines = content.split("\n")
                chunk_lines = lines[start_line - 1 : end_line]
                return "\n".join(chunk_lines)
        except Exception as e:
            if self.valves.debug_mode:
                print(f"❌ Error getting chunk content for {chunk_id}: {e}")
        return ""

    def _build_context_from_search(self, query: str, user_valves) -> str:
        """Build context using semantic search results with comprehensive metadata"""
        if not self.repo_cache:
            return ""

        context_parts = []
        show_metadata = getattr(user_valves, "show_file_metadata", True)

        # Header with query
        context_parts.append("🔍 REPOSITORY CONTEXT (Query-Based Semantic Search)")
        context_parts.append("═" * 100)
        context_parts.append(f"Repository: {self.valves.github_repo}")
        context_parts.append(f"Branch: {self.valves.github_branch}")
        context_parts.append(f'Search Query: "{query}"')
        context_parts.append("")

        # Repository statistics
        if self.repo_metadata:
            context_parts.append("📊 REPOSITORY STATISTICS:")
            context_parts.append(
                f"• Total Files: {self.repo_metadata.get('total_files_included', 0):,}"
            )
            context_parts.append(
                f"• Total Size: {self.repo_metadata.get('total_bytes', 0):,} bytes"
            )
            context_parts.append(
                f"• Total Lines: {self.repo_metadata.get('total_lines', 0):,}"
            )
            context_parts.append(
                f"• Total Characters: {self.repo_metadata.get('total_characters', 0):,}"
            )
            context_parts.append(
                f"• Total Chunks: {self.repo_metadata.get('total_chunks', 0):,}"
            )
            context_parts.append(
                f"• Load Time: {self.repo_metadata.get('load_time_seconds', 0)} seconds"
            )
            context_parts.append("")

        # Semantic search results
        if self.valves.enable_semantic_search and HAS_EMBEDDINGS:
            search_results = self._semantic_search(query)

            if search_results:
                context_parts.append(
                    f"🎯 MOST RELEVANT CODE SECTIONS (Top {len(search_results)} of {len(self.embeddings_cache)} chunks):"
                )
                context_parts.append("─" * 80)

                for i, result in enumerate(search_results, 1):
                    file_path = result["file_path"]
                    similarity = result["similarity"]
                    start_line = result["start_line"]
                    end_line = result["end_line"]
                    line_count = result["line_count"]
                    size = result["size"]

                    # File metadata header
                    context_parts.append(f"\n[{i}] 📄 FILE: {file_path}")
                    context_parts.append(
                        f"    📊 Lines: {start_line:,}-{end_line:,} ({line_count:,} lines)"
                    )
                    context_parts.append(f"    📏 Size: {size:,} characters")
                    context_parts.append(f"    🎯 Relevance: {similarity:.4f}")

                    # Add file-level metadata if available
                    if show_metadata and file_path in self.repo_cache:
                        file_data = self.repo_cache[file_path]
                        analysis = file_data.get("analysis", {})
                        if analysis:
                            context_parts.append(
                                f"    🔤 Total File Lines: {analysis.get('line_count', 0):,}"
                            )
                            context_parts.append(
                                f"    📝 Language: {analysis.get('language', 'Unknown')}"
                            )
                            context_parts.append(
                                f"    📎 Extension: {analysis.get('file_extension', 'none')}"
                            )
                            context_parts.append(
                                f"    🔗 GitHub URL: {file_data.get('github_url', '')}"
                            )

                    context_parts.append(f"    {'─' * 60}")
                    context_parts.append("```")
                    context_parts.append(result["content"])
                    context_parts.append("```")
                    context_parts.append("")

                context_parts.append(
                    f"[Semantic search found {len(search_results)} relevant sections with similarity ≥ {self.valves.similarity_threshold}]"
                )
            else:
                context_parts.append(
                    f'❌ No highly relevant sections found for query: "{query}"'
                )
                context_parts.append(
                    f"   (Searched {len(self.embeddings_cache):,} chunks with threshold ≥ {self.valves.similarity_threshold})"
                )

                # Fallback to file listing
                context_parts.append("\n📁 AVAILABLE FILES FOR REFERENCE:")
                for i, file_path in enumerate(sorted(self.repo_cache.keys())[:15], 1):
                    file_data = self.repo_cache[file_path]
                    analysis = file_data.get("analysis", {})
                    size = file_data["size"]
                    lines = analysis.get("line_count", 0)
                    chars = analysis.get("char_count", 0)
                    context_parts.append(
                        f"  [{i:2d}] 📄 {file_path} ({size:,} bytes, {lines:,} lines, {chars:,} chars)"
                    )

                if len(self.repo_cache) > 15:
                    context_parts.append(
                        f"       ... and {len(self.repo_cache) - 15:,} more files"
                    )
        else:
            # Fallback without semantic search
            context_parts.append("📁 REPOSITORY FILES (Semantic search disabled):")
            context_parts.append("─" * 80)
            for i, file_path in enumerate(sorted(self.repo_cache.keys())[:20], 1):
                file_data = self.repo_cache[file_path]
                analysis = file_data.get("analysis", {})
                size = file_data["size"]
                lines = analysis.get("line_count", 0)
                chars = analysis.get("char_count", 0)
                lang = analysis.get("language", "Unknown")

                context_parts.append(f"[{i:2d}] 📄 {file_path}")
                if show_metadata:
                    context_parts.append(
                        f"     📊 {size:,} bytes, {lines:,} lines, {chars:,} characters"
                    )
                    context_parts.append(f"     📝 Language: {lang}")
                    context_parts.append(f"     🔗 {file_data.get('github_url', '')}")

            if len(self.repo_cache) > 20:
                context_parts.append(
                    f"\n... and {len(self.repo_cache) - 20:,} more files available"
                )

        # Add detailed directory structure if requested
        if self.valves.show_detailed_file_tree and self.detailed_tree_cache:
            context_parts.append(f"\n{self.detailed_tree_cache}")

        full_context = "\n".join(context_parts)

        # Truncate if too long, but preserve structure
        if len(full_context) > self.valves.max_context_length:
            full_context = (
                full_context[: self.valves.max_context_length]
                + "\n\n[CONTEXT TRUNCATED - USE FULL MODE FOR COMPLETE CONTENT]"
            )

        return full_context

    def _build_full_context(self, user_valves) -> str:
        """Build complete repository context with character-perfect reproduction"""
        if not self.repo_cache:
            return ""

        context_parts = []
        show_metadata = getattr(user_valves, "show_file_metadata", True)

        # Comprehensive header
        context_parts.append("🗂️ COMPLETE REPOSITORY CONTEXT (Full Mode)")
        context_parts.append("═" * 100)

        # Repository metadata
        if self.repo_metadata:
            context_parts.append("📊 REPOSITORY STATISTICS:")
            context_parts.append(f"Repository: {self.repo_metadata['repo_url']}")
            context_parts.append(f"Branch: {self.repo_metadata['branch']}")
            context_parts.append(
                f"Files Processed: {self.repo_metadata.get('total_files_processed', 0):,}"
            )
            context_parts.append(
                f"Files Included: {self.repo_metadata.get('total_files_included', 0):,}"
            )
            context_parts.append(
                f"Files Excluded: {self.repo_metadata.get('total_files_excluded', 0):,}"
            )
            context_parts.append(
                f"Total Size: {self.repo_metadata.get('total_bytes', 0):,} bytes"
            )
            context_parts.append(
                f"Total Lines: {self.repo_metadata.get('total_lines', 0):,}"
            )
            context_parts.append(
                f"Total Characters: {self.repo_metadata.get('total_characters', 0):,}"
            )
            context_parts.append(
                f"Total Chunks: {self.repo_metadata.get('total_chunks', 0):,}"
            )
            context_parts.append(
                f"Load Time: {self.repo_metadata.get('load_time_seconds', 0)} seconds"
            )
            context_parts.append(
                f"Processing Speed: {self.repo_metadata.get('files_per_second', 0)} files/sec"
            )
            context_parts.append(
                f"Last Updated: {self.repo_metadata.get('last_updated', 'Unknown')}"
            )
            context_parts.append("")

        # Detailed file summary table
        if show_metadata:
            context_parts.append(self._generate_file_summary_table())
            context_parts.append("")

        # Detailed directory structure
        if self.valves.show_detailed_file_tree and self.detailed_tree_cache:
            context_parts.append(self.detailed_tree_cache)
            context_parts.append("")

        # Complete file contents with precise metadata
        context_parts.append(
            "📋 COMPLETE FILE CONTENTS (Character-Perfect Reproduction):"
        )
        context_parts.append("═" * 100)

        for file_path in sorted(self.repo_cache.keys()):
            file_data = self.repo_cache[file_path]
            analysis = file_data.get("analysis", {})

            # File header with comprehensive metadata
            context_parts.append(f"\n{'█' * 80}")
            context_parts.append(f"📄 FILE: {file_path}")
            context_parts.append(f"{'█' * 80}")

            if show_metadata:
                context_parts.append(
                    f"🔗 GitHub URL: {file_data.get('github_url', '')}"
                )
                context_parts.append(f"🔗 Raw URL: {file_data.get('raw_url', '')}")
                context_parts.append(f"📊 File Size: {file_data['size']:,} bytes")
                context_parts.append(
                    f"📏 Character Count: {analysis.get('char_count', 0):,}"
                )
                context_parts.append(
                    f"📄 Line Count: {analysis.get('line_count', 0):,}"
                )
                context_parts.append(
                    f"📋 Non-Empty Lines: {analysis.get('non_empty_lines', 0):,}"
                )
                context_parts.append(
                    f"⬜ Empty Lines: {analysis.get('empty_lines', 0):,}"
                )
                context_parts.append(
                    f"📐 Max Line Length: {analysis.get('max_line_length', 0):,}"
                )
                context_parts.append(
                    f"📊 Avg Line Length: {analysis.get('avg_line_length', 0)}"
                )
                context_parts.append(f"🎯 Chunks: {file_data.get('chunks', 0)}")
                context_parts.append(
                    f"🏷️ Language: {analysis.get('language', 'Unknown')}"
                )
                context_parts.append(
                    f"📎 Extension: {analysis.get('file_extension', 'none')}"
                )
                context_parts.append(
                    f"🔤 Encoding: {analysis.get('estimated_encoding', 'utf-8')}"
                )
                context_parts.append(f"⭐ SHA: {file_data.get('sha', '')}")
                context_parts.append(
                    f"🕒 Last Updated: {file_data.get('last_updated', '')}"
                )

                # Language-specific metadata
                if "import_lines" in analysis:
                    context_parts.append(
                        f"📦 Import Lines: {analysis['import_lines']:,}"
                    )
                if "comment_lines" in analysis:
                    context_parts.append(
                        f"💬 Comment Lines: {analysis['comment_lines']:,}"
                    )
                if "function_lines" in analysis:
                    context_parts.append(
                        f"⚡ Function Lines: {analysis['function_lines']:,}"
                    )
                if "class_lines" in analysis:
                    context_parts.append(f"🏗️ Class Lines: {analysis['class_lines']:,}")

                context_parts.append(
                    f"🎨 Whitespace Ratio: {analysis.get('whitespace_ratio', 0)}%"
                )
                context_parts.append(
                    f"📍 Indented Lines: {analysis.get('indented_lines', 0):,}"
                )
                context_parts.append(f"🔤 Tab Lines: {analysis.get('tab_lines', 0):,}")
                context_parts.append(
                    f"🔸 Space Lines: {analysis.get('space_lines', 0):,}"
                )

            context_parts.append(f"{'─' * 80}")
            context_parts.append("CONTENT START:")
            context_parts.append(f"{'─' * 80}")

            # Character-perfect content reproduction
            context_parts.append(file_data["content"])

            context_parts.append(f"{'─' * 80}")
            context_parts.append(f"CONTENT END: {file_path}")
            context_parts.append(f"{'─' * 80}")

        full_context = "\n".join(context_parts)

        # Only truncate if absolutely necessary for full mode
        if len(full_context) > self.valves.max_context_length:
            truncate_point = self.valves.max_context_length - 500
            full_context = (
                full_context[:truncate_point]
                + f"\n\n{'═' * 80}\n[CONTEXT TRUNCATED AT {len(full_context):,} CHARACTERS]\n[INCREASE max_context_length FOR COMPLETE REPRODUCTION]\n[ORIGINAL FULL SIZE: {len(full_context):,} CHARACTERS]\n{'═' * 80}"
            )

        return full_context

    def _should_trigger_loading(self, messages: List[Dict], user_valves) -> bool:
        """Determine if repository should be loaded based on user input"""
        if not messages or not self.valves.github_repo:
            return False

        # Get last user message
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        if not user_messages:
            return False

        last_message = user_messages[-1]["content"].lower()

        # Check for manual purge commands first
        purge_commands = [
            "purge cache",
            "purge context",
            "clear cache",
            "clear context",
            "reload repo",
            "refresh repo",
        ]
        if any(cmd in last_message for cmd in purge_commands):
            return True

        # Check user's preferred mode
        preferred_mode = getattr(user_valves, "preferred_context_mode", "auto")

        if preferred_mode == "never":
            return False
        elif preferred_mode == "always":
            return True
        elif preferred_mode == "on-request":
            # Only load if explicitly requested
            trigger_words = [
                "load repo",
                "repository",
                "show files",
                "analyze code",
                "repo analysis",
            ]
            return any(word in last_message for word in trigger_words)
        else:  # auto mode
            # Check auto-trigger phrases
            trigger_phrases = getattr(user_valves, "auto_trigger_phrases", "").split(
                ","
            )
            trigger_phrases = [
                phrase.strip().lower() for phrase in trigger_phrases if phrase.strip()
            ]

            return any(phrase in last_message for phrase in trigger_phrases)

    def _determine_context_mode(self, messages: List[Dict]) -> str:
        """Determine which context mode to use based on message content"""
        if not messages:
            return self.valves.context_mode

        # Get last user message
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        if not user_messages:
            return self.valves.context_mode

        last_message = user_messages[-1]["content"].lower()

        # Check for explicit mode requests
        if any(
            phrase in last_message
            for phrase in [
                "full context",
                "complete repository",
                "all files",
                "entire codebase",
            ]
        ):
            return "full"

        # Check for question patterns that benefit from search
        question_indicators = [
            "how",
            "what",
            "where",
            "why",
            "when",
            "which",
            "find",
            "search",
            "locate",
            "?",
        ]
        is_question = any(
            indicator in last_message for indicator in question_indicators
        )

        # Override context mode based on message content
        if self.valves.context_mode == "smart":
            if is_question or "analyze" in last_message or "explain" in last_message:
                return "smart"  # Use semantic search
            else:
                return "query-only"

        return self.valves.context_mode

    def purge_cache(self, __event_emitter__=None):
        """Purge all cached data with detailed feedback"""
        files_count = len(self.repo_cache)
        embeddings_count = len(self.embeddings_cache)

        self.repo_cache = {}
        self.embeddings_cache = {}
        self.file_tree_cache = ""
        self.detailed_tree_cache = ""
        self.repo_metadata = {}
        self.cache_timestamp = 0

        # Remove persistent cache files
        if self.valves.persistent_cache:
            try:
                cache_key = self._get_cache_key()
                cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    if self.valves.debug_mode:
                        print(f"✅ Removed persistent cache file: {cache_file}")
            except Exception as e:
                if self.valves.debug_mode:
                    print(f"❌ Error removing cache file: {e}")

        print(
            f"🗑️ Repository cache purged: {files_count:,} files, {embeddings_count:,} embeddings"
        )
        return f"🗑️ Cache purged: {files_count:,} files and {embeddings_count:,} embeddings cleared"

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.repo_cache:
            return False
        return (time.time() - self.cache_timestamp) < self.valves.cache_duration

    async def inlet(
        self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None
    ) -> dict:
        """Process incoming request and inject GitHub repository context with precision controls"""

        # Get user valves
        user_valves = None
        if __user__ and "valves" in __user__:
            user_valves = __user__["valves"]

        # Check if user has disabled GitHub context
        if user_valves and hasattr(user_valves, "enable_github_context"):
            if not user_valves.enable_github_context:
                return body

        # Check repository configuration
        if not self.valves.github_repo:
            if self.valves.debug_mode:
                print("❌ No GitHub repository configured")
            return body

        messages = body.get("messages", [])

        # Check for manual purge commands
        if messages and self.valves.enable_manual_purge:
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            if user_messages:
                last_message = user_messages[-1]["content"].lower()
                purge_commands = [
                    "purge cache",
                    "purge context",
                    "clear cache",
                    "clear context",
                ]

                if any(cmd in last_message for cmd in purge_commands):
                    if __event_emitter__:
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": "🗑️ Purging repository cache...",
                                    "done": False,
                                },
                            }
                        )

                    purge_result = self.purge_cache(__event_emitter__)

                    if __event_emitter__:
                        await __event_emitter__(
                            {
                                "type": "status",
                                "data": {
                                    "description": f"✅ {purge_result}",
                                    "done": True,
                                },
                            }
                        )

                    # Force reload on next request
                    return body

        # Determine if we should load the repository
        should_load = (
            self.valves.auto_load_on_startup
            or self._should_trigger_loading(messages, user_valves)
            or not self._is_cache_valid()
        )

        # Load repository if needed
        if should_load:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "🔄 Repository loading initiated...",
                            "done": False,
                        },
                    }
                )

            success = await self.load_repository(__event_emitter__)
            if not success:
                if self.valves.debug_mode:
                    print("❌ Failed to load repository")
                return body

        # Skip if no cache available
        if not self.repo_cache:
            if self.valves.debug_mode:
                print("❌ No cached repository data available")
            return body

        # Determine context mode
        context_mode = self._determine_context_mode(messages)

        # Build appropriate context based on mode
        if context_mode == "full":
            context = self._build_full_context(user_valves)
        elif context_mode in ["smart", "query-only"]:
            # Use last user message for search
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            query = user_messages[-1]["content"] if user_messages else ""
            context = self._build_context_from_search(query, user_valves)
        else:
            return body  # No context injection

        if not context:
            return body

        # Add custom user prompt if provided
        custom_prompt = ""
        if user_valves and hasattr(user_valves, "custom_system_prompt"):
            custom_prompt = user_valves.custom_system_prompt

        if custom_prompt:
            context = f"{custom_prompt}\n\n{context}"

        # Remove any existing repository system messages to avoid duplicates
        messages = [
            msg
            for msg in messages
            if not (
                msg["role"] == "system"
                and (
                    "🔍 REPOSITORY CONTEXT" in msg.get("content", "")
                    or "🗂️ COMPLETE REPOSITORY CONTEXT" in msg.get("content", "")
                )
            )
        ]

        # Create comprehensive system message
        system_message = {"role": "system", "content": context}

        # Insert at beginning
        messages.insert(0, system_message)
        body["messages"] = messages

        # Debug logging
        if self.valves.debug_mode:
            print(
                f"✅ Context injected: {len(context):,} characters in {context_mode} mode"
            )
            print(
                f"📊 Repository: {self.valves.github_repo} ({len(self.repo_cache):,} files)"
            )
            print(
                f"🧠 Embeddings: {'enabled' if self.valves.enable_semantic_search else 'disabled'} ({len(self.embeddings_cache):,} cached)"
            )

        # Final status confirmation
        if __event_emitter__:
            files_count = len(self.repo_cache)
            total_size = sum(f["size"] for f in self.repo_cache.values())
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"✅ Repository context active: {files_count:,} files ({total_size:,} bytes) loaded in {context_mode} mode",
                        "done": True,
                        "hidden": False,
                    },
                }
            )

        return body

    async def outlet(
        self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None
    ) -> dict:
        """Process outgoing response with optional enhancements"""
        # Could add response processing, logging, or citations here
        return body
