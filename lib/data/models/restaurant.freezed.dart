// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'restaurant.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

Restaurant _$RestaurantFromJson(Map<String, dynamic> json) {
  return _Restaurant.fromJson(json);
}

/// @nodoc
mixin _$Restaurant {
  // Handles both raw ingest "id" and contract "restaurant_id"
  @JsonKey(name: 'restaurant_id')
  String? get restaurantId => throw _privateConstructorUsedError;
  String? get id => throw _privateConstructorUsedError;
  @JsonKey(name: 'google_place_id')
  String? get googlePlaceId => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_th')
  String get nameTh => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_en')
  String? get nameEn => throw _privateConstructorUsedError;
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;
  @JsonKey(name: 'price_band')
  int? get priceBand => throw _privateConstructorUsedError;
  @JsonKey(name: 'price_tier')
  String? get priceTier => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_halal_certified')
  int get isHalalCertified => throw _privateConstructorUsedError;
  @JsonKey(name: 'has_parking')
  int get hasParking => throw _privateConstructorUsedError; // Recommendation Contract §3.1 Fields
  @JsonKey(name: 'distance_m')
  int? get distanceM => throw _privateConstructorUsedError;
  double? get rating => throw _privateConstructorUsedError;
  @JsonKey(name: 'photo_url')
  String? get photoUrl => throw _privateConstructorUsedError;
  @JsonKey(name: 'safety_tier')
  String get safetyTier => throw _privateConstructorUsedError;
  @JsonKey(name: 'needs_ack')
  bool get needsAck => throw _privateConstructorUsedError;
  @JsonKey(name: 'ack_reason')
  String? get ackReason => throw _privateConstructorUsedError;
  @JsonKey(name: 'safe_dishes')
  List<Map<String, dynamic>> get safeDishes =>
      throw _privateConstructorUsedError;
  @JsonKey(name: 'excluded_count')
  int get excludedCount => throw _privateConstructorUsedError;

  /// Serializes this Restaurant to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of Restaurant
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RestaurantCopyWith<Restaurant> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RestaurantCopyWith<$Res> {
  factory $RestaurantCopyWith(
    Restaurant value,
    $Res Function(Restaurant) then,
  ) = _$RestaurantCopyWithImpl<$Res, Restaurant>;
  @useResult
  $Res call({
    @JsonKey(name: 'restaurant_id') String? restaurantId,
    String? id,
    @JsonKey(name: 'google_place_id') String? googlePlaceId,
    @JsonKey(name: 'name_th') String nameTh,
    @JsonKey(name: 'name_en') String? nameEn,
    double latitude,
    double longitude,
    @JsonKey(name: 'price_band') int? priceBand,
    @JsonKey(name: 'price_tier') String? priceTier,
    @JsonKey(name: 'is_halal_certified') int isHalalCertified,
    @JsonKey(name: 'has_parking') int hasParking,
    @JsonKey(name: 'distance_m') int? distanceM,
    double? rating,
    @JsonKey(name: 'photo_url') String? photoUrl,
    @JsonKey(name: 'safety_tier') String safetyTier,
    @JsonKey(name: 'needs_ack') bool needsAck,
    @JsonKey(name: 'ack_reason') String? ackReason,
    @JsonKey(name: 'safe_dishes') List<Map<String, dynamic>> safeDishes,
    @JsonKey(name: 'excluded_count') int excludedCount,
  });
}

/// @nodoc
class _$RestaurantCopyWithImpl<$Res, $Val extends Restaurant>
    implements $RestaurantCopyWith<$Res> {
  _$RestaurantCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of Restaurant
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? restaurantId = freezed,
    Object? id = freezed,
    Object? googlePlaceId = freezed,
    Object? nameTh = null,
    Object? nameEn = freezed,
    Object? latitude = null,
    Object? longitude = null,
    Object? priceBand = freezed,
    Object? priceTier = freezed,
    Object? isHalalCertified = null,
    Object? hasParking = null,
    Object? distanceM = freezed,
    Object? rating = freezed,
    Object? photoUrl = freezed,
    Object? safetyTier = null,
    Object? needsAck = null,
    Object? ackReason = freezed,
    Object? safeDishes = null,
    Object? excludedCount = null,
  }) {
    return _then(
      _value.copyWith(
            restaurantId: freezed == restaurantId
                ? _value.restaurantId
                : restaurantId // ignore: cast_nullable_to_non_nullable
                      as String?,
            id: freezed == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as String?,
            googlePlaceId: freezed == googlePlaceId
                ? _value.googlePlaceId
                : googlePlaceId // ignore: cast_nullable_to_non_nullable
                      as String?,
            nameTh: null == nameTh
                ? _value.nameTh
                : nameTh // ignore: cast_nullable_to_non_nullable
                      as String,
            nameEn: freezed == nameEn
                ? _value.nameEn
                : nameEn // ignore: cast_nullable_to_non_nullable
                      as String?,
            latitude: null == latitude
                ? _value.latitude
                : latitude // ignore: cast_nullable_to_non_nullable
                      as double,
            longitude: null == longitude
                ? _value.longitude
                : longitude // ignore: cast_nullable_to_non_nullable
                      as double,
            priceBand: freezed == priceBand
                ? _value.priceBand
                : priceBand // ignore: cast_nullable_to_non_nullable
                      as int?,
            priceTier: freezed == priceTier
                ? _value.priceTier
                : priceTier // ignore: cast_nullable_to_non_nullable
                      as String?,
            isHalalCertified: null == isHalalCertified
                ? _value.isHalalCertified
                : isHalalCertified // ignore: cast_nullable_to_non_nullable
                      as int,
            hasParking: null == hasParking
                ? _value.hasParking
                : hasParking // ignore: cast_nullable_to_non_nullable
                      as int,
            distanceM: freezed == distanceM
                ? _value.distanceM
                : distanceM // ignore: cast_nullable_to_non_nullable
                      as int?,
            rating: freezed == rating
                ? _value.rating
                : rating // ignore: cast_nullable_to_non_nullable
                      as double?,
            photoUrl: freezed == photoUrl
                ? _value.photoUrl
                : photoUrl // ignore: cast_nullable_to_non_nullable
                      as String?,
            safetyTier: null == safetyTier
                ? _value.safetyTier
                : safetyTier // ignore: cast_nullable_to_non_nullable
                      as String,
            needsAck: null == needsAck
                ? _value.needsAck
                : needsAck // ignore: cast_nullable_to_non_nullable
                      as bool,
            ackReason: freezed == ackReason
                ? _value.ackReason
                : ackReason // ignore: cast_nullable_to_non_nullable
                      as String?,
            safeDishes: null == safeDishes
                ? _value.safeDishes
                : safeDishes // ignore: cast_nullable_to_non_nullable
                      as List<Map<String, dynamic>>,
            excludedCount: null == excludedCount
                ? _value.excludedCount
                : excludedCount // ignore: cast_nullable_to_non_nullable
                      as int,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$RestaurantImplCopyWith<$Res>
    implements $RestaurantCopyWith<$Res> {
  factory _$$RestaurantImplCopyWith(
    _$RestaurantImpl value,
    $Res Function(_$RestaurantImpl) then,
  ) = __$$RestaurantImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @JsonKey(name: 'restaurant_id') String? restaurantId,
    String? id,
    @JsonKey(name: 'google_place_id') String? googlePlaceId,
    @JsonKey(name: 'name_th') String nameTh,
    @JsonKey(name: 'name_en') String? nameEn,
    double latitude,
    double longitude,
    @JsonKey(name: 'price_band') int? priceBand,
    @JsonKey(name: 'price_tier') String? priceTier,
    @JsonKey(name: 'is_halal_certified') int isHalalCertified,
    @JsonKey(name: 'has_parking') int hasParking,
    @JsonKey(name: 'distance_m') int? distanceM,
    double? rating,
    @JsonKey(name: 'photo_url') String? photoUrl,
    @JsonKey(name: 'safety_tier') String safetyTier,
    @JsonKey(name: 'needs_ack') bool needsAck,
    @JsonKey(name: 'ack_reason') String? ackReason,
    @JsonKey(name: 'safe_dishes') List<Map<String, dynamic>> safeDishes,
    @JsonKey(name: 'excluded_count') int excludedCount,
  });
}

/// @nodoc
class __$$RestaurantImplCopyWithImpl<$Res>
    extends _$RestaurantCopyWithImpl<$Res, _$RestaurantImpl>
    implements _$$RestaurantImplCopyWith<$Res> {
  __$$RestaurantImplCopyWithImpl(
    _$RestaurantImpl _value,
    $Res Function(_$RestaurantImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of Restaurant
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? restaurantId = freezed,
    Object? id = freezed,
    Object? googlePlaceId = freezed,
    Object? nameTh = null,
    Object? nameEn = freezed,
    Object? latitude = null,
    Object? longitude = null,
    Object? priceBand = freezed,
    Object? priceTier = freezed,
    Object? isHalalCertified = null,
    Object? hasParking = null,
    Object? distanceM = freezed,
    Object? rating = freezed,
    Object? photoUrl = freezed,
    Object? safetyTier = null,
    Object? needsAck = null,
    Object? ackReason = freezed,
    Object? safeDishes = null,
    Object? excludedCount = null,
  }) {
    return _then(
      _$RestaurantImpl(
        restaurantId: freezed == restaurantId
            ? _value.restaurantId
            : restaurantId // ignore: cast_nullable_to_non_nullable
                  as String?,
        id: freezed == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as String?,
        googlePlaceId: freezed == googlePlaceId
            ? _value.googlePlaceId
            : googlePlaceId // ignore: cast_nullable_to_non_nullable
                  as String?,
        nameTh: null == nameTh
            ? _value.nameTh
            : nameTh // ignore: cast_nullable_to_non_nullable
                  as String,
        nameEn: freezed == nameEn
            ? _value.nameEn
            : nameEn // ignore: cast_nullable_to_non_nullable
                  as String?,
        latitude: null == latitude
            ? _value.latitude
            : latitude // ignore: cast_nullable_to_non_nullable
                  as double,
        longitude: null == longitude
            ? _value.longitude
            : longitude // ignore: cast_nullable_to_non_nullable
                  as double,
        priceBand: freezed == priceBand
            ? _value.priceBand
            : priceBand // ignore: cast_nullable_to_non_nullable
                  as int?,
        priceTier: freezed == priceTier
            ? _value.priceTier
            : priceTier // ignore: cast_nullable_to_non_nullable
                  as String?,
        isHalalCertified: null == isHalalCertified
            ? _value.isHalalCertified
            : isHalalCertified // ignore: cast_nullable_to_non_nullable
                  as int,
        hasParking: null == hasParking
            ? _value.hasParking
            : hasParking // ignore: cast_nullable_to_non_nullable
                  as int,
        distanceM: freezed == distanceM
            ? _value.distanceM
            : distanceM // ignore: cast_nullable_to_non_nullable
                  as int?,
        rating: freezed == rating
            ? _value.rating
            : rating // ignore: cast_nullable_to_non_nullable
                  as double?,
        photoUrl: freezed == photoUrl
            ? _value.photoUrl
            : photoUrl // ignore: cast_nullable_to_non_nullable
                  as String?,
        safetyTier: null == safetyTier
            ? _value.safetyTier
            : safetyTier // ignore: cast_nullable_to_non_nullable
                  as String,
        needsAck: null == needsAck
            ? _value.needsAck
            : needsAck // ignore: cast_nullable_to_non_nullable
                  as bool,
        ackReason: freezed == ackReason
            ? _value.ackReason
            : ackReason // ignore: cast_nullable_to_non_nullable
                  as String?,
        safeDishes: null == safeDishes
            ? _value._safeDishes
            : safeDishes // ignore: cast_nullable_to_non_nullable
                  as List<Map<String, dynamic>>,
        excludedCount: null == excludedCount
            ? _value.excludedCount
            : excludedCount // ignore: cast_nullable_to_non_nullable
                  as int,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$RestaurantImpl implements _Restaurant {
  const _$RestaurantImpl({
    @JsonKey(name: 'restaurant_id') this.restaurantId,
    this.id,
    @JsonKey(name: 'google_place_id') this.googlePlaceId,
    @JsonKey(name: 'name_th') required this.nameTh,
    @JsonKey(name: 'name_en') this.nameEn,
    required this.latitude,
    required this.longitude,
    @JsonKey(name: 'price_band') this.priceBand,
    @JsonKey(name: 'price_tier') this.priceTier,
    @JsonKey(name: 'is_halal_certified') this.isHalalCertified = 0,
    @JsonKey(name: 'has_parking') this.hasParking = 2,
    @JsonKey(name: 'distance_m') this.distanceM,
    this.rating,
    @JsonKey(name: 'photo_url') this.photoUrl,
    @JsonKey(name: 'safety_tier') this.safetyTier = 'verified',
    @JsonKey(name: 'needs_ack') this.needsAck = false,
    @JsonKey(name: 'ack_reason') this.ackReason,
    @JsonKey(name: 'safe_dishes')
    final List<Map<String, dynamic>> safeDishes = const [],
    @JsonKey(name: 'excluded_count') this.excludedCount = 0,
  }) : _safeDishes = safeDishes;

  factory _$RestaurantImpl.fromJson(Map<String, dynamic> json) =>
      _$$RestaurantImplFromJson(json);

  // Handles both raw ingest "id" and contract "restaurant_id"
  @override
  @JsonKey(name: 'restaurant_id')
  final String? restaurantId;
  @override
  final String? id;
  @override
  @JsonKey(name: 'google_place_id')
  final String? googlePlaceId;
  @override
  @JsonKey(name: 'name_th')
  final String nameTh;
  @override
  @JsonKey(name: 'name_en')
  final String? nameEn;
  @override
  final double latitude;
  @override
  final double longitude;
  @override
  @JsonKey(name: 'price_band')
  final int? priceBand;
  @override
  @JsonKey(name: 'price_tier')
  final String? priceTier;
  @override
  @JsonKey(name: 'is_halal_certified')
  final int isHalalCertified;
  @override
  @JsonKey(name: 'has_parking')
  final int hasParking;
  // Recommendation Contract §3.1 Fields
  @override
  @JsonKey(name: 'distance_m')
  final int? distanceM;
  @override
  final double? rating;
  @override
  @JsonKey(name: 'photo_url')
  final String? photoUrl;
  @override
  @JsonKey(name: 'safety_tier')
  final String safetyTier;
  @override
  @JsonKey(name: 'needs_ack')
  final bool needsAck;
  @override
  @JsonKey(name: 'ack_reason')
  final String? ackReason;
  final List<Map<String, dynamic>> _safeDishes;
  @override
  @JsonKey(name: 'safe_dishes')
  List<Map<String, dynamic>> get safeDishes {
    if (_safeDishes is EqualUnmodifiableListView) return _safeDishes;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_safeDishes);
  }

  @override
  @JsonKey(name: 'excluded_count')
  final int excludedCount;

  @override
  String toString() {
    return 'Restaurant(restaurantId: $restaurantId, id: $id, googlePlaceId: $googlePlaceId, nameTh: $nameTh, nameEn: $nameEn, latitude: $latitude, longitude: $longitude, priceBand: $priceBand, priceTier: $priceTier, isHalalCertified: $isHalalCertified, hasParking: $hasParking, distanceM: $distanceM, rating: $rating, photoUrl: $photoUrl, safetyTier: $safetyTier, needsAck: $needsAck, ackReason: $ackReason, safeDishes: $safeDishes, excludedCount: $excludedCount)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RestaurantImpl &&
            (identical(other.restaurantId, restaurantId) ||
                other.restaurantId == restaurantId) &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.googlePlaceId, googlePlaceId) ||
                other.googlePlaceId == googlePlaceId) &&
            (identical(other.nameTh, nameTh) || other.nameTh == nameTh) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.latitude, latitude) ||
                other.latitude == latitude) &&
            (identical(other.longitude, longitude) ||
                other.longitude == longitude) &&
            (identical(other.priceBand, priceBand) ||
                other.priceBand == priceBand) &&
            (identical(other.priceTier, priceTier) ||
                other.priceTier == priceTier) &&
            (identical(other.isHalalCertified, isHalalCertified) ||
                other.isHalalCertified == isHalalCertified) &&
            (identical(other.hasParking, hasParking) ||
                other.hasParking == hasParking) &&
            (identical(other.distanceM, distanceM) ||
                other.distanceM == distanceM) &&
            (identical(other.rating, rating) || other.rating == rating) &&
            (identical(other.photoUrl, photoUrl) ||
                other.photoUrl == photoUrl) &&
            (identical(other.safetyTier, safetyTier) ||
                other.safetyTier == safetyTier) &&
            (identical(other.needsAck, needsAck) ||
                other.needsAck == needsAck) &&
            (identical(other.ackReason, ackReason) ||
                other.ackReason == ackReason) &&
            const DeepCollectionEquality().equals(
              other._safeDishes,
              _safeDishes,
            ) &&
            (identical(other.excludedCount, excludedCount) ||
                other.excludedCount == excludedCount));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hashAll([
    runtimeType,
    restaurantId,
    id,
    googlePlaceId,
    nameTh,
    nameEn,
    latitude,
    longitude,
    priceBand,
    priceTier,
    isHalalCertified,
    hasParking,
    distanceM,
    rating,
    photoUrl,
    safetyTier,
    needsAck,
    ackReason,
    const DeepCollectionEquality().hash(_safeDishes),
    excludedCount,
  ]);

  /// Create a copy of Restaurant
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RestaurantImplCopyWith<_$RestaurantImpl> get copyWith =>
      __$$RestaurantImplCopyWithImpl<_$RestaurantImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$RestaurantImplToJson(this);
  }
}

