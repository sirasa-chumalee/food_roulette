import 'package:flutter/foundation.dart';

class AppConfig {
  static const bool useMock = bool.fromEnvironment(
    'USE_MOCK',
    defaultValue: false,
  );

  /// Explicit --dart-define=API_BASE_URL=... always wins.
  static const String _envBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  /// Single source of truth for the backend address. Every provider and
  /// service must read this — never hardcode a loopback URL locally.
  ///
  /// Defaults are platform-aware because loopback differs by target:
  /// the Android emulator reaches the host machine via 10.0.2.2, while the
  /// iOS simulator, macOS and desktop builds talk to plain 127.0.0.1.
  static String get baseUrl {
    if (_envBaseUrl.isNotEmpty) return _envBaseUrl;
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }
}
