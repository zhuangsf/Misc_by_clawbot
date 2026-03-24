import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class PhotoItem {
  final int id;
  final String category;
  final String title;
  final String emoji;
  final Color color;

  PhotoItem({
    required this.id,
    required this.category,
    required this.title,
    required this.emoji,
    required this.color,
  });
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _currentCategory = 'all';
  int _currentNavIndex = 0;

  final List<PhotoItem> _photos = [
    PhotoItem(id: 1, category: 'birthday', title: '3岁生日', emoji: '🎂', color: AppColors.primaryPink),
    PhotoItem(id: 2, category: 'travel', title: '去海边', emoji: '🏖️', color: AppColors.primaryBlue),
    PhotoItem(id: 3, category: 'daily', title: '幼儿园', emoji: '🏫', color: AppColors.primaryGreen),
    PhotoItem(id: 4, category: 'birthday', title: '蛋糕', emoji: '🎂', color: AppColors.primaryYellow),
    PhotoItem(id: 5, category: 'travel', title: '爬山', emoji: '⛰️', color: AppColors.primaryGreen),
    PhotoItem(id: 6, category: 'daily', title: '画画', emoji: '🎨', color: AppColors.primaryPurple),
    PhotoItem(id: 7, category: 'holiday', title: '春节', emoji: '🧧', color: AppColors.primaryRed),
    PhotoItem(id: 8, category: 'travel', title: '游乐场', emoji: '🎢', color: AppColors.primaryOrange),
    PhotoItem(id: 9, category: 'daily', title: '跳舞', emoji: '💃', color: AppColors.primaryPink),
  ];

  final List<Map<String, dynamic>> _categories = [
    {'key': 'all', 'label': '全部', 'emoji': '📸', 'color': AppColors.primaryRed},
    {'key': 'birthday', 'label': '生日', 'emoji': '🎂', 'color': AppColors.primaryPink},
    {'key': 'travel', 'label': '出游', 'emoji': '🌍', 'color': AppColors.primaryBlue},
    {'key': 'daily', 'label': '日常', 'emoji': '🏠', 'color': AppColors.primaryGreen},
    {'key': 'holiday', 'label': '节日', 'emoji': '🎉', 'color': AppColors.primaryOrange},
  ];

  List<PhotoItem> get _filteredPhotos {
    if (_currentCategory == 'all') return _photos;
    return _photos.where((p) => p.category == _currentCategory).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // 顶部 Header
          Container(
            padding: EdgeInsets.only(
              top: MediaQuery.of(context).padding.top + 20,
              left: 20,
              right: 20,
              bottom: 20,
            ),
            decoration: const BoxDecoration(
              gradient: AppColors.homeHeaderGradient,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 标题
                const Row(
                  children: [
                    Text('📸', style: TextStyle(fontSize: 28)),
                    SizedBox(width: 8),
                    Text(
                      '童年相册',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 15),
                
                // 用户信息
                Row(
                  children: [
                    Container(
                      width: 50,
                      height: 50,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(25),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.1),
                            blurRadius: 15,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: const Center(
                        child: Text('👧', style: TextStyle(fontSize: 28)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '小公主',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                        Text(
                          '记录成长的美好',
                          style: TextStyle(fontSize: 12, color: Colors.white70),
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 15),
                
                // 统计卡片
                Row(
                  children: [
                    _buildStatCard('128', '照片'),
                    const SizedBox(width: 15),
                    _buildStatCard('12', '相册'),
                    const SizedBox(width: 15),
                    _buildStatCard('2', '年份'),
                  ],
                ),
              ],
            ),
          ),
          
          // 分类标签
          Container(
            height: 60,
            padding: const EdgeInsets.symmetric(vertical: 10),
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 15),
              itemCount: _categories.length,
              itemBuilder: (context, index) {
                final cat = _categories[index];
                final isActive = _currentCategory == cat['key'];
                return GestureDetector(
                  onTap: () => setState(() => _currentCategory = cat['key']),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    margin: const EdgeInsets.symmetric(horizontal: 5),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                    decoration: BoxDecoration(
                      color: isActive ? AppColors.primaryRed : cat['color'],
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: isActive
                          ? [
                              BoxShadow(
                                color: AppColors.primaryRed.withOpacity(0.4),
                                blurRadius: 15,
                                offset: const Offset(0, 4),
                              ),
                            ]
                          : null,
                    ),
                    child: Row(
                      children: [
                        Text(cat['emoji'], style: const TextStyle(fontSize: 16)),
                        const SizedBox(width: 4),
                        Text(
                          cat['label'],
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: isActive ? Colors.white : AppColors.textDark,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          
          // 照片网格
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.all(15),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                mainAxisSpacing: 8,
                crossAxisSpacing: 8,
                childAspectRatio: 1,
              ),
              itemCount: _filteredPhotos.length,
              itemBuilder: (context, index) {
                final photo = _filteredPhotos[index];
                return _buildPhotoItem(photo);
              },
            ),
          ),
          
          // 底部导航
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.08),
                  blurRadius: 20,
                  offset: const Offset(0, -4),
                ),
              ],
            ),
            child: SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 10),
                child: Row(
                  children: [
                    _buildNavItem(0, '🏠', '首页'),
                    _buildNavItem(1, '📁', '相册'),
                    _buildNavItem(2, '➕', '上传'),
                    _buildNavItem(3, '👤', '我的'),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
      
      // 悬浮按钮
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('📷 拍照上传功能开发中...'),
              backgroundColor: AppColors.primaryOrange,
            ),
          );
        },
        backgroundColor: AppColors.primaryOrange,
        child: const Text('📷', style: TextStyle(fontSize: 28)),
      ),
    );
  }

  Widget _buildStatCard(String number, String label) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 15),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.25),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          children: [
            Text(
              number,
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            Text(
              label,
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPhotoItem(PhotoItem photo) {
    return GestureDetector(
      onTap: () {
        showDialog(
          context: context,
          builder: (context) => Dialog(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
            child: Padding(
              padding: const EdgeInsets.all(30),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(photo.emoji, style: const TextStyle(fontSize: 80)),
                  const SizedBox(height: 15),
                  Text(
                    photo.title,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('关闭'),
                  ),
                ],
              ),
            ),
          ),
        );
      },
      child: Hero(
        tag: 'photo_${photo.id}',
        child: Container(
          decoration: BoxDecoration(
            color: photo.color,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: photo.color.withOpacity(0.4),
                blurRadius: 8,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Stack(
            children: [
              Center(
                child: Text(photo.emoji, style: const TextStyle(fontSize: 40)),
              ),
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Colors.transparent, Colors.black.withOpacity(0.3)],
                    ),
                    borderRadius: const BorderRadius.vertical(bottom: Radius.circular(16)),
                  ),
                  child: Text(
                    photo.title,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, String emoji, String label) {
    final isActive = _currentNavIndex == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _currentNavIndex = index),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: isActive ? AppColors.primaryRed : Colors.transparent,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: isActive ? Colors.white : AppColors.textGray,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
