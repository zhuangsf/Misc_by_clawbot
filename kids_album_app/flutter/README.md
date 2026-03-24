# 📸 童年相册 - Flutter 项目

儿童云相册 App，专为小朋友设计 🎈

## 🎨 设计特点

- **活力彩色风格**：红、橙、黄、绿、蓝、粉七彩渐变
- **儿童友好**：大图标、圆润边角、可爱 Emoji
- **功能完整**：登录、注册、云相册、分类浏览

## 📁 项目结构

```
kids_album_app/flutter/
├── lib/
│   ├── main.dart              # 入口文件
│   ├── theme/
│   │   └── app_theme.dart     # 主题配置（颜色、字体）
│   └── screens/
│       ├── splash_screen.dart # 启动页
│       ├── login_screen.dart  # 登录页
│       ├── register_screen.dart # 注册页
│       └── home_screen.dart   # 云相册首页
└── pubspec.yaml               # 项目配置
```

## 🚀 如何运行

### 1. 安装 Flutter 环境

参考官方文档：https://flutter.dev/docs/get-started/install

### 2. 获取依赖

```bash
cd kids_album_app/flutter
flutter pub get
```

### 3. 运行预览

```bash
flutter run
```

### 4. 构建 APK

```bash
# 调试版 APK
flutter build apk --debug

# 发布版 APK
flutter build apk --release
```

APK 文件生成在：`build/app/outputs/flutter-apk/`

## 📱 功能预览

| 页面 | 说明 |
|------|------|
| 启动页 | Logo + 加载动画 + 飘动 Emoji 装饰 |
| 登录页 | 手机号 + 密码 + 注册入口 |
| 注册页 | 昵称 + 手机 + 密码 + 生日选择 |
| 云相册 | 照片瀑布流 + 分类筛选 + 底部导航 |

## 🎯 分类标签

- 📸 全部
- 🎂 生日
- 🌍 出游
- 🏠 日常
- 🎉 节日

## 🛠️ 后续开发

- [ ] 相册详情页（查看大图）
- [ ] 照片上传功能
- [ ] 分类管理
- [ ] 个人中心
- [ ] 后端 API 对接

---

*让每一次成长都被记住* 💝
