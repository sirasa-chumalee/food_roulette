import 'package:freezed_annotation/freezed_annotation.dart';

part 'restaurant.freezed.dart';
part 'restaurant.g.dart';

@freezed
class Restaurant with _$Restaurant {
  const factory Restaurant({
    // Handles both raw ingest "id" and contract "restaurant_id"
    @JsonKey(name: 'restaurant_id') String? restaurantId,
    String? id,

    @JsonKey(name: 'google_place_id') String? googlePlaceId,
    @JsonKey(name: 'name_th') required String nameTh,
    @JsonKey(name: 'name_en') String? nameEn,
    required double latitude,
    required double longitude,
    @JsonKey(name: 'price_band') int? priceBand,
    @JsonKey(name: 'price_tier') String? priceTier,
    @JsonKey(name: 'is_halal_certified') @Default(0) int isHalalCertified,
    @JsonKey(name: 'has_parking') @Default(2) int hasParking,

    // Recommendation Contract §3.1 Fields
    @JsonKey(name: 'distance_m') int? distanceM,
    double? rating,
    @JsonKey(name: 'photo_url') String? photoUrl,
    @JsonKey(name: 'safety_tier') @Default('verified') String safetyTier,
    @JsonKey(name: 'needs_ack') @Default(false) bool needsAck,
    @JsonKey(name: 'ack_reason') String? ackReason,
    @JsonKey(name: 'safe_dishes') @Default([]) List<Map<String, dynamic>> safeDishes,
    @JsonKey(name: 'excluded_count') @Default(0) int excludedCount,
  }) = _Restaurant;

  factory Restaurant.fromJson(Map<String, dynamic> json) => _$RestaurantFromJson(json);
}

extension RestaurantX on Restaurant {
  String get effectiveId => restaurantId ?? id ?? '';

  String get parkingStatusText {
    switch (hasParking) {
      case 1:
        return 'Has Parking';
      case 0:
        return 'No Parking';
      default:
        return 'Parking Unknown';
    }
  }
}