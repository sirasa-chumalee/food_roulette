//Role: Production HTTP Implementation (using Dio).

//Purpose: Implements FoodRouletteApi by making real network calls to your FastAPI backend server (e.g., [http://10.0.2.2:8000](http://10.0.2.2:8000)).

import 'package:dio/dio.dart';
import '../../core/constants.dart';
import '../models/menu_item.dart';
import '../models/restaurant.dart';
import 'api_client.dart';

class HttpApi implements FoodRouletteApi {
  final Dio _dio;

  HttpApi({Dio? dio})
      : _dio = dio ??
            Dio(
              BaseOptions(
                baseUrl: AppConfig.baseUrl,
                connectTimeout: const Duration(seconds: 5),
                receiveTimeout: const Duration(seconds: 5),
              ),
            );

  @override
  Future<Map<String, dynamic>> checkHealth() async {
    final response = await _dio.get('/health');
    return response.data as Map<String, dynamic>;
  }

  @override
  Future<List<Restaurant>> getRestaurants() async {
    final response = await _dio.get('/restaurants');
    final List<dynamic> data = response.data;
    return data.map((e) => Restaurant.fromJson(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<Restaurant> getRestaurantById(String id) async {
    final response = await _dio.get('/restaurants/$id');
    return Restaurant.fromJson(response.data as Map<String, dynamic>);
  }

  @override
  Future<List<MenuItem>> getMenuItemsByRestaurantId(String restaurantId) async {
    final response = await _dio.get('/restaurants/$restaurantId/menu');
    final List<dynamic> data = response.data;
    return data.map((e) => MenuItem.fromJson(e as Map<String, dynamic>)).toList();
  }
}