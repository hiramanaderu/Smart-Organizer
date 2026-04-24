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

## License

MIT
