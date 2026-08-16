import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../../../data/models/restaurant_detail.dart';

const String baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

final restaurantDetailProvider =
    FutureProvider.family.autoDispose<RestaurantDetail, String>(
        (ref, restaurantId) async {
  final response =
      await http.get(Uri.parse('$baseUrl/restaurants/$restaurantId'));
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return RestaurantDetail.fromJson(data, baseUrl);
  } else {
    throw Exception('Failed to load restaurant details (${response.statusCode})');
  }
});