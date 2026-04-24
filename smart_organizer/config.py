"""配置文件：文件类型映射与全局常量."""

from typing import Dict, List

# 文件类型分类映射
FILE_CATEGORIES: Dict[str, List[str]] = {
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".raw"],
    "文档": [".pdf", ".doc", ".docx", ".txt", ".md", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".rtf"],
    "视频": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "程序": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"],
    "代码": [
        ".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".h", ".go",
        ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".r", ".m", ".sh", ".sql"
    ],
    "数据": [".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".conf", ".db", ".sqlite"],
}

# 反向映射：扩展名 -> 分类
EXT_TO_CATEGORY: Dict[str, str] = {}
for category, exts in FILE_CATEGORIES.items():
    for ext in exts:
        EXT_TO_CATEGORY[ext.lower()] = category

# 大小阈值（字节）
SIZE_SMALL = 1024 * 1024          # 1 MB
SIZE_MEDIUM = 50 * 1024 * 1024    # 50 MB
SIZE_LARGE = 500 * 1024 * 1024    # 500 MB

# 默认忽略的目录名
DEFAULT_IGNORE_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", ".pytest_cache",
    "node_modules", ".idea", ".vscode", "venv", ".venv", "env",
    "build", "dist", "target", ".egg-info", ".tox"
}

# 默认忽略的文件模式
DEFAULT_IGNORE_PATTERNS = {
    ".DS_Store", "Thumbs.db", "desktop.ini", ".directory"
}

# 日期格式
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"
