class AppConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000', // Android emulator loopback
  );

  static const bool useMock = bool.fromEnvironment(
    'USE_MOCK',
    defaultValue: false,
  );
}