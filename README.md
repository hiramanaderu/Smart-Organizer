# Smart Organizer

一个基于 **纯 Python 标准库** 开发的智能文件整理与分析工具，无需任何第三方依赖，开箱即用。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| **目录分析** | 递归扫描目录，统计文件类型分布、大小区间、大文件排行 |
| **重复检测** | 基于 MD5 哈希查找重复文件，支持「快速模式」（大文件只读前 8KB）与「精确模式」 |
| **智能整理** | 按文件类型 / 修改日期 / 修改月份 / 文件大小 自动分类移动，支持预览与撤销 |
| **HTML 报告** | 生成美观的分析报告（含 CSS 饼图、柱状图、数据表格），支持亮/暗主题自适应 |
| **撤销日志** | 所有整理操作自动记录 JSON 日志，可随时一键恢复 |

---

## 项目结构

```
Smart Organizer/
├── main.py                      # 程序入口（无参数启动 TUI，有参数走 CLI）
├── README.md
└── smart_organizer/             # 核心包
    ├── __init__.py              # 版本与作者信息
    ├── config.py                # 文件类型映射、阈值常量、忽略目录配置
    ├── scanner.py               # 目录扫描器（FileInfo / ScanResult）
    ├── duplicate_finder.py      # 重复文件查找（MD5 + 大小预过滤）
    ├── organizer.py             # 文件整理引擎（计划/执行/撤销）
    ├── reporter.py              # HTML 报告生成器（纯字符串模板）
    ├── tui.py                   # 交互式终端菜单
    └── cli.py                   # 命令行参数解析
```

---

## 快速开始

### 交互式菜单（推荐初次体验）

```bash
cd "Smart Organizer"
python main.py
```

启动后将看到终端菜单，支持分析目录、查找重复、整理文件、生成报告、撤销操作等功能。

### 命令行模式

```bash
# 分析目录
python main.py analyze ~/Downloads

# 查找重复文件（快速模式）
python main.py dup ~/Downloads --report

# 查找重复文件（完整 MD5 精确模式）
python main.py dup ~/Downloads --full

# 整理文件（按类型）
python main.py organize ~/Desktop ./Sorted --strategy type

# 整理文件（按修改日期），跳过预览直接执行
python main.py organize ~/Desktop ./Sorted --strategy date --yes

# 生成完整 HTML 报告（含重复检测）
python main.py report ~/Downloads -o ./reports/analysis.html --dup

# 列出可撤销的操作日志
python main.py logs

# 撤销最近一次整理
python main.py undo
```

### 支持的整理策略

| 策略 | 命令行参数 | 说明 |
|------|-----------|------|
| 按文件类型 | `type` | 根据扩展名归入图片/文档/视频/音频/代码等文件夹 |
| 按修改日期 | `date` | 按修改日期（年-月-日）分类 |
| 按修改月份 | `month` | 按修改月份（年-月）分类 |
| 按文件大小 | `size` | 按文件体积区间（<1MB / 1-50MB / 50-500MB / >500MB）分类 |

---

## 技术实现

### 扫描器 (`scanner.py`)
- 使用 `os.scandir()` 高效递归遍历，跳过常见忽略目录（`.git`, `node_modules`, `__pycache__` 等）
- `FileInfo` 数据类封装文件元数据，惰性计算 MD5
- `ScanResult` 聚合统计，支持分类计数、大小分布、Top N 大文件
- 支持按扩展名、文件大小范围过滤扫描结果

### 重复查找 (`duplicate_finder.py`)
- **两阶段优化**：先用文件大小分组（唯一大小直接排除），再对同大小文件计算 MD5
- **快速模式**：超过 8KB 的文件只读取头部数据计算部分 MD5，显著提速
- 精确模式下计算完整文件 MD5，确保零误报

### 整理引擎 (`organizer.py`)
- **策略模式**：`Strategy` 枚举定义四种整理规则
- **预览机制**：`build_plan()` 先生成整理计划，展示预计移动文件数与总大小，用户确认后才执行
- **安全机制**：自动处理文件名冲突（自动重命名）、支持 JSON 撤销日志
- **撤销恢复**：根据日志将文件恢复到原始位置，日志执行后自动标记为 `.undone.json`

### 报告生成 (`reporter.py`)
- 纯 Python 字符串拼接生成 HTML，零模板引擎依赖
- 使用 CSS `conic-gradient` 绘制数据饼图
- 支持 `prefers-color-scheme` 自动适配系统亮/暗主题
- 包含文件类型分布、大文件排行、重复文件检测等板块

---

## 自定义配置

修改 `smart_organizer/config.py` 即可调整：

- `FILE_CATEGORIES`：自定义文件类型分类与扩展名映射
- `DEFAULT_IGNORE_DIRS`：扫描时忽略的目录名集合
- `DEFAULT_IGNORE_PATTERNS`：扫描时忽略的文件名模式
- `SIZE_SMALL / SIZE_MEDIUM / SIZE_LARGE`：大小区间阈值
- `DATE_FORMAT / MONTH_FORMAT`：日期格式化字符串

---

## License

MIT
