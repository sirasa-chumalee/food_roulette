import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../../../core/constants.dart';
import '../../../data/models/restaurant_detail.dart';

// Backend address comes from AppConfig (platform-aware loopback).
final String baseUrl = AppConfig.baseUrl;

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
