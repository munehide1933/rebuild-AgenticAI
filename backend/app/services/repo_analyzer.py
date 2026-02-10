from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class RepoAnalyzer:
    """轻量级仓库分析器，用于生成上下文摘要。"""

    DEFAULT_IGNORE = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".next",
        "dist",
        "build",
        ".pytest_cache",
    }

    def __init__(self, max_files: int = 400, max_file_bytes: int = 12000) -> None:
        self.max_files = max_files
        self.max_file_bytes = max_file_bytes

    def analyze(self, repo_path: str, focus: str | None = None) -> dict[str, Any]:
        root = Path(repo_path).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"Repo path not found: {repo_path}")

        file_entries = []
        language_stats: dict[str, int] = {}
        important_files: dict[str, str] = {}

        for idx, path in enumerate(self._iter_files(root)):
            if idx >= self.max_files:
                break

            rel_path = str(path.relative_to(root))
            file_entries.append(rel_path)
            ext = path.suffix.lower() or "no_ext"
            language_stats[ext] = language_stats.get(ext, 0) + 1

            if self._is_important_file(path, rel_path):
                important_files[rel_path] = self._read_file_snippet(path)

        summary = {
            "root": str(root),
            "focus": focus or "",
            "file_count": len(file_entries),
            "file_tree": file_entries[:200],
            "languages": dict(sorted(language_stats.items(), key=lambda item: item[1], reverse=True)),
            "important_files": important_files,
        }
        return summary

    def _iter_files(self, root: Path):
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in self.DEFAULT_IGNORE]
            for filename in filenames:
                if filename.startswith(".") and filename not in {".env", ".env.example"}:
                    continue
                yield Path(dirpath) / filename

    @staticmethod
    def _is_important_file(path: Path, rel_path: str) -> bool:
        lower = rel_path.lower()
        return lower in {
            "readme.md",
            "pyproject.toml",
            "package.json",
            "backend/requirements.txt",
            "frontend/package.json",
        } or lower.endswith((".py", ".ts", ".tsx", ".js", ".md")) and "app/" in lower

    def _read_file_snippet(self, path: Path) -> str:
        try:
            data = path.read_bytes()[: self.max_file_bytes]
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""
