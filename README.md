# Developer Portfolio

一个基于纯原生技术栈（HTML / CSS / JavaScript）构建的现代化开发者作品集网站，用于展示前端开发能力与工程化实践。

---

## 技术栈

- **HTML5** — 语义化标签、无障碍属性
- **CSS3** — CSS Variables、Grid、Flexbox、Backdrop Filter、动画关键帧
- **Vanilla JavaScript** — 模块化 IIFE、Intersection Observer、Hash Router、Custom Events

无任何第三方依赖，所有交互与视觉效果均为手写实现。

---

## 功能亮点

| 模块 | 说明 |
|------|------|
| **Hash Router** | 单页体验，无刷新页面切换，带退出/进入动画 |
| **主题切换** | 亮/暗双主题，自动适配系统偏好，localStorage 持久化 |
| **打字机效果** | 首页多句循环打字，模拟真实输入体验 |
| **滚动触发动画** | Intersection Observer 实现元素渐入、滑入、缩放 |
| **技能进度条** | 进入视口后自动填充至目标百分比 |
| **数字计数器** | 带缓动函数的滚动数字动画 |
| **项目筛选** | 按分类筛选项目卡片，带动画重排 |
| **表单验证** | 实时校验与提交反馈，模拟异步请求状态 |
| **滚动进度条** | 顶部渐变进度条，实时反映阅读进度 |
| **响应式布局** | 完整适配桌面、平板与移动端，含汉堡菜单 |
| **性能优化** | `prefers-reduced-motion` 媒体查询支持，减少动画偏好用户负担 |

---

## 项目结构

```
git/
├── index.html          # 入口文件
├── css/
│   ├── main.css        # 样式系统、组件、响应式
│   └── animations.css  # 关键帧动画与 reveal 工具类
├── js/
│   ├── router.js       # Hash 路由与页面模板
│   ├── animations.js   # 动画工具（打字机、计数器、技能条）
│   └── app.js          # 主题、菜单、表单、筛选、全局交互
└── README.md
```

---

## 本地运行

```bash
# 方式一：直接打开
open index.html

# 方式二：使用任意静态服务器
cd git
python3 -m http.server 8080
# 或
npx serve .
```

---

## 上传 GitHub 前的自定义清单

将以下占位内容替换为你的真实信息：

1. **首页信息** (`js/router.js` → `pages.home`)
   - 职位标题、统计数字

2. **关于我** (`js/router.js` → `pages.about`)
   - 个人简介、技能标签、技能百分比

3. **项目展示** (`js/router.js` → `pages.projects`)
   - 项目名称、描述、技术标签、预览链接、源码链接

4. **工作经历** (`js/router.js` → `pages.experience`)
   - 时间、公司、职位、工作描述

5. **联系方式** (`js/router.js` → `pages.contact`)
   - 邮箱、GitHub、LinkedIn 等社交链接

6. **头像** (`js/router.js` → `pages.home`)
   - 将 `.hero-avatar` 中的文字替换为 `<img>` 或使用你的 Logo

---

## 演示截图建议

为了让你在 GitHub 上获得更好的展示效果，建议上传以下截图到仓库的 `screenshots/` 目录，并在 README 中引用：

- 桌面端首页亮/暗主题
- 移动端响应式效果
- 项目筛选交互过程

---

## License

MIT
