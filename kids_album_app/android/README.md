# 📸 童年相册 - Android 原生项目

儿童云相册 App，专为小朋友设计 🎈

## 🎨 设计特点

- **活力彩色风格**：红、橙、黄、绿、蓝、粉七彩渐变
- **儿童友好**：大图标、圆润边角、可爱 Emoji
- **原生 Android**：使用 Kotlin + Material Design 3

## 📁 项目结构

```
kids_album_app/android/
├── app/
│   └── src/main/
│       ├── java/com/kidsalbum/
│       │   ├── ui/
│       │   │   ├── SplashActivity.kt     # 启动页
│       │   │   ├── LoginActivity.kt      # 登录页
│       │   │   ├── RegisterActivity.kt   # 注册页
│       │   │   └── HomeActivity.kt        # 云相册首页
│       │   ├── adapter/
│       │   │   └── PhotoAdapter.kt       # 照片列表适配器
│       │   └── model/
│       │       └── Photo.kt               # 照片数据模型
│       └── res/
│           ├── layout/                    # XML 布局文件
│           ├── values/                    # 颜色、字符串、主题
│           ├── drawable/                  # 背景、形状
│           └── xml/                       # 备份规则
├── build.gradle                           # 项目配置
└── settings.gradle                        # 项目设置
```

## 🛠️ 如何使用

### 1. 用 Android Studio 打开

```bash
# 打开 android 文件夹
cd kids_album_app/android
# 用 Android Studio 打开
```

### 2. 在 Android Studio 中

1. **File → Open** → 选择 `kids_album_app/android` 文件夹
2. 等待 Gradle 同步完成
3. **Build → Build APK** → 生成调试 APK

### 3. 运行到手机

- USB 连接手机 → 点击 Run 'app'
- 或生成 APK 后手动安装

## 🎯 界面预览

| 页面 | 说明 |
|------|------|
| 启动页 | Logo + 加载动画 + 飘动 Emoji |
| 登录页 | 手机号 + 密码 + 注册入口 |
| 注册页 | 昵称 + 手机 + 密码 + 生日选择 |
| 云相册 | 照片网格 + 分类筛选 + 底部导航 |

## 🎨 自定义修改

### 修改颜色
在 `res/values/colors.xml` 中修改：
```xml
<color name="primary_red">#FF6B6B</color>
<color name="primary_orange">#FFB347</color>
<!-- 等等... -->
```

### 修改布局
在 `res/layout/` 目录下的 XML 文件中修改

### 修改数据
在 `HomeActivity.kt` 的 `allPhotos` 列表中修改

---

*让每一次成长都被记住* 💝
