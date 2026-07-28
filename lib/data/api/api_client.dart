//Defines the contract for what network calls your app can make
import '../models/menu_item.dart';
import '../models/restaurant.dart';

abstract class FoodRouletteApi {
  Future<Map<String, dynamic>> checkHealth();
  Future<List<Restaurant>> getRestaurants();
  Future<Restaurant> getRestaurantById(String id);
  Future<List<MenuItem>> getMenuItemsByRestaurantId(String restaurantId);
}