/// App-wide configuration.
///
/// The backend base URL can be injected at build/run time:
///   flutter run --dart-define=API_BASE=http://localhost:8000
///
/// When empty (the production case, where FastAPI serves this PWA itself),
/// we fall back to the same origin the app was loaded from.
class AppConfig {
  static const String _defineBase =
      String.fromEnvironment('API_BASE', defaultValue: '');

  static String get apiBase =>
      _defineBase.isNotEmpty ? _defineBase : Uri.base.origin;

  /// Family message hard limit — mirrors the backend + TRMNL layout budget.
  static const int messageMaxChars = 120;

  /// Seconds the "Send" button stays disabled after a tap (double-tap guard).
  static const int sendCooldownSeconds = 5;
}
