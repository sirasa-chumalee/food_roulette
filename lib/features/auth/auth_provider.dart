// Session state: is anyone logged in, and as whom?
//
// AuthState mirrors go_router's redirect contract:
//   unknown  -> still deciding (show splash)
//   loggedIn -> /chat allowed; /login redirects back
//   loggedOut-> /chat redirects to /login
// The 401 interceptor calls logout() on an expired/invalid token, which flips
// this to loggedOut and the router bounces every screen to /login.
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_repository.dart';

enum AuthStatus { unknown, loggedIn, loggedOut }

/// Thrown when the backend rejects the token (401/403). The session is dead —
/// call sites must not mask this with offline/mock fallbacks.
class AuthRequiredError implements Exception {
  @override
  String toString() => 'Authentication required';
}

class AuthState {
  final AuthStatus status;
  final String? userId;

  const AuthState({this.status = AuthStatus.unknown, this.userId});

  AuthState copyWith({AuthStatus? status, String? userId}) => AuthState(
        status: status ?? this.status,
        userId: userId ?? this.userId,
      );
}

class AuthController extends Notifier<AuthState> {
  AuthRepository get _repo => ref.read(authRepositoryProvider);

  /// In-memory mirror of the secure-storage token. flutter_secure_storage is
  /// async-only, but HTTP call sites need the header synchronously — they read
  /// this instead of touching disk per request.
  String? _currentToken;
  String? get currentToken => _currentToken;

  @override
  AuthState build() {
    _restore();
    return const AuthState();
  }

  Future<void> _restore() async {
    // Secure storage can be unreadable (test runners have no platform
    // channel; a real device can refuse Keychain/Keystore access). A failure
    // here must degrade to logged-out, never hang the app on splash.
    ({String userId, String token})? session;
    try {
      session = await _repo.restore();
    } catch (_) {
      session = null;
    }
    // The await above can outlive this notifier (app closed mid-restore);
    // touching `state` then throws, so swallow exactly that case.
    try {
      _currentToken = session?.token;
      state = session == null
          ? const AuthState(status: AuthStatus.loggedOut)
          : AuthState(status: AuthStatus.loggedIn, userId: session.userId);
    } on StateError {
      // Notifier already disposed — nothing left to update.
    }
  }

  Future<void> registerAndLogin({
    required String email,
    required String password,
    required String displayName,
  }) async {
    await _repo.register(
        email: email, password: password, displayName: displayName);
    await _repo.login(email: email, password: password);
    final restored = await _repo.restore();
    _currentToken = restored?.token;
    state = AuthState(
      status: AuthStatus.loggedIn,
      userId: restored?.userId,
    );
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    await _repo.login(email: email, password: password);
    final restored = await _repo.restore();
    _currentToken = restored?.token;
    state = AuthState(
      status: AuthStatus.loggedIn,
      userId: restored?.userId,
    );
  }

  /// Called by the logout button AND by the 401 interceptor whenever the
  /// backend rejects a stored token (expired, revoked, or user deleted).
  Future<void> logout() async {
    try {
      await _repo.logout();
    } finally {
      _currentToken = null;
      state = const AuthState(status: AuthStatus.loggedOut);
    }
  }

  /// For API call sites: the backend answered 401/403, so the token is dead.
  /// Logs out exactly once (parallel failing calls see the cleared token and
  /// skip straight to the throw) and always throws [AuthRequiredError] so no
  /// caller masks a dead session behind offline/mock fallback data.
  Future<Never> sessionExpired() async {
    if (_currentToken != null) await logout();
    throw AuthRequiredError();
  }
}

final authProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});
