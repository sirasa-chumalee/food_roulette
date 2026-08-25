// Auth repository: register / login against the FastAPI backend.
//
// Contract (backend/app/schemas.py):
//   POST /auth/register {email, password, display_name} -> 201 {id, email, ...}
//   POST /auth/login    {email, password}               -> 200 {access_token,
//                                                            token_type, user_id}
// Errors arrive as {"error": "<CODE>", "message": "..."} with a non-2xx status;
// we surface the message so the login screen can show *why* it failed.
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../core/constants.dart';
import '../../data/auth/token_store.dart';

class AuthException implements Exception {
  final String message;
  AuthException(this.message);
  @override
  String toString() => message;
}

class AuthRepository {
  AuthRepository({http.Client? client, TokenStore? tokenStore})
      : _client = client ?? http.Client(),
        tokenStore = tokenStore ?? TokenStore();

  final http.Client _client;
  final TokenStore tokenStore;

  Uri _uri(String path) => Uri.parse('${AppConfig.baseUrl}$path');

  /// Register a new account and immediately log into it. Returns the user id.
  Future<String> register({
    required String email,
    required String password,
    required String displayName,
  }) async {
    final response = await _client.post(
      _uri('/auth/register'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'display_name': displayName,
      }),
    );

    if (response.statusCode == 201) return userIdFromJson(response.body);

    throw AuthException(_errorMessage(response, fallback: 'Could not create the account.'));
  }

  /// Log in and persist the bearer token + user id in secure storage.
  Future<void> login({
    required String email,
    required String password,
  }) async {
    final response = await _client.post(
      _uri('/auth/login'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode != 200) {
      throw AuthException(_errorMessage(response, fallback: 'Wrong email or password.'));
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final token = data['access_token'] as String?;
    final userId = data['user_id'] as String?;
    if (token == null || userId == null) {
      throw AuthException('Login response was missing its token.');
    }
    await tokenStore.save(token: token, userId: userId);
  }

  Future<void> logout() => tokenStore.clear();

  /// Best-effort restore at app start; null when no session was stored.
  Future<({String userId, String token})?> restore() async {
    final token = await tokenStore.readToken();
    final userId = await tokenStore.readUserId();
    if (token == null || userId == null) return null;
    return (userId: userId, token: token);
  }

  // --- helpers -------------------------------------------------------------

  static String userIdFromJson(String body) =>
      (jsonDecode(body) as Map<String, dynamic>)['id'] as String;

  static String _errorMessage(http.Response response, {required String fallback}) {
    try {
      final data = jsonDecode(response.body);
      if (data is Map && data['message'] is String && (data['message'] as String).isNotEmpty) {
        return data['message'] as String;
      }
    } catch (_) {}
    return fallback;
  }
}
