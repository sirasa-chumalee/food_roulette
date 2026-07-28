//apiClientProvider: Checks the runtime flag (AppConfig.useMock) and dynamically supplies either MockApi() or HttpApi() to the rest of the application.

//restaurantsProvider: A FutureProvider or AsyncNotifier that fetches the list of restaurants via apiClientProvider.

//Feature Notifiers (M1+): Holds state providers like profileProvider (user's dietary constraints & preferences) and recommendationsProvider.
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants.dart';
import '../data/api/api_client.dart';
import '../data/api/http_api.dart';
import '../data/api/mock_api.dart';
import '../data/models/menu_item.dart';
import '../data/models/restaurant.dart';

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

final restaurantMenuProvider = FutureProvider.family<List<MenuItem>, String>((ref, restaurantId) async {
  final api = ref.watch(apiClientProvider);
  return api.getMenuItemsByRestaurantId(restaurantId);
});