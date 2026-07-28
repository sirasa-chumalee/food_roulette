import 'package:flutter/material.dart';

class FoodTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorSchemeSeed: Colors.black, // <-- Prevents auto-generated green accents
      brightness: Brightness.light,
      
      // Override FilterChip / ChoiceChip styles app-wide
      chipTheme: ChipThemeData(
        selectedColor: const Color(0xFF333333), // Dark grey when selected
        secondarySelectedColor: const Color(0xFF333333),
        labelStyle: const TextStyle(color: Colors.black),
        secondaryLabelStyle: const TextStyle(color: Colors.white),
        checkmarkColor: Colors.white, // White checkmark instead of green
        side: const BorderSide(color: Color(0xFF333333)),
      ),
      
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
      ),
    );
  }
}