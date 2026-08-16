class RestaurantReview {
  final String authorName;
  final double rating;
  final String text;
  final String relativeTime;

  const RestaurantReview({
    required this.authorName,
    required this.rating,
    required this.text,
    required this.relativeTime,
  });

  factory RestaurantReview.fromJson(Map<String, dynamic> json) {
    return RestaurantReview(
      authorName: json['author_name']?.toString() ?? 'Anonymous',
      rating: (json['rating'] as num?)?.toDouble() ?? 0.0,
      text: json['text']?.toString() ?? '',
      relativeTime: json['relative_time']?.toString() ?? '',
    );
  }
}

class DetailMenuItem {
  final int id;
  final String nameTh;
  final String? nameEn;
  final double priceThb;
  final int spicyLevel;
  final String safetyTier;

  const DetailMenuItem({
    required this.id,
    required this.nameTh,
    this.nameEn,
    required this.priceThb,
    required this.spicyLevel,
    this.safetyTier = 'verified',
  });

  factory DetailMenuItem.fromJson(Map<String, dynamic> json) {
    return DetailMenuItem(
      id: json['id'] as int? ?? 0,
      nameTh: json['name_th']?.toString() ?? '',
      nameEn: json['name_en']?.toString(),
      priceThb: (json['price_thb'] as num?)?.toDouble() ?? 0.0,
      spicyLevel: json['spicy_level'] as int? ?? 0,
      safetyTier: json['safety_tier']?.toString() ?? 'verified',
    );
  }
}

class RestaurantDetail {
  final String id;
  final String nameTh;
  final String? nameEn;
  final String? placesDisplayName;
  final String? address;
  final String? priceTier;
  final double? rating;
  final int? userRatingCount;
  final List<String> photos;
  final List<String> openingHours;
  final List<RestaurantReview> reviews;
  final List<DetailMenuItem> safeDishes;

  const RestaurantDetail({
    required this.id,
    required this.nameTh,
    this.nameEn,
    this.placesDisplayName,
    this.address,
    this.priceTier,
    this.rating,
    this.userRatingCount,
    this.photos = const [],
    this.openingHours = const [],
    this.reviews = const [],
    this.safeDishes = const [],
  });

  /// Cover photo (first photo with full baseUrl resolution)
  String? get coverPhotoUrl => photos.isNotEmpty ? photos.first : null;

  /// Prefers Places display name, falls back to Thai name
  String get displayName =>
      placesDisplayName?.isNotEmpty == true ? placesDisplayName! : nameTh;

  factory RestaurantDetail.fromJson(Map<String, dynamic> json, String baseUrl) {
    final rest = json['restaurant'] as Map<String, dynamic>? ?? {};
    final places = json['places'] as Map<String, dynamic>?;

    // 1. Resolve Safe Dishes & Menu
    final dishesList = (json['safe_dishes'] as List? ?? json['menu'] as List? ?? [])
        .map((e) => DetailMenuItem.fromJson(e as Map<String, dynamic>))
        .toList();

    // 2. Resolve Places Photos (prepend baseUrl to relative paths)
    List<String> resolvedPhotos = [];
    if (places != null && places['photos'] != null) {
      resolvedPhotos = (places['photos'] as List).map((p) {
        final path = p.toString();
        return path.startsWith('http') ? path : '$baseUrl$path';
      }).toList();
    }

    // 3. Resolve Places Reviews
    List<RestaurantReview> resolvedReviews = [];
    if (places != null && places['reviews'] != null) {
      resolvedReviews = (places['reviews'] as List)
          .map((r) => RestaurantReview.fromJson(r as Map<String, dynamic>))
          .toList();
    }

    // 4. Resolve Opening Hours List
    List<String> resolvedHours = [];
    if (places != null && places['opening_hours'] != null) {
      resolvedHours = (places['opening_hours'] as List)
          .map((h) => h.toString())
          .toList();
    }

    return RestaurantDetail(
      id: rest['id']?.toString() ?? '',
      nameTh: rest['name_th']?.toString() ?? '',
      nameEn: rest['name_en']?.toString(),
      priceTier: rest['price_band']?.toString(),
      placesDisplayName: places?['display_name']?.toString(),
      address: places?['formatted_address']?.toString(),
      rating: places?['rating'] != null ? (places!['rating'] as num).toDouble() : null,
      userRatingCount: places?['user_rating_count'] as int?,
      photos: resolvedPhotos,
      openingHours: resolvedHours,
      reviews: resolvedReviews,
      safeDishes: dishesList,
    );
  }
}