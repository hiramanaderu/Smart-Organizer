"""目录扫描器：递归遍历并收集文件元数据."""

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Set

from .config import DEFAULT_IGNORE_DIRS, DEFAULT_IGNORE_PATTERNS, EXT_TO_CATEGORY


@dataclass
class FileInfo:
    """单个文件的元数据."""

    path: Path
    size: int
    modified_time: float
    md5: Optional[str] = field(default=None, repr=False)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def ext(self) -> str:
        return self.path.suffix.lower()

    @property
    def category(self) -> str:
        return EXT_TO_CATEGORY.get(self.ext, "其他")

    @property
    def modified_date(self) -> str:
        return datetime.fromtimestamp(self.modified_time).strftime("%Y-%m-%d")

    @property
    def modified_month(self) -> str:
        return datetime.fromtimestamp(self.modified_time).strftime("%Y-%m")

    @property
    def size_label(self) -> str:
        return human_readable_size(self.size)

    def compute_md5(self, chunk_size: int = 8192) -> str:
        """计算文件 MD5，结果缓存."""
        if self.md5 is not None:
            return self.md5
        h = hashlib.md5()
        try:
            with open(self.path, "rb") as f:
                while chunk := f.read(chunk_size):
                    h.update(chunk)
            self.md5 = h.hexdigest()
        except (OSError, PermissionError):
            self.md5 = ""
        return self.md5


@dataclass
class ScanResult:
    """扫描结果聚合."""

    files: List[FileInfo] = field(default_factory=list)
    scanned_dirs: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_size(self) -> int:
        return sum(f.size for f in self.files)

    @property
    def total_size_label(self) -> str:
        return human_readable_size(self.total_size)

    def category_counts(self) -> dict:
        """按分类统计文件数量与大小."""
        stats: dict = {}
        for f in self.files:
            cat = f.category
            if cat not in stats:
                stats[cat] = {"count": 0, "size": 0}
            stats[cat]["count"] += 1
            stats[cat]["size"] += f.size
        # 按数量降序排列
        return dict(sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True))

    def largest_files(self, n: int = 20) -> List[FileInfo]:
        """返回最大的 n 个文件."""
        return sorted(self.files, key=lambda f: f.size, reverse=True)[:n]

    def size_distribution(self) -> dict:
        """按大小区间分布统计."""
        from .config import SIZE_LARGE, SIZE_MEDIUM, SIZE_SMALL

        dist = {"小文件 (<1MB)": 0, "中文件 (1-50MB)": 0, "大文件 (50-500MB)": 0, "超大文件 (>500MB)": 0}
        for f in self.files:
            s = f.size
            if s < SIZE_SMALL:
                dist["小文件 (<1MB)"] += 1
            elif s < SIZE_MEDIUM:
                dist["中文件 (1-50MB)"] += 1
            elif s < SIZE_LARGE:
                dist["大文件 (50-500MB)"] += 1
            else:
                dist["超大文件 (>500MB)"] += 1
        return dist


def human_readable_size(size_bytes: int) -> str:
    """将字节转换为人类可读格式."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


def scan_directory(
    root: str,
    ignore_dirs: Optional[Set[str]] = None,
    ignore_patterns: Optional[Set[str]] = None,
    min_size: int = 0,
    max_size: Optional[int] = None,
    extensions: Optional[Set[str]] = None,
) -> ScanResult:
    """递归扫描目录，返回 ScanResult.

    Args:
        root: 扫描根目录
        ignore_dirs: 忽略的目录名集合
        ignore_patterns: 忽略的文件名模式集合
        min_size: 最小文件大小（字节）
        max_size: 最大文件大小（字节）
        extensions: 只包含指定扩展名（如 {'.py', '.txt'}）
    """
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"目录不存在: {root}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"不是目录: {root}")

    ignore_dirs = (ignore_dirs or set()) | DEFAULT_IGNORE_DIRS
    ignore_patterns = (ignore_patterns or set()) | DEFAULT_IGNORE_PATTERNS

    result = ScanResult()
    result.scanned_dirs += 1

    def _should_ignore(name: str) -> bool:
        return name in ignore_patterns or any(name.endswith(p.lstrip("*")) for p in ignore_patterns)

    def _walk(current: Path) -> Iterator[FileInfo]:
        try:
            for entry in os.scandir(current):
                try:
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name not in ignore_dirs:
                            result.scanned_dirs += 1
                            yield from _walk(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        if _should_ignore(entry.name):
                            continue
                        size = entry.stat().st_size
                        if size < min_size:
                            continue
                        if max_size is not None and size > max_size:
                            continue
                        ext = Path(entry.name).suffix.lower()
                        if extensions and ext not in extensions:
                            continue
                        yield FileInfo(
                            path=Path(entry.path),
                            size=size,
                            modified_time=entry.stat().st_mtime,
                        )
                except (OSError, PermissionError) as e:
                    result.errors.append(str(e))
        except (OSError, PermissionError) as e:
            result.errors.append(str(e))

    result.files = list(_walk(root_path))
    return result
