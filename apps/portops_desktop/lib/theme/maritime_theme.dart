// Panama PortOps-AI v2.0 - Industrial Maritime Theme
// Author: Desarrollado v1.0 Miguel Benítez
// License: GNU GPL-3.0 with Section 7 Mandatory Attribution

import 'package:flutter/material.dart';

class MaritimeColors {
  static const Color background = Color(0xFF0A192F);       // Deep Oceanic Navy
  static const Color surface = Color(0xFF112240);          // Slate Dark Blue
  static const Color surfaceCard = Color(0xFF1B2E4B);      // Lighter Slate Blue
  static const Color border = Color(0xFF233554);           // Muted Slate Border
  static const Color cyan = Color(0xFF64FFDA);             // Teal Glow / Accent
  static const Color gold = Color(0xFFFFD166);             // Amber Gold
  static const Color emerald = Color(0xFF10B981);          // Success Emerald
  static const Color coral = Color(0xFFF43F5E);            // Alert Coral
  static const Color textLight = Color(0xFFCCD6F6);        // High-contrast Light Text
  static const Color textMuted = Color(0xFF8892B0);        // Secondary Text
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
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: MaritimeColors.cyan,
          fontSize: 18,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: MaritimeColors.surface,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: MaritimeColors.border, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: MaritimeColors.cyan.withOpacity(0.15),
          foregroundColor: MaritimeColors.cyan,
          side: const BorderSide(color: MaritimeColors.cyan, width: 1.2),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: 0.5),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: MaritimeColors.surfaceCard,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: MaritimeColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: MaritimeColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: MaritimeColors.cyan, width: 1.5),
        ),
        hintStyle: const TextStyle(color: MaritimeColors.textMuted),
        labelStyle: const TextStyle(color: MaritimeColors.cyan),
      ),
    );
  }
}