abstract class _Restaurant implements Restaurant {
  const factory _Restaurant({
    @JsonKey(name: 'restaurant_id') final String? restaurantId,
    final String? id,
    @JsonKey(name: 'google_place_id') final String? googlePlaceId,
    @JsonKey(name: 'name_th') required final String nameTh,
    @JsonKey(name: 'name_en') final String? nameEn,
    required final double latitude,
    required final double longitude,
    @JsonKey(name: 'price_band') final int? priceBand,
    @JsonKey(name: 'price_tier') final String? priceTier,
    @JsonKey(name: 'is_halal_certified') final int isHalalCertified,
    @JsonKey(name: 'has_parking') final int hasParking,
    @JsonKey(name: 'distance_m') final int? distanceM,
    final double? rating,
    @JsonKey(name: 'photo_url') final String? photoUrl,
    @JsonKey(name: 'safety_tier') final String safetyTier,
    @JsonKey(name: 'needs_ack') final bool needsAck,
    @JsonKey(name: 'ack_reason') final String? ackReason,
    @JsonKey(name: 'safe_dishes') final List<Map<String, dynamic>> safeDishes,
    @JsonKey(name: 'excluded_count') final int excludedCount,
  }) = _$RestaurantImpl;

  factory _Restaurant.fromJson(Map<String, dynamic> json) =
      _$RestaurantImpl.fromJson;

