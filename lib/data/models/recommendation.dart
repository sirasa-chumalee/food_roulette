class SafeDish {
  final int id;
  final String? nameTh;
  final String? nameEn;
  final double priceThb;
  final int spicyLevel;
  final String safetyTier; // "verified" | "unverified"

  SafeDish({
    required this.id,
    this.nameTh,
    this.nameEn,
    required this.priceThb,
    required this.spicyLevel,
    required this.safetyTier,
  });

  factory SafeDish.fromJson(Map<String, dynamic> json) {
    return SafeDish(
      id: json['id'] ?? 0,
      nameTh: json['name_th'],
      nameEn: json['name_en'],
      priceThb: (json['price_thb'] ?? 0.0).toDouble(),
      spicyLevel: json['spicy_level'] ?? 0,
      safetyTier: json['safety_tier'] ?? 'unverified',
    );
  }
}

class RecommendedRestaurant {
  final String restaurantId;
  final String? nameTh;
  final String? nameEn;
  final double? latitude;
  final double? longitude;
  final double? distanceM;
  final String? priceTier;
  final double? rating;
  final String? photoUrl;
  final String? description;
  final String safetyTier; // "verified" | "unverified"
  final bool needsAck;
  final String? ackReason;
  final int excludedCount;
  final List<SafeDish> safeDishes;

  RecommendedRestaurant({
    required this.restaurantId,
    this.nameTh,
    this.nameEn,
    this.latitude,
    this.longitude,
    this.distanceM,
    this.priceTier,
    this.rating,
    this.photoUrl,
    this.description,
    required this.safetyTier,
    required this.needsAck,
    this.ackReason,
    required this.excludedCount,
    required this.safeDishes,
  });

  bool get isVerified => safetyTier == 'verified';
  String get displayName => nameTh ?? nameEn ?? 'Restaurant';

  factory RecommendedRestaurant.fromJson(Map<String, dynamic> json) {
  // Safe rating parser handling int, double, or String
  double? parseRating(dynamic rawRating) {
    if (rawRating == null) return null;
    if (rawRating is num) return rawRating.toDouble();
    if (rawRating is String) return double.tryParse(rawRating);
    return null;
  }

  return RecommendedRestaurant(
    restaurantId: json['restaurant_id'] ?? '',
    nameTh: json['name_th'],
    nameEn: json['name_en'],
    latitude: (json['latitude'] as num?)?.toDouble(),
    longitude: (json['longitude'] as num?)?.toDouble(),
    distanceM: (json['distance_m'] as num?)?.toDouble(),
    priceTier: json['price_tier'],
    rating: parseRating(json['rating'] ?? json['stars'] ?? json['score']),
    photoUrl: json['photo_url'],
    description: json['description'],
    safetyTier: json['safety_tier'] ?? 'unverified',
    needsAck: json['needs_ack'] ?? false,
    ackReason: json['ack_reason'],
    excludedCount: json['excluded_count'] ?? 0,
    safeDishes: (json['safe_dishes'] as List? ?? [])
        .map((e) => SafeDish.fromJson(e))
        .toList(),
  );
}
}

class RecommendOut {
  final List<RecommendedRestaurant> recommendations;
  final bool fallbackUsed;

  RecommendOut({
    required this.recommendations,
    required this.fallbackUsed,
  });

  factory RecommendOut.fromJson(Map<String, dynamic> json) {
    return RecommendOut(
      recommendations: (json['recommendations'] as List? ?? [])
          .map((e) => RecommendedRestaurant.fromJson(e))
          .toList(),
      fallbackUsed: json['fallback_used'] ?? false,
    );
  }
}