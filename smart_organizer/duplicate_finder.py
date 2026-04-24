"""重复文件查找器：基于 MD5 哈希检测重复内容."""

from collections import defaultdict
from typing import Dict, List

from .scanner import FileInfo, ScanResult


def find_duplicates(
    scan_result: ScanResult,
    quick_mode: bool = True,
    size_filter: bool = True,
) -> Dict[str, List[FileInfo]]:
    """查找重复文件.

    采用两阶段策略优化性能：
    1. 先用文件大小分组（相同大小才可能是重复）
    2. 再对同大小文件计算 MD5 精确比对

    Args:
        scan_result: 扫描结果
        quick_mode: 为 True 时只取前 8KB 计算部分哈希，适合大文件快速筛查
        size_filter: 是否先用大小预过滤

    Returns:
        {md5: [FileInfo, ...]} 只返回有重复的文件组
    """
    files = scan_result.files
    if not files:
        return {}

    # 阶段 1：按大小分组
    size_groups: Dict[int, List[FileInfo]] = defaultdict(list)
    for f in files:
        size_groups[f.size].append(f)

    # 阶段 2：对大小相同的文件计算 MD5
    md5_groups: Dict[str, List[FileInfo]] = defaultdict(list)

    for size, group in size_groups.items():
        if size_filter and len(group) < 2:
            continue  # 唯一大小不可能是重复
        for f in group:
            if quick_mode and f.size > 8192:
                md5 = _partial_md5(f.path)
            else:
                md5 = f.compute_md5()
            if md5:
                md5_groups[md5].append(f)

    # 过滤出真正有重复的组
    duplicates = {md5: group for md5, group in md5_groups.items() if len(group) > 1}
    return duplicates


def _partial_md5(path, chunk_size: int = 8192) -> str:
    """计算文件前 chunk_size 字节的 MD5，用于快速比对."""
    import hashlib

    try:
        with open(path, "rb") as f:
            chunk = f.read(chunk_size)
        return hashlib.md5(chunk).hexdigest()
    except (OSError, PermissionError):
        return ""


def duplicate_summary(duplicates: Dict[str, List[FileInfo]]) -> dict:
    """生成重复文件统计摘要."""
    total_groups = len(duplicates)
    total_duplicate_files = sum(len(group) for group in duplicates.values())
    wasted_space = sum(
        (len(group) - 1) * group[0].size
        for group in duplicates.values()
    )
    from .scanner import human_readable_size

    return {
        "total_groups": total_groups,
        "total_duplicate_files": total_duplicate_files,
        "wasted_space": wasted_space,
        "wasted_space_label": human_readable_size(wasted_space),
    }
