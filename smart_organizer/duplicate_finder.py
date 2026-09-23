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
        quick_mode: 为 True 时先以头部哈希筛选，再完整校验内容
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

    # 部分哈希只用于缩小候选集，不作为内容相同的最终依据。
    candidates = defaultdict(list)
    for size, group in size_groups.items():
        if size_filter and len(group) < 2:
            continue
        for f in group:
            digest = _partial_md5(f.path) if quick_mode else "full"
            if digest:
                candidates[(size, digest)].append(f)

    duplicates = {}
    for group in candidates.values():
        if len(group) < 2:
            continue
        verified = defaultdict(list)
        for f in group:
            digest = f.compute_md5()
            if digest:
                verified[digest].append(f)
        # 相同完整哈希后仍逐字节比较，避免哈希碰撞。
        for digest, matches in verified.items():
            partitions = []
            for f in matches:
                for partition in partitions:
                    if _same_content(f.path, partition[0].path):
                        partition.append(f)
                        break
                else:
                    partitions.append([f])
            for index, partition in enumerate(partitions):
                if len(partition) > 1:
                    duplicates[f"{partition[0].size}:{digest}:{index}"] = partition
    return duplicates


def _same_content(left, right) -> bool:
    try:
        with left.open("rb") as a, right.open("rb") as b:
            while True:
                chunk = a.read(1024 * 1024)
                if chunk != b.read(1024 * 1024):
                    return False
                if not chunk:
                    return True
    except OSError:
        return False


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

