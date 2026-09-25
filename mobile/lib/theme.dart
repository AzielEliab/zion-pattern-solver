import 'package:flutter/material.dart';

/// Gold accent shared by light and dark. No analytics.
const Color kMatteBlack = Color(0xFF12110E);
const Color kSurface = Color(0xFF1C1B16);
const Color kGold = Color(0xFFC9A227);
const Color kGoldDim = Color(0xFF8A7219);
const Color kIvory = Color(0xFFF4F0E6);
const Color kPaper = Color(0xFFF6F3EA);
const Color kInk = Color(0xFF1C1914);

ThemeData buildLightTheme() {
  return _theme(
    const ColorScheme.light(
      primary: kGold,
      onPrimary: kInk,
      secondary: kGoldDim,
      onSecondary: kIvory,
      surface: Color(0xFFFFFDF8),
      onSurface: kInk,
      error: Color(0xFF8C2E22),
      onError: Color(0xFFFFFDF8),
    ),
    scaffold: kPaper,
  );
}

ThemeData buildDarkTheme() {
  return _theme(
    const ColorScheme.dark(
      primary: kGold,
      onPrimary: kInk,
      secondary: kGoldDim,
      onSecondary: kIvory,
      surface: kSurface,
      onSurface: kIvory,
      error: Color(0xFFF0B2A8),
      onError: kInk,
    ),
    scaffold: kMatteBlack,
  );
}

/// Dark theme kept for callers that want an explicit night surface.
ThemeData buildAppTheme() => buildDarkTheme();

ThemeData _theme(ColorScheme scheme, {required Color scaffold}) {
  final onGold = scheme.onPrimary;
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: scaffold,
    focusColor: kGold,
    hoverColor: const Color(0x14C9A227),
    appBarTheme: AppBarTheme(
      backgroundColor: scaffold,
      foregroundColor: scheme.onSurface,
      elevation: 0,
      centerTitle: false,
    ),
    cardTheme: CardThemeData(
      color: scheme.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: scheme.brightness == Brightness.dark ? const Color(0xFF343128) : const Color(0xFFE4DCC8)),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: kGold,
        foregroundColor: onGold,
        minimumSize: const Size(64, 48),
      ),
    ),
    sliderTheme: const SliderThemeData(
      activeTrackColor: kGold,
      thumbColor: kGold,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: kGold, width: 2),
      ),
    ),
  );
}
