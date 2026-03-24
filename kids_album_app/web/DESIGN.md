# 📱 极客未来风相册App - 设计规范

## 1. 设计风格定位

**主题**: 极客未来风 (Geek Future)
**关键词**: 科技感、金属质感、蓝色/紫色渐变、几何元素、发光效果

## 2. 色彩规范

```css
:root {
    /* 主色调 - 赛博蓝 */
    --primary: #00D9FF;
    --primary-dark: #0099CC;
    --primary-light: #66E5FF;
    
    /* 辅助色 - 紫罗兰 */
    --accent: #8B5CF6;
    --accent-light: #A78BFA;
    
    /* 背景色 - 深空黑 */
    --bg-dark: #0A0E17;
    --bg-card: #111827;
    --bg-elevated: #1F2937;
    
    /* 渐变 */
    --gradient-primary: linear-gradient(135deg, #00D9FF 0%, #8B5CF6 100%);
    --gradient-glow: linear-gradient(135deg, rgba(0,217,255,0.3) 0%, rgba(139,92,246,0.3) 100%);
    
    /* 文字色 */
    --text-primary: #F9FAFB;
    --text-secondary: #9CA3AF;
    --text-muted: #6B7280;
    
    /* 边框/分隔 */
    --border: rgba(0, 217, 255, 0.2);
    --glow: 0 0 20px rgba(0, 217, 255, 0.3);
}
```

## 3. 字体规范

- 主字体: 'Orbitron', sans-serif (科技感标题)
- 正文字体: 'Rajdhani', 'Noto Sans SC', sans-serif
- 数字/代码: 'JetBrains Mono', monospace

## 4. 页面结构

### 4.1 Splash启动页
- 全屏深色背景 + 动态粒子/网格动画
- 居中App Logo + 渐变文字名称
- 底部版本信息

### 4.2 登录页
- 上方Logo区域
- 输入框: 透明背景、底部发光边框
- 按钮: 渐变背景、悬停发光效果
- 底部注册链接

### 4.3 注册页
- 类似于登录页布局
- 增加头像上传区域
- 更多输入字段

### 4.4 首页 - 相册网格
- 顶部: 搜索栏 + 筛选按钮
- 主体: 照片网格 (2列/3列切换)
- 照片卡片: 圆角、悬停放大+发光
- 底部: 固定导航栏

### 4.5 照片详情页
- 全屏图片展示
- 底部信息栏: 日期、位置、标签
- 底部操作栏: 分享、删除、编辑

### 4.6 个人资料页
- 头像 + 昵称 + 简介
- 统计卡片: 相册数、照片数、收藏数
- 功能列表: 设置、隐私、关于

## 5. 组件规范

### 按钮
- 主按钮: 渐变背景 + 圆角 + 发光阴影
- 次按钮: 透明背景 + 边框 + 悬停发光

### 输入框
- 深色背景 + 底部发光边框
- focus状态: 边框变亮 + 发光扩散

### 卡片
- 圆角16px
- 背景: --bg-card
- 边框: 1px solid --border
- 悬停: 发光效果 + 轻微上浮

### 导航栏
- 固定底部
- 玻璃拟态效果 (backdrop-filter: blur)
- 图标 + 文字标签

## 6. 交互动效

- 页面切换: 淡入淡出 (0.3s ease)
- 按钮悬停: 发光增强 + 轻微缩放 (scale 1.02)
- 图片加载: 骨架屏动画
- 卡片悬停: translateY(-4px) + box-shadow增强

## 7. 图标库

使用 Phosphor Icons 或 Font Awesome:
- 相册: ph-image
- 搜索: ph-magnifying-glass
- 设置: ph-gear
- 分享: ph-share-network
- 删除: ph-trash
- 编辑: ph-pencil

## 8. 响应式设计

- Mobile: < 640px (单列布局)
- Tablet: 640px - 1024px (双列布局)
- Desktop: > 1024px (三列布局)

---

**创建文件列表**:
1. index.html - 入口页
2. splash.html - 启动页
3. login.html - 登录页
4. register.html - 注册页
5. home.html - 相册首页(网格)
6. photo.html - 照片详情页
7. profile.html - 个人资料页

---
*设计版本: v1.0 | 2026-03-21*
