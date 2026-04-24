"""命令行接口 (Command Line Interface)."""

import argparse
import sys
from pathlib import Path

from .duplicate_finder import duplicate_summary, find_duplicates
from .organizer import Strategy, build_plan, execute_plan, list_undo_logs, undo
from .reporter import generate_report
from .scanner import scan_directory


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smart-organizer",
        description="智能文件整理与分析工具 — 纯 Python 标准库实现",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s analyze ~/Downloads           分析下载目录
  %(prog)s dup ~/Downloads --report      查找重复并生成报告
  %(prog)s organize ~/Desktop ./Sorted --strategy type
  %(prog)s report ~/Downloads -o ./report.html
  %(prog)s undo                          撤销最近一次整理
        """,
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # analyze
    cmd_analyze = sub.add_parser("analyze", help="分析目录结构")
    cmd_analyze.add_argument("path", help="要分析的目录路径")
    cmd_analyze.add_argument("--top", type=int, default=10, help="显示大文件数量 (默认: 10)")

    # duplicate
    cmd_dup = sub.add_parser("dup", help="查找重复文件")
    cmd_dup.add_argument("path", help="要扫描的目录路径")
    cmd_dup.add_argument("--full", action="store_true", help="使用完整 MD5 而非快速模式")
    cmd_dup.add_argument("--report", action="store_true", help="同时生成 HTML 报告")
    cmd_dup.add_argument("-o", "--output", default="./reports/dup_report.html", help="报告输出路径")

    # organize
    cmd_org = sub.add_parser("organize", help="整理文件")
    cmd_org.add_argument("source", help="源目录")
    cmd_org.add_argument("target", help="目标目录")
    cmd_org.add_argument(
        "--strategy",
        choices=["type", "date", "month", "size"],
        default="type",
        help="整理策略 (默认: type)",
    )
    cmd_org.add_argument("--yes", action="store_true", help="跳过预览直接执行")

    # report
    cmd_rep = sub.add_parser("report", help="生成 HTML 分析报告")
    cmd_rep.add_argument("path", help="要分析的目录路径")
    cmd_rep.add_argument("-o", "--output", default="./reports/report.html", help="输出路径")
    cmd_rep.add_argument("--dup", action="store_true", help="包含重复文件检测")

    # undo
    sub.add_parser("undo", help="撤销最近一次整理操作")

    # logs
    sub.add_parser("logs", help="列出所有可撤销的操作日志")

    return parser


def handle_analyze(args):
    result = scan_directory(args.path)
    cats = result.category_counts()
    print(f"扫描完成: {result.total_files} 个文件，共 {result.total_size_label}")
    print(f"目录数: {result.scanned_dirs}")
    if result.errors:
        print(f"警告: {len(result.errors)} 个文件无法访问")
    print("\n文件类型分布:")
    for cat, data in cats.items():
        pct = data["count"] / result.total_files * 100 if result.total_files else 0
        from .scanner import human_readable_size
        print(f"  {cat:8s} {data['count']:4d} 个  {pct:5.1f}%  {human_readable_size(data['size'])}")
    print(f"\n大文件 Top {args.top}:")
    for i, f in enumerate(result.largest_files(args.top), 1):
        print(f"  {i:2d}. {f.size_label:>10s}  {f.name}")


def handle_dup(args):
    result = scan_directory(args.path)
    dups = find_duplicates(result, quick_mode=not args.full)
    summary = duplicate_summary(dups)
    print(f"重复组: {summary['total_groups']}")
    print(f"重复文件: {summary['total_duplicate_files']}")
    print(f"可释放空间: {summary['wasted_space_label']}")
    if dups:
        for md5, files in dups.items():
            print(f"\n[{md5}] {len(files)} 个文件:")
            for f in files:
                print(f"  - {f.path}")
    if args.report:
        path = generate_report(result, args.output, duplicates=dups)
        print(f"\n报告已保存: {path}")


def handle_organize(args):
    strategy_map = {
        "type": Strategy.BY_TYPE,
        "date": Strategy.BY_DATE,
        "month": Strategy.BY_MONTH,
        "size": Strategy.BY_SIZE,
    }
    result = scan_directory(args.source)
    plan = build_plan(result, strategy_map[args.strategy], args.target, dry_run=True)
    print(plan.preview())
    if not args.yes:
        confirm = input("\n确认执行? [y/N]: ").strip().lower()
        if confirm != "y":
            print("已取消。")
            return
    log = execute_plan(plan)
    print(f"整理完成。日志: {log}")


def handle_report(args):
    result = scan_directory(args.path)
    dups = None
    if args.dup:
        dups = find_duplicates(result, quick_mode=True)
    path = generate_report(result, args.output, duplicates=dups)
    print(f"报告已保存: {path}")


def handle_undo(_args):
    logs = list_undo_logs()
    if not logs:
        print("没有可撤销的日志。")
        return
    log = logs[0]
    print(f"正在撤销: {log.name}")
    restored = undo(log)
    print(f"成功恢复 {restored} 个文件。")


def handle_logs(_args):
    logs = list_undo_logs()
    if not logs:
        print("没有可撤销的日志。")
        return
    print("可撤销的操作日志:")
    for log in logs:
        print(f"  - {log}")


def run_cli(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handlers = {
        "analyze": handle_analyze,
        "dup": handle_dup,
        "organize": handle_organize,
        "report": handle_report,
        "undo": handle_undo,
        "logs": handle_logs,
    }

    try:
        handlers[args.command](args)
    except KeyboardInterrupt:
        print("\n操作已取消。")
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
