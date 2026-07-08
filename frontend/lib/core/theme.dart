import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Hyper-minimalist, large-touch-target theme for non-tech family users.
ThemeData buildTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF00695C), // calm teal
    brightness: Brightness.light,
  );

  final base = ThemeData(colorScheme: scheme, useMaterial3: true);

  return base.copyWith(
    scaffoldBackgroundColor: const Color(0xFFF6F7F9),
    textTheme: GoogleFonts.cairoTextTheme(base.textTheme),
    appBarTheme: AppBarTheme(
      centerTitle: true,
      backgroundColor: scheme.surface,
      foregroundColor: scheme.onSurface,
      elevation: 0,
      titleTextStyle: GoogleFonts.cairo(
        fontSize: 24, fontWeight: FontWeight.w700, color: scheme.onSurface,
      ),
    ),
    // Big, unmistakable buttons.
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        minimumSize: const Size.fromHeight(72),
        textStyle: GoogleFonts.cairo(fontSize: 24, fontWeight: FontWeight.w700),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.all(20),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(18)),
      hintStyle: GoogleFonts.cairo(fontSize: 20, color: Colors.black38),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      margin: const EdgeInsets.symmetric(vertical: 8),
    ),
  );
}
