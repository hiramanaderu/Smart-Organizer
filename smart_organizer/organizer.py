"""文件整理器：按规则分类整理文件，支持预览与撤销."""

import json
import hashlib
import os
import uuid
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

    reserved = set()
    for f in scan_result.files:
        folder_name = _resolve_folder(f, strategy)
        dst_dir = target / folder_name
        dst = dst_dir / f.name

        if f.path.resolve() == dst.resolve():
            continue

        # 预览与执行使用同一计划，同时保留本批次的目标路径。
        counter = 1
        original_dst = dst
        while os.path.lexists(dst) or os.path.normcase(str(dst)) in reserved:
            stem = original_dst.stem
            suffix = original_dst.suffix
            dst = dst_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        reserved.add(os.path.normcase(str(dst)))
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


def _fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_log(path: Path, data: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def _move_without_overwrite(src: Path, dst: Path, fingerprint: str) -> None:
    """独占创建目标文件；复制成功且源文件未变化后才删除源文件。"""
    if src.is_symlink() or not src.is_file():
        raise OSError(f"源文件不是普通文件: {src}")
    if _fingerprint(src) != fingerprint:
        raise OSError(f"源文件内容已改变: {src}")
    created = False
    try:
        with src.open("rb") as reader, dst.open("xb") as writer:
            created = True
            shutil.copyfileobj(reader, writer)
            writer.flush()
            os.fsync(writer.fileno())
        shutil.copystat(src, dst)
        if _fingerprint(dst) != fingerprint or _fingerprint(src) != fingerprint:
            raise OSError("复制过程中内容发生变化，已保留源文件")
        src.unlink()
    except BaseException:
        if created and src.exists():
            dst.unlink(missing_ok=True)
        raise


def execute_plan(plan: OrganizePlan, log_dir: str = "./logs") -> Path:
    """逐项记录移动状态；部分失败时保留可恢复日志。"""
    log_path = Path(log_dir).expanduser().resolve()
    log_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = log_path / f"undo_{timestamp}_{uuid.uuid4().hex}.json"
    data = {"timestamp": timestamp, "strategy": plan.strategy.value,
            "status": "running", "actions": []}
    _write_log(log_file, data)
    try:
        for action in plan.actions:
            action.dst.parent.mkdir(parents=True, exist_ok=True)
            record = {"src": str(action.src), "dst": str(action.dst),
                      "original_name": action.original_name,
                      "sha256": _fingerprint(action.src), "status": "pending"}
            data["actions"].append(record)
            _write_log(log_file, data)
            _move_without_overwrite(action.src, action.dst, record["sha256"])
            record["status"] = "moved"
            _write_log(log_file, data)
        data["status"] = "complete"
        _write_log(log_file, data)
    except Exception as error:
        data["status"] = "failed"
        data["error"] = str(error)
        _write_log(log_file, data)
        raise RuntimeError(f"整理未完成，恢复日志: {log_file}: {error}") from error
    return log_file


def undo(log_file: Path) -> int:
    """恢复成功后逐项记账，冲突或内容改变时保留日志供重试。"""
    with log_file.open(encoding="utf-8") as stream:
        data = json.load(stream)
    restored = 0
    errors = []
    for action in reversed(data.get("actions", [])):
        if action.get("status") in ("restored", "skipped"):
            continue
        src, dst = Path(action["dst"]), Path(action["src"])
        try:
            if action.get("status") == "pending" and dst.exists():
                # 移动未完成，原文件还在；不删除目标处可能存在的文件。
                action["status"] = "skipped"
                _write_log(log_file, data)
                continue
            if action.get("status") == "restoring" and not src.exists() and dst.is_file():
                if _fingerprint(dst) == action.get("sha256"):
                    action["status"] = "restored"
                    _write_log(log_file, data)
                    continue
            if src.is_symlink():
                raise OSError(f"拒绝恢复符号链接: {src}")
            fingerprint = action.get("sha256") or _fingerprint(src)
            action["sha256"] = fingerprint
            action["status"] = "restoring"
            _write_log(log_file, data)
            dst.parent.mkdir(parents=True, exist_ok=True)
            _move_without_overwrite(src, dst, fingerprint)
            action["status"] = "restored"
            restored += 1
            _write_log(log_file, data)
        except (OSError, shutil.Error) as error:
            errors.append(str(error))
    if errors:
        data["status"] = "restore_failed"
        data["errors"] = errors
        _write_log(log_file, data)
        raise RuntimeError(f"已恢复 {restored} 个文件，其余需重试；日志: {log_file}; " + "; ".join(errors))
    data["status"] = "undone"
    _write_log(log_file, data)
    log_file.rename(log_file.with_suffix(".undone.json"))
    return restored


def list_undo_logs(log_dir: str = "./logs") -> List[Path]:
    log_path = Path(log_dir).expanduser().resolve()
    return sorted((f for f in log_path.glob("undo_*.json")
                   if not f.name.endswith(".undone.json")), reverse=True)


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

