"""文件整理器：按规则分类整理文件，支持预览与撤销."""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from .scanner import FileInfo, ScanResult, human_readable_size


class Strategy(Enum):
    """整理策略."""

    BY_TYPE = "type"
    BY_DATE = "date"
    BY_MONTH = "month"
    BY_SIZE = "size"


@dataclass
class MoveAction:
    """单次移动操作记录."""

    src: Path
    dst: Path
    original_name: str
    strategy: Strategy


@dataclass
class OrganizePlan:
    """整理计划."""

    actions: List[MoveAction] = field(default_factory=list)
    strategy: Strategy = Strategy.BY_TYPE
    target_dir: Path = Path(".")
    created_dirs: List[Path] = field(default_factory=list)

    @property
    def affected_files(self) -> int:
        return len(self.actions)

    @property
    def total_size(self) -> int:
        return sum(a.src.stat().st_size for a in self.actions if a.src.exists())

    def preview(self) -> str:
        """生成可读的预览文本."""
        lines = [
            f"整理策略: {self.strategy.value}",
            f"目标目录: {self.target_dir}",
            f"预计移动: {self.affected_files} 个文件",
            f"总大小: {human_readable_size(self.total_size)}",
            "-" * 50,
        ]
        for action in self.actions[:50]:
            lines.append(f"{action.src.name} -> {action.dst}")
        if len(self.actions) > 50:
            lines.append(f"... 还有 {len(self.actions) - 50} 个文件")
        return "\n".join(lines)


def build_plan(
    scan_result: ScanResult,
    strategy: Strategy,
    target_dir: str,
    dry_run: bool = True,
) -> OrganizePlan:
    """构建整理计划（不执行文件操作）."""
    target = Path(target_dir).expanduser().resolve()
    plan = OrganizePlan(strategy=strategy, target_dir=target)

    for f in scan_result.files:
        folder_name = _resolve_folder(f, strategy)
        dst_dir = target / folder_name
        dst = dst_dir / f.name

        # 处理重名
        counter = 1
        original_dst = dst
        while dst.exists() and not dry_run:
            stem = original_dst.stem
            suffix = original_dst.suffix
            dst = dst_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        plan.actions.append(
            MoveAction(
                src=f.path,
                dst=dst,
                original_name=f.name,
                strategy=strategy,
            )
        )
        if dst_dir not in plan.created_dirs:
            plan.created_dirs.append(dst_dir)

    return plan


def execute_plan(plan: OrganizePlan, log_dir: str = "./logs") -> Path:
    """执行整理计划并生成撤销日志.

    Returns:
        撤销日志文件路径
    """
    log_path = Path(log_dir).expanduser().resolve()
    log_path.mkdir(parents=True, exist_ok=True)

    # 创建目标目录
    for d in plan.created_dirs:
        d.mkdir(parents=True, exist_ok=True)

    # 执行移动
    executed: List[dict] = []
    for action in plan.actions:
        try:
            shutil.move(str(action.src), str(action.dst))
            executed.append({
                "src": str(action.src),
                "dst": str(action.dst),
                "original_name": action.original_name,
            })
        except (OSError, shutil.Error) as e:
            raise RuntimeError(f"移动失败 {action.src} -> {action.dst}: {e}")

    # 写入撤销日志
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"undo_{timestamp}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "strategy": plan.strategy.value,
                "actions": executed,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    return log_file


def undo(log_file: Path) -> int:
    """根据日志撤销整理操作.

    Returns:
        成功恢复的文件数量
    """
    if not log_file.exists():
        raise FileNotFoundError(f"日志文件不存在: {log_file}")

    with open(log_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    restored = 0
    for action in reversed(data.get("actions", [])):
        src = Path(action["dst"])
        dst = Path(action["src"])
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            restored += 1
        except (OSError, shutil.Error):
            pass

    # 重命名日志，标记已撤销
    undone_name = log_file.with_suffix(".undone.json")
    log_file.rename(undone_name)
    return restored


def list_undo_logs(log_dir: str = "./logs") -> List[Path]:
    """列出可用的撤销日志."""
    log_path = Path(log_dir).expanduser().resolve()
    if not log_path.exists():
        return []
    return sorted(
        [f for f in log_path.glob("undo_*.json") if f.suffix != ".undone"],
        reverse=True,
    )


def _resolve_folder(f: FileInfo, strategy: Strategy) -> str:
    """根据策略决定目标文件夹名."""
    if strategy == Strategy.BY_TYPE:
        return f.category
    elif strategy == Strategy.BY_DATE:
        return f.modified_date
    elif strategy == Strategy.BY_MONTH:
        return f.modified_month
    elif strategy == Strategy.BY_SIZE:
        from .config import SIZE_LARGE, SIZE_MEDIUM, SIZE_SMALL

        s = f.size
        if s < SIZE_SMALL:
            return "小文件_1MB以下"
        elif s < SIZE_MEDIUM:
            return "中文件_1-50MB"
        elif s < SIZE_LARGE:
            return "大文件_50-500MB"
        else:
            return "超大文件_500MB以上"
    return "其他"
