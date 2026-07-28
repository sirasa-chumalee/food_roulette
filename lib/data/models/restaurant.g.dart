// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'restaurant.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$RestaurantImpl _$$RestaurantImplFromJson(Map<String, dynamic> json) =>
    _$RestaurantImpl(
      restaurantId: json['restaurant_id'] as String?,
      id: json['id'] as String?,
      googlePlaceId: json['google_place_id'] as String?,
      nameTh: json['name_th'] as String,
      nameEn: json['name_en'] as String?,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      priceBand: (json['price_band'] as num?)?.toInt(),
      priceTier: json['price_tier'] as String?,
      isHalalCertified: (json['is_halal_certified'] as num?)?.toInt() ?? 0,
      hasParking: (json['has_parking'] as num?)?.toInt() ?? 2,
      distanceM: (json['distance_m'] as num?)?.toInt(),
      rating: (json['rating'] as num?)?.toDouble(),
      photoUrl: json['photo_url'] as String?,
      safetyTier: json['safety_tier'] as String? ?? 'verified',
      needsAck: json['needs_ack'] as bool? ?? false,
      ackReason: json['ack_reason'] as String?,
      safeDishes:
          (json['safe_dishes'] as List<dynamic>?)
              ?.map((e) => e as Map<String, dynamic>)
              .toList() ??
          const [],
      excludedCount: (json['excluded_count'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$RestaurantImplToJson(_$RestaurantImpl instance) =>
    <String, dynamic>{
      'restaurant_id': instance.restaurantId,
      'id': instance.id,
      'google_place_id': instance.googlePlaceId,
      'name_th': instance.nameTh,
      'name_en': instance.nameEn,
      'latitude': instance.latitude,
      'longitude': instance.longitude,
      'price_band': instance.priceBand,
      'price_tier': instance.priceTier,
      'is_halal_certified': instance.isHalalCertified,
      'has_parking': instance.hasParking,
      'distance_m': instance.distanceM,
      'rating': instance.rating,
      'photo_url': instance.photoUrl,
      'safety_tier': instance.safetyTier,
      'needs_ack': instance.needsAck,
      'ack_reason': instance.ackReason,
      'safe_dishes': instance.safeDishes,
      'excluded_count': instance.excludedCount,
    };
