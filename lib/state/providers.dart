import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../core/constants.dart';
import '../features/auth/auth_provider.dart';
import '../data/api/api_client.dart';
import '../data/api/http_api.dart';
import '../data/api/mock_api.dart';
import '../data/models/menu_item.dart';
import '../data/models/recommendation.dart';
import '../data/models/restaurant.dart';
import '../data/models/user_preferences.dart';

// Backend address comes from AppConfig (platform-aware loopback; override
// with --dart-define=API_BASE_URL=...).
final String baseUrl = AppConfig.baseUrl;

/// Shared bearer-header builder for every authenticated call. Identity lives
/// in the Authorization header (signed JWT); the backend never accepts a
/// user_id from the body anymore.
Map<String, String> authHeaders(Ref ref) {
  final token = ref.read(authProvider.notifier).currentToken;
  return {
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Bearer $token',
  };
}

// 1. Profile / Preferences Notifier
class ProfileNotifier extends AsyncNotifier<UserPreferences> {
  @override
  Future<UserPreferences> build() async {
    return UserPreferences();
  }

  Future<void> updatePreferences(UserPreferences newPrefs) async {
    state = AsyncValue.data(newPrefs);
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/preferences'),
        headers: authHeaders(ref),
        body: jsonEncode(newPrefs.toJson()),
      );
      if (response.statusCode == 200) {
        // Refresh recommendations automatically when preferences update
        ref.invalidate(recommendationsProvider);
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        await ref.read(authProvider.notifier).sessionExpired();
      }
    } catch (_) {
      // Backend optional during UI mock testing
    }
  }
}

final profileProvider =
    AsyncNotifierProvider<ProfileNotifier, UserPreferences>(ProfileNotifier.new);

// 2. Recommendations Notifier
class RecommendationsNotifier extends AsyncNotifier<RecommendOut> {
  @override
  Future<RecommendOut> build() async {
    return _fetchRecommendations();
  }

  Future<RecommendOut> refreshRecommendations({
    String? prompt,
  }) async {
    state = const AsyncLoading();

    try {
      final result = await _fetchRecommendations(
        prompt: prompt,
      );

      state = AsyncData(result);

      return result;
    } catch (e, st) {
      state = AsyncError(e, st);
      rethrow;
    }
  }

  Future<RecommendOut> _fetchRecommendations({
    String? prompt,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/recommend'),
        headers: authHeaders(ref),
        body: jsonEncode({
          "limit": 4,

          // Optional if your backend supports chat prompts
          if (prompt != null) "prompt": prompt,
        }),
      );

      if (response.statusCode == 200) {
        return RecommendOut.fromJson(
          jsonDecode(response.body),
          baseUrl,
        );
      }
      // Dead session: log out and propagate — never fall back to mock data
      // while the user is actually logged out.
      if (response.statusCode == 401 || response.statusCode == 403) {
        await ref.read(authProvider.notifier).sessionExpired();
      }

      throw Exception("server returned ${response.statusCode}");
    } catch (e) {
      // A dead session must surface, not masquerade as offline mode.
      if (e is AuthRequiredError) rethrow;
      return RecommendOut(
      fallbackUsed: true,
      recommendations: [
        RecommendedRestaurant(
          restaurantId: 'tu_place_1',
          nameTh: "Matthew's",
          safetyTier: 'verified',
          needsAck: false,
          excludedCount: 12,
          rating: 4.7,
          safeDishes: [
            SafeDish(
              id: 1,
              nameTh: 'ไข่ตุ๋นฟูจิ',
              priceThb: 200.0,
              spicyLevel: 0,
              safetyTier: 'verified',
            ),
          ],
        ),
        RecommendedRestaurant(
          restaurantId: 'tu_place_8',
          nameTh: 'เรสเตอร์ เดย์',
          safetyTier: 'unverified',
          needsAck: true,
          ackReason: 'Unverified ingredient record',
          excludedCount: 5,
          rating: 3.4,
          safeDishes: [
            SafeDish(
              id: 8,
              nameTh: 'Cajun Seafood Pasta',
              priceThb: 250.0,
              spicyLevel: 1,
              safetyTier: 'unverified',
            ),
          ],
        ),
      ],
    );
    }
  }
}

final recommendationsProvider =
    AsyncNotifierProvider<RecommendationsNotifier, RecommendOut>(
        RecommendationsNotifier.new);

final apiClientProvider = Provider<FoodRouletteApi>((ref) {
  if (AppConfig.useMock) {
    return MockApi();
  }
  return HttpApi();
});

final healthCheckProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.checkHealth();
});

final restaurantsProvider = FutureProvider<List<Restaurant>>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.getRestaurants();
});

final restaurantMenuProvider =
    FutureProvider.family<List<MenuItem>, String>((ref, restaurantId) async {
  final api = ref.watch(apiClientProvider);
  return api.getMenuItemsByRestaurantId(restaurantId);
});