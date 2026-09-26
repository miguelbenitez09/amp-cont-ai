// Panama PortOps-AI v1.0 - Industrial Maritime Theme
// Author: Desarrollado v1.0 Miguel Benítez
// License: GNU GPL-3.0 with Section 7 Mandatory Attribution

import 'package:flutter/material.dart';

class MaritimeColors {
  static const Color background = Color(0xFF070D1E);       // Deep Oceanic Navy Abisal
  static const Color surface = Color(0xFF0F1B35);          // Rich Slate Blue
  static const Color surfaceCard = Color(0xFF162546);      // Card Container
  static const Color surfaceElevated = Color(0xFF1E325C);  // Hover & Elevated Slate
  static const Color border = Color(0xFF22355C);           // Muted Slate Border
  static const Color borderGlow = Color(0x4D00E5FF);       // Cyan Subtle Border Glow
  static const Color cyan = Color(0xFF00E5FF);             // Neon Cyan / Primary Accent
  static const Color teal = Color(0xFF00B4D8);             // Deep Maritime Teal
  static const Color gold = Color(0xFFFFD166);             // Amber Gold
  static const Color emerald = Color(0xFF00F5D4);          // High-vis Success Emerald
  static const Color coral = Color(0xFFFF5A5F);            // Warning & Alert Coral
  static const Color textLight = Color(0xFFE6EDF8);        // High-contrast Light Text (WCAG AAA)
  static const Color textMuted = Color(0xFF90A4CB);        // Secondary Descriptive Text
}

class MaritimeTheme {
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      primaryColor: MaritimeColors.cyan,
      scaffoldBackgroundColor: MaritimeColors.background,
      cardColor: MaritimeColors.surface,
      colorScheme: const ColorScheme.dark(
        primary: MaritimeColors.cyan,
        secondary: MaritimeColors.gold,
        surface: MaritimeColors.surface,
        error: MaritimeColors.coral,
      ),
      fontFamily: 'Segoe UI',
      appBarTheme: const AppBarTheme(
        backgroundColor: MaritimeColors.surface,
        elevation: 1,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: MaritimeColors.cyan,
          fontSize: 18,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: MaritimeColors.surfaceCard,
        elevation: 3,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: MaritimeColors.border, width: 1.2),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: MaritimeColors.cyan.withOpacity(0.18),
          foregroundColor: MaritimeColors.cyan,
          side: const BorderSide(color: MaritimeColors.cyan, width: 1.4),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          elevation: 2,
          shadowColor: MaritimeColors.cyan.withOpacity(0.3),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          textStyle: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.6, fontSize: 13.5),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: MaritimeColors.textLight,
          side: const BorderSide(color: MaritimeColors.border, width: 1.2),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, letterSpacing: 0.4),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: MaritimeColors.surfaceCard,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: MaritimeColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: MaritimeColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: MaritimeColors.cyan, width: 1.8),
        ),
        hintStyle: const TextStyle(color: MaritimeColors.textMuted, fontSize: 13.5),
        labelStyle: const TextStyle(color: MaritimeColors.cyan, fontWeight: FontWeight.bold),
      ),
      sliderTheme: const SliderThemeData(
        activeTrackColor: MaritimeColors.cyan,
        inactiveTrackColor: MaritimeColors.border,
        thumbColor: MaritimeColors.emerald,
        overlayColor: Color(0x3300E5FF),
      ),
    );
  }
}
