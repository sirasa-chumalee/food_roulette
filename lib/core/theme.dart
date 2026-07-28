import 'package:flutter/material.dart';

class FoodTheme { // <-- Changed class name
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorSchemeSeed: const Color.fromARGB(0, 223, 221, 218),
      brightness: Brightness.light,
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
      ),
    );
  }
}