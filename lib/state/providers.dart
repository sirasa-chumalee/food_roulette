import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../core/constants.dart';
import '../data/api/api_client.dart';
import '../data/api/http_api.dart';
import '../data/api/mock_api.dart';
import '../data/models/menu_item.dart';
import '../data/models/recommendation.dart';
import '../data/models/restaurant.dart';
import '../data/models/user_preferences.dart';

const baseUrl = 'http://127.0.0.1:8000';

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
        Uri.parse('$baseUrl/users/1/preferences'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(newPrefs.toJson()),
      );
      if (response.statusCode == 200) {
        // Refresh recommendations automatically when preferences update
        ref.invalidate(recommendationsProvider);
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
    // Watching profileProvider ensures recommendations refresh when user changes preferences
    await ref.watch(profileProvider.future);

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/recommend'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "user_id": "1",
          "limit": 4,
        }),
      );

      if (response.statusCode == 200) {
        return RecommendOut.fromJson(jsonDecode(response.body));
      }
    } catch (_) {}

    // Fallback Mock Data matching RecommendOut schema
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