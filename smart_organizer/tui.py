"""交互式终端界面 (Text User Interface)."""

import os
import sys
from pathlib import Path

from .duplicate_finder import find_duplicates
from .organizer import Strategy, build_plan, execute_plan, list_undo_logs, undo
from .reporter import generate_report
from .scanner import scan_directory


def clear():
    """清屏."""
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\n按 Enter 键继续...")


def read_path(prompt: str, must_exist: bool = True) -> str:
    """读取并验证路径输入."""
    while True:
        p = input(prompt).strip()
        if not p:
            print("路径不能为空，请重新输入。")
            continue
        p = os.path.expanduser(p)
        if must_exist and not os.path.exists(p):
            print(f"路径不存在: {p}")
            continue
        return p


def read_choice(prompt: str, choices: dict) -> str:
    """读取选项."""
    print()
    for k, v in choices.items():
        print(f"  [{k}] {v}")
    while True:
        c = input(prompt).strip()
        if c in choices:
            return c
        print("无效选项，请重新选择。")


def banner():
    print("╔══════════════════════════════════════════╗")
    print("║       Smart Organizer 智能文件整理        ║")
    print("║         纯 Python 标准库实现             ║")
    print("╚══════════════════════════════════════════╝")
    print()


def menu() -> str:
    clear()
    banner()
    print("主菜单:")
    print("  [1] 分析目录结构")
    print("  [2] 查找重复文件")
    print("  [3] 整理文件")
    print("  [4] 生成 HTML 报告")
    print("  [5] 撤销上次整理")
    print("  [6] 查看帮助")
    print("  [0] 退出")
    print()
    return input("请选择操作: ").strip()


def show_help():
    clear()
    banner()
    print("功能说明:\n")
    print("1. 分析目录 — 扫描指定目录，统计文件类型、大小分布、大文件排行。")
    print("2. 查找重复 — 基于 MD5 哈希检测内容完全相同的文件，支持快速模式。")
    print("3. 整理文件 — 按类型/日期/大小自动分类移动文件，支持预览与撤销。")
    print("4. 生成报告 — 将扫描结果导出为美观的 HTML 页面，含图表与数据。")
    print("5. 撤销操作 — 根据日志恢复文件到原始位置。\n")
    print("整理策略:\n")
    print("  · 按类型 — 根据扩展名归入图片/文档/视频等文件夹")
    print("  · 按日期 — 按修改日期（年-月-日）分类")
    print("  · 按月   — 按修改月份（年-月）分类")
    print("  · 按大小 — 按文件体积区间分类\n")
    pause()


def action_analyze():
    clear()
    banner()
    print("【分析目录】\n")
    root = read_path("请输入要分析的目录: ")
    print("\n正在扫描，请稍候...")
    try:
        result = scan_directory(root)
        cats = result.category_counts()
        clear()
        banner()
        print(f"扫描完成: {result.total_files} 个文件，{result.total_size_label}")
        print(f"扫描目录数: {result.scanned_dirs}")
        if result.errors:
            print(f"警告: {len(result.errors)} 个文件无法访问")
        print("\n文件类型分布:")
        for cat, data in cats.items():
            pct = data['count'] / result.total_files * 100
            bar = "█" * int(pct / 5)
            print(f"  {cat:6s} {data['count']:4d} 个  {pct:5.1f}%  {bar}")
        print("\n大小分布:")
        for label, count in result.size_distribution().items():
            print(f"  {label}: {count} 个")
        print("\n大文件 Top 5:")
        for f in result.largest_files(5):
            print(f"  {f.size_label:>10s}  {f.name}")
    except Exception as e:
        print(f"错误: {e}")
    pause()


def action_duplicates():
    clear()
    banner()
    print("【查找重复文件】\n")
    root = read_path("请输入要扫描的目录: ")
    quick = read_choice("选择比对模式: ", {"1": "快速模式（大文件只读前 8KB）", "2": "精确模式（完整 MD5）"})
    quick_mode = quick == "1"
    print("\n正在查找重复文件，请稍候...")
    try:
        result = scan_directory(root)
        dups = find_duplicates(result, quick_mode=quick_mode)
        clear()
        banner()
        if not dups:
            print("未发现重复文件。")
        else:
            from .duplicate_finder import duplicate_summary
            summary = duplicate_summary(dups)
            print(f"发现 {summary['total_groups']} 组重复文件")
            print(f"重复文件总数: {summary['total_duplicate_files']}")
            print(f"可释放空间: {summary['wasted_space_label']}\n")
            for md5, files in list(dups.items())[:5]:
                print(f"  [{md5[:16]}...] {len(files)} 个文件，每个 {files[0].size_label}")
                for f in files:
                    print(f"      → {f.path}")
                print()
            if len(dups) > 5:
                print(f"  ... 还有 {len(dups) - 5} 组")
    except Exception as e:
        print(f"错误: {e}")
    pause()


def action_organize():
    clear()
    banner()
    print("【整理文件】\n")
    root = read_path("请输入要整理的目录: ")
    target = read_path("请输入整理后的目标目录（可新建）: ", must_exist=False)
    strategy_map = {
        "1": Strategy.BY_TYPE,
        "2": Strategy.BY_DATE,
        "3": Strategy.BY_MONTH,
        "4": Strategy.BY_SIZE,
    }
    s = read_choice("选择整理策略: ", {
        "1": "按文件类型",
        "2": "按修改日期",
        "3": "按修改月份",
        "4": "按文件大小",
    })
    strategy = strategy_map[s]

    print("\n正在分析...")
    try:
        result = scan_directory(root)
        plan = build_plan(result, strategy, target, dry_run=True)
        clear()
        banner()
        print(plan.preview())
        print()
        confirm = input("确认执行以上整理操作吗？[y/N]: ").strip().lower()
        if confirm == "y":
            log = execute_plan(plan)
            print(f"\n✅ 整理完成！日志已保存: {log}")
            print("如需撤销，请使用主菜单的『撤销上次整理』功能。")
        else:
            print("已取消操作。")
    except Exception as e:
        print(f"错误: {e}")
    pause()


def action_report():
    clear()
    banner()
    print("【生成 HTML 报告】\n")
    root = read_path("请输入要分析的目录: ")
    default_out = "./reports/analysis_report.html"
    out = input(f"报告输出路径 [默认: {default_out}]: ").strip() or default_out
    quick = input("是否同时检测重复文件？[y/N]: ").strip().lower() == "y"

    print("\n正在生成报告，请稍候...")
    try:
        result = scan_directory(root)
        dups = None
        if quick:
            dups = find_duplicates(result, quick_mode=True)
        path = generate_report(result, out, duplicates=dups)
        print(f"\n✅ 报告已生成: {path.absolute()}")
        print("请用浏览器打开查看。")
    except Exception as e:
        print(f"错误: {e}")
    pause()


def action_undo():
    clear()
    banner()
    print("【撤销整理操作】\n")
    logs = list_undo_logs()
    if not logs:
        print("没有找到可撤销的日志文件。")
        pause()
        return

    print("可撤销的操作记录:")
    for i, log in enumerate(logs[:10], 1):
        print(f"  [{i}] {log.name}")
    print("  [0] 返回")
    print()
    choice = input("请选择要撤销的记录编号: ").strip()
    if choice == "0":
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(logs):
            print("无效编号。")
            pause()
            return
        log_file = logs[idx]
        confirm = input(f"确认撤销 [{log_file.name}]？[y/N]: ").strip().lower()
        if confirm == "y":
            restored = undo(log_file)
            print(f"\n✅ 成功恢复 {restored} 个文件。")
        else:
            print("已取消。")
    except Exception as e:
        print(f"错误: {e}")
    pause()


def run_tui():
    """启动交互式菜单."""
    while True:
        choice = menu()
        if choice == "0":
            clear()
            print("再见！")
            sys.exit(0)
        elif choice == "1":
            action_analyze()
        elif choice == "2":
            action_duplicates()
        elif choice == "3":
            action_organize()
        elif choice == "4":
            action_report()
        elif choice == "5":
            action_undo()
        elif choice == "6":
            show_help()
        else:
            print("无效选项。")
            pause()
