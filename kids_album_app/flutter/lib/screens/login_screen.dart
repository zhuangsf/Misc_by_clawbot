import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'register_screen.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _login() {
    // 模拟登录，实际应调用API
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        child: Column(
          children: [
            // 头部渐变
            Container(
              width: double.infinity,
              padding: const EdgeInsets.only(top: 60, bottom: 30),
              decoration: const BoxDecoration(
                gradient: AppColors.headerGradient,
              ),
              child: Column(
                children: [
                  const Text('🌈', style: TextStyle(fontSize: 80)),
                  const SizedBox(height: 10),
                  ShaderMask(
                    shaderCallback: (bounds) => Colors.white.withOpacity(0.9).createShader(bounds),
                    child: const Text(
                      '欢迎回来！',
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '登录继续探索童年记忆',
                    style: TextStyle(fontSize: 14, color: Colors.white70),
                  ),
                ],
              ),
            ),
            
            // 表单
            Padding(
              padding: const EdgeInsets.all(30),
              child: Column(
                children: [
                  // 手机号
                  _buildInputField(
                    controller: _phoneController,
                    label: '📱 手机号',
                    hint: '请输入手机号',
                    keyboardType: TextInputType.phone,
                  ),
                  const SizedBox(height: 20),
                  
                  // 密码
                  _buildInputField(
                    controller: _passwordController,
                    label: '🔒 密码',
                    hint: '请输入密码',
                    obscureText: _obscurePassword,
                    suffix: IconButton(
                      icon: Icon(
                        _obscurePassword ? Icons.visibility_off : Icons.visibility,
                        color: AppColors.textGray,
                      ),
                      onPressed: () {
                        setState(() => _obscurePassword = !_obscurePassword);
                      },
                    ),
                  ),
                  const SizedBox(height: 30),
                  
                  // 登录按钮
                  _buildGradientButton(
                    text: '登 录',
                    onPressed: _login,
                    colors: [AppColors.primaryRed, AppColors.primaryPink],
                  ),
                  const SizedBox(height: 15),
                  
                  // 注册按钮
                  _buildGradientButton(
                    text: '注 册 新 账 号',
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const RegisterScreen()),
                      );
                    },
                    colors: [AppColors.primaryGreen, AppColors.primaryBlue],
                  ),
                  const SizedBox(height: 20),
                  
                  // 底部提示
                  RichText(
                    text: TextSpan(
                      style: const TextStyle(fontSize: 14, color: AppColors.textGray),
                      children: [
                        const TextSpan(text: '登录即表示同意 '),
                        TextSpan(
                          text: '用户协议',
                          style: TextStyle(color: AppColors.primaryRed, fontWeight: FontWeight.w600),
                        ),
                        const TextSpan(text: ' 和 '),
                        TextSpan(
                          text: '隐私政策',
                          style: TextStyle(color: AppColors.primaryRed, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputField({
    required TextEditingController controller,
    required String label,
    required String hint,
    bool obscureText = false,
    TextInputType? keyboardType,
    Widget? suffix,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: AppColors.textDark,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          obscureText: obscureText,
          keyboardType: keyboardType,
          decoration: InputDecoration(
            hintText: hint,
            suffixIcon: suffix,
          ),
        ),
      ],
    );
  }

  Widget _buildGradientButton({
    required String text,
    required VoidCallback onPressed,
    required List<Color> colors,
  }) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: colors),
        borderRadius: BorderRadius.circular(25),
        boxShadow: [
          BoxShadow(
            color: colors[0].withOpacity(0.4),
            blurRadius: 25,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          padding: const EdgeInsets.symmetric(vertical: 18),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(25),
          ),
        ),
        child: Text(
          text,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
            letterSpacing: 2,
          ),
        ),
      ),
    );
  }
}
