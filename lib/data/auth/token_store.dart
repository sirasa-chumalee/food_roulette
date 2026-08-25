// Token storage for the JWT access token.
//
// The bearer token IS the user's identity for every protected call, so it must
// never live in plain SharedPreferences (backed by an unencrypted XML file,
// trivially readable on a rooted device or a backup). flutter_secure_storage
// routes through the Android Keystore / iOS Keychain instead.
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenStore {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static const _tokenKey = 'access_token';
  static const _userIdKey = 'user_id';

  Future<void> save({required String token, required String userId}) async {
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _userIdKey, value: userId);
  }

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<String?> readUserId() => _storage.read(key: _userIdKey);

  /// True when a previous session left a token behind. Only a liveness hint:
  /// an expired/stale token still counts here, and the first API call will get
  /// a 401 that logs the session out.
  Future<bool> hasToken() async =>
      await readToken() != null;

  Future<void> clear() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _userIdKey);
  }
}