  // Handles both raw ingest "id" and contract "restaurant_id"
  @override
  @JsonKey(name: 'restaurant_id')
  String? get restaurantId;
  @override
  String? get id;
  @override
  @JsonKey(name: 'google_place_id')
  String? get googlePlaceId;
  @override
  @JsonKey(name: 'name_th')
  String get nameTh;
  @override
  @JsonKey(name: 'name_en')
  String? get nameEn;
  @override
  double get latitude;
  @override
  double get longitude;
  @override
  @JsonKey(name: 'price_band')
  int? get priceBand;
  @override
  @JsonKey(name: 'price_tier')
  String? get priceTier;
  @override
  @JsonKey(name: 'is_halal_certified')
  int get isHalalCertified;
  @override
  @JsonKey(name: 'has_parking')
  int get hasParking; // Recommendation Contract §3.1 Fields
  @override
  @JsonKey(name: 'distance_m')
  int? get distanceM;
  @override
  double? get rating;
  @override
  @JsonKey(name: 'photo_url')
  String? get photoUrl;
  @override
  @JsonKey(name: 'safety_tier')
  String get safetyTier;
  @override
  @JsonKey(name: 'needs_ack')
  bool get needsAck;
  @override
  @JsonKey(name: 'ack_reason')
  String? get ackReason;
  @override
  @JsonKey(name: 'safe_dishes')
  List<Map<String, dynamic>> get safeDishes;
  @override
  @JsonKey(name: 'excluded_count')
  int get excludedCount;

  /// Create a copy of Restaurant
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RestaurantImplCopyWith<_$RestaurantImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
