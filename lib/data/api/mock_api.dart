//Role: Local Mock Implementation.

//Purpose: Implements FoodRouletteApi by reading local static JSON fixtures directly from docs/api/fixtures/ using Flutter’s rootBundle. This lets you develop and test UI features offline without needing a running backend.

import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/menu_item.dart';
import '../models/restaurant.dart';
import 'api_client.dart';

class MockApi implements FoodRouletteApi {
  @override
  Future<Map<String, dynamic>> checkHealth() async {
    return {
      "status": "ok",
      "version": "0.1.0-mock",
      "restaurants": 50,
      "menu_items": 1250
    };
  }

  @override
  Future<List<Restaurant>> getRestaurants() async {
    final String jsonString = await rootBundle.loadString('docs/api/fixtures/restaurants.json');
    final List<dynamic> jsonList = jsonDecode(jsonString);
    return jsonList.map((e) => Restaurant.fromJson(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<Restaurant> getRestaurantById(String id) async {
    final list = await getRestaurants();
    return list.firstWhere(
      (r) => r.effectiveId == id,
      orElse: () => throw Exception('Restaurant $id not found in mock fixtures'),
    );
  }

  @override
  Future<List<MenuItem>> getMenuItemsByRestaurantId(String restaurantId) async {
    final String jsonString = await rootBundle.loadString('docs/api/fixtures/menu_items.json');
    final List<dynamic> jsonList = jsonDecode(jsonString);
    final allItems = jsonList.map((e) => MenuItem.fromJson(e as Map<String, dynamic>)).toList();
    return allItems.where((item) => item.restaurantId == restaurantId).toList();
  }
}