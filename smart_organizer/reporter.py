"""HTML 报告生成器：纯标准库生成美观的分析报告."""

import html
from pathlib import Path
from typing import Dict, List, Optional

from .duplicate_finder import duplicate_summary
from .scanner import ScanResult, human_readable_size


def generate_report(
    scan_result: ScanResult,
    output_path: str,
    duplicates: Optional[Dict[str, List]] = None,
) -> Path:
    """生成 HTML 分析报告."""
    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    categories = scan_result.category_counts()
    size_dist = scan_result.size_distribution()
    top_files = scan_result.largest_files(10)

    # 计算 CSS 饼图角度
    pie_slices = _build_pie_css(categories)

    # 重复文件摘要
    dup_summary = None
    dup_groups = []
    if duplicates:
        dup_summary = duplicate_summary(duplicates)
        dup_groups = list(duplicates.items())[:10]

    content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart Organizer 分析报告</title>
<style>
:root{{--bg:#f8f9fa;--card:#fff;--text:#212529;--muted:#6c757d;--primary:#339af0;--accent:#7950f2;--border:#dee2e6;--radius:12px;--shadow:0 4px 20px rgba(0,0,0,0.06);}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0d1117;--card:#161b22;--text:#c9d1d9;--muted:#8b949e;--primary:#58a6ff;--accent:#bc8cff;--border:#30363d;--shadow:0 4px 20px rgba(0,0,0,0.3);}}}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;padding:40px 20px}}
.container{{max-width:960px;margin:0 auto}}
header{{text-align:center;margin-bottom:48px}}
header h1{{font-size:2rem;margin-bottom:8px}}
header p{{color:var(--muted);font-size:0.95rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-bottom:32px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;box-shadow:var(--shadow);transition:transform .2s}}
.card:hover{{transform:translateY(-4px)}}
.card-value{{font-size:2rem;font-weight:700;color:var(--primary);line-height:1}}
.card-label{{font-size:0.85rem;color:var(--muted);margin-top:6px}}
.section{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:28px;margin-bottom:24px;box-shadow:var(--shadow)}}
.section h2{{font-size:1.25rem;margin-bottom:20px;display:flex;align-items:center;gap:10px}}
.pie-wrap{{width:200px;height:200px;border-radius:50%;position:relative;margin:0 auto 24px;background:conic-gradient({pie_slices});}}
.pie-legend{{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;font-size:0.85rem}}
.legend-item{{display:flex;align-items:center;gap:6px}}
.legend-color{{width:12px;height:12px;border-radius:3px}}
table{{width:100%;border-collapse:collapse;font-size:0.9rem;margin-top:12px}}
th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid var(--border)}}
th{{font-weight:600;color:var(--muted);font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em}}
tr:hover{{background:rgba(51,154,240,0.04)}}
.bar-bg{{background:var(--bg);border-radius:6px;height:8px;overflow:hidden}}
.bar-fill{{height:100%;background:linear-gradient(90deg,var(--primary),var(--accent));border-radius:6px;transition:width 1s ease}}
.dup-group{{background:var(--bg);border-radius:var(--radius);padding:16px;margin-bottom:16px}}
.dup-group h4{{font-size:0.9rem;color:var(--muted);margin-bottom:10px}}
.dup-group ul{{list-style:none;font-size:0.85rem}}
.dup-group li{{padding:4px 0;border-bottom:1px dashed var(--border)}}
.dup-group li:last-child{{border:none}}
footer{{text-align:center;color:var(--muted);font-size:0.8rem;margin-top:48px}}
@media(max-width:640px){{body{{padding:20px 12px}}.grid{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<div class="container">
<header>
<h1>📁 文件分析报告</h1>
<p>生成时间：{__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</header>

<div class="grid">
<div class="card"><div class="card-value">{scan_result.total_files}</div><div class="card-label">文件总数</div></div>
<div class="card"><div class="card-value">{scan_result.total_size_label}</div><div class="card-label">总大小</div></div>
<div class="card"><div class="card-value">{scan_result.scanned_dirs}</div><div class="card-label">扫描目录</div></div>
<div class="card"><div class="card-value">{len(categories)}</div><div class="card-label">文件分类</div></div>
</div>

<div class="section">
<h2>📊 文件类型分布</h2>
<div class="pie-wrap" title="文件类型分布"></div>
<div class="pie-legend">
{_build_legend(categories)}
</div>
<table>
<tr><th>分类</th><th>数量</th><th>占比</th><th>大小</th></tr>
{_build_category_rows(categories, scan_result.total_files)}
</table>
</div>

<div class="section">
<h2>📏 大文件排行 Top 10</h2>
<table>
<tr><th>文件名</th><th>类型</th><th>修改日期</th><th>大小</th></tr>
{_build_file_rows(top_files)}
</table>
</div>

{_build_duplicates_section(dup_summary, dup_groups)}

<footer>
Generated by Smart Organizer · Pure Python Standard Library
</footer>
</div>
<script>
document.querySelectorAll('.bar-fill').forEach(bar=>{{const w=bar.style.width;bar.style.width='0';setTimeout(()=>bar.style.width=w,100)}});
</script>
</body>
</html>"""

    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    return out


def _build_pie_css(categories: dict) -> str:
    """生成 conic-gradient CSS."""
    if not categories:
        return "#dee2e6 0deg"
    total = sum(v["count"] for v in categories.values())
    colors = ["#339af0", "#7950f2", "#40c057", "#fab005", "#fa5252", "#22b8cf", "#be4bdb", "#fd7e14", "#868e96", "#212529"]
    slices = []
    current_deg = 0
    for i, (cat, data) in enumerate(categories.items()):
        deg = (data["count"] / total) * 360
        color = colors[i % len(colors)]
        slices.append(f"{color} {current_deg:.1f}deg {(current_deg + deg):.1f}deg")
        current_deg += deg
    return ", ".join(slices)


def _build_legend(categories: dict) -> str:
    colors = ["#339af0", "#7950f2", "#40c057", "#fab005", "#fa5252", "#22b8cf", "#be4bdb", "#fd7e14", "#868e96", "#212529"]
    items = []
    for i, cat in enumerate(categories.keys()):
        c = colors[i % len(colors)]
        items.append(f'<div class="legend-item"><div class="legend-color" style="background:{c}"></div>{html.escape(cat)}</div>')
    return "\n".join(items)


def _build_category_rows(categories: dict, total: int) -> str:
    rows = []
    for cat, data in categories.items():
        pct = (data["count"] / total * 100) if total else 0
        rows.append(
            f"<tr><td>{html.escape(cat)}</td><td>{data['count']}</td>"
            f'<td><div class="bar-bg"><div class="bar-fill" style="width:{pct:.1f}%"></div></div></td>'
            f"<td>{human_readable_size(data['size'])}</td></tr>"
        )
    return "\n".join(rows)


def _build_file_rows(files) -> str:
    rows = []
    for f in files:
        rows.append(
            f"<tr><td>{html.escape(f.name)}</td><td>{html.escape(f.category)}</td>"
            f"<td>{f.modified_date}</td><td>{f.size_label}</td></tr>"
        )
    return "\n".join(rows)


def _build_duplicates_section(summary, groups) -> str:
    if not summary:
        return ""
    group_html = ""
    for md5, files in groups:
        group_html += f'<div class="dup-group"><h4>MD5: {md5[:16]}... ({len(files)} 个文件，每个 {files[0].size_label})</h4><ul>'
        for f in files:
            group_html += f'<li>{html.escape(str(f.path))}</li>'
        group_html += '</ul></div>'

    return f"""<div class="section">
<h2>🔍 重复文件检测</h2>
<div class="grid" style="margin-bottom:20px">
<div class="card"><div class="card-value">{summary['total_groups']}</div><div class="card-label">重复组</div></div>
<div class="card"><div class="card-value">{summary['total_duplicate_files']}</div><div class="card-label">重复文件数</div></div>
<div class="card"><div class="card-value">{summary['wasted_space_label']}</div><div class="card-label">可释放空间</div></div>
</div>
{group_html}
</div>"""
