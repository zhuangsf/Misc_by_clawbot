import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  // 主色调 - 活力彩色
  static const Color primaryRed = Color(0xFFFF6B6B);
  static const Color primaryOrange = Color(0xFFFFB347);
  static const Color primaryYellow = Color(0xFFFFE066);
  static const Color primaryGreen = Color(0xFF7ED957);
  static const Color primaryBlue = Color(0xFF5DADEC);
  static const Color primaryPurple = Color(0xFFC9A0DC);
  static const Color primaryPink = Color(0xFFFF9ED2);
  
  // 功能色
  static const Color white = Color(0xFFFFFFFF);
  static const Color textDark = Color(0xFF2D3436);
  static const Color textGray = Color(0xFF636E72);
  
  // 分类颜色
  static const Map<String, Color> categoryColors = {
    'all': primaryRed,
    'birthday': primaryPink,
    'travel': primaryBlue,
    'daily': primaryGreen,
    'holiday': primaryOrange,
  };
  
  // 渐变
  static const LinearGradient mainGradient = LinearGradient(
    colors: [primaryRed, primaryOrange, primaryYellow, primaryGreen, primaryBlue],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient headerGradient = LinearGradient(
    colors: [primaryPink, primaryOrange],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  
  static const LinearGradient homeHeaderGradient = LinearGradient(
    colors: [primaryBlue, primaryGreen],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
}

class AppTheme {
  static ThemeData get theme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primaryRed,
        brightness: Brightness.light,
      ),
      textTheme: GoogleFonts.notoSansScTextTheme(),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 18),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(25),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFFFFEF5),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(20),
          borderSide: const BorderSide(color: AppColors.primaryYellow, width: 3),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(20),
          borderSide: const BorderSide(color: AppColors.primaryYellow, width: 3),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(20),
          borderSide: const BorderSide(color: AppColors.primaryOrange, width: 3),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      ),
    );
  }
}
