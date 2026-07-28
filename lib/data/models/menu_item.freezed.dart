// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'menu_item.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

MenuItem _$MenuItemFromJson(Map<String, dynamic> json) {
  return _MenuItem.fromJson(json);
}

/// @nodoc
mixin _$MenuItem {
  int get id => throw _privateConstructorUsedError;
  @JsonKey(name: 'restaurant_id')
  String get restaurantId => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_th')
  String get nameTh => throw _privateConstructorUsedError;
  @JsonKey(name: 'name_en')
  String? get nameEn => throw _privateConstructorUsedError;
  String? get category => throw _privateConstructorUsedError;
  @JsonKey(name: 'price_thb')
  double get priceThb => throw _privateConstructorUsedError;
  @JsonKey(name: 'spicy_level')
  int get spicyLevel => throw _privateConstructorUsedError;
  String get confidence => throw _privateConstructorUsedError; // Allergen Flags
  int get crustaceans => throw _privateConstructorUsedError;
  int get fish => throw _privateConstructorUsedError;
  int get milk => throw _privateConstructorUsedError;
  int get eggs => throw _privateConstructorUsedError;
  int get peanuts => throw _privateConstructorUsedError;
  @JsonKey(name: 'tree_nuts')
  int get treeNuts => throw _privateConstructorUsedError;
  int get wheat => throw _privateConstructorUsedError;
  int get soy => throw _privateConstructorUsedError;
  int get sesame => throw _privateConstructorUsedError;
  int get molluscs => throw _privateConstructorUsedError; // Constraint Flags
  @JsonKey(name: 'contains_meat')
  int get containsMeat => throw _privateConstructorUsedError;
  @JsonKey(name: 'contains_pork')
  int get containsPork => throw _privateConstructorUsedError;
  @JsonKey(name: 'contains_beef')
  int get containsBeef => throw _privateConstructorUsedError;
  @JsonKey(name: 'contains_alcohol')
  int get containsAlcohol => throw _privateConstructorUsedError;
  @JsonKey(name: 'contains_pungent_veg')
  int get containsPungentVeg => throw _privateConstructorUsedError; // Pre-derived Diet Booleans
  @JsonKey(name: 'is_vegetarian')
  bool get isVegetarian => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_vegan')
  bool get isVegan => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_pescatarian')
  bool get isPescatarian => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_jay')
  bool get isJay => throw _privateConstructorUsedError; // Contract M1+ Safety Tier
  @JsonKey(name: 'safety_tier')
  String? get safetyTier => throw _privateConstructorUsedError;

  /// Serializes this MenuItem to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MenuItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MenuItemCopyWith<MenuItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MenuItemCopyWith<$Res> {
  factory $MenuItemCopyWith(MenuItem value, $Res Function(MenuItem) then) =
      _$MenuItemCopyWithImpl<$Res, MenuItem>;
  @useResult
  $Res call({
    int id,
    @JsonKey(name: 'restaurant_id') String restaurantId,
    @JsonKey(name: 'name_th') String nameTh,
    @JsonKey(name: 'name_en') String? nameEn,
    String? category,
    @JsonKey(name: 'price_thb') double priceThb,
    @JsonKey(name: 'spicy_level') int spicyLevel,
    String confidence,
    int crustaceans,
    int fish,
    int milk,
    int eggs,
    int peanuts,
    @JsonKey(name: 'tree_nuts') int treeNuts,
    int wheat,
    int soy,
    int sesame,
    int molluscs,
    @JsonKey(name: 'contains_meat') int containsMeat,
    @JsonKey(name: 'contains_pork') int containsPork,
    @JsonKey(name: 'contains_beef') int containsBeef,
    @JsonKey(name: 'contains_alcohol') int containsAlcohol,
    @JsonKey(name: 'contains_pungent_veg') int containsPungentVeg,
    @JsonKey(name: 'is_vegetarian') bool isVegetarian,
    @JsonKey(name: 'is_vegan') bool isVegan,
    @JsonKey(name: 'is_pescatarian') bool isPescatarian,
    @JsonKey(name: 'is_jay') bool isJay,
    @JsonKey(name: 'safety_tier') String? safetyTier,
  });
}

/// @nodoc
class _$MenuItemCopyWithImpl<$Res, $Val extends MenuItem>
    implements $MenuItemCopyWith<$Res> {
  _$MenuItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MenuItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? restaurantId = null,
    Object? nameTh = null,
    Object? nameEn = freezed,
    Object? category = freezed,
    Object? priceThb = null,
    Object? spicyLevel = null,
    Object? confidence = null,
    Object? crustaceans = null,
    Object? fish = null,
    Object? milk = null,
    Object? eggs = null,
    Object? peanuts = null,
    Object? treeNuts = null,
    Object? wheat = null,
    Object? soy = null,
    Object? sesame = null,
    Object? molluscs = null,
    Object? containsMeat = null,
    Object? containsPork = null,
    Object? containsBeef = null,
    Object? containsAlcohol = null,
    Object? containsPungentVeg = null,
    Object? isVegetarian = null,
    Object? isVegan = null,
    Object? isPescatarian = null,
    Object? isJay = null,
    Object? safetyTier = freezed,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as int,
            restaurantId: null == restaurantId
                ? _value.restaurantId
                : restaurantId // ignore: cast_nullable_to_non_nullable
                      as String,
            nameTh: null == nameTh
                ? _value.nameTh
                : nameTh // ignore: cast_nullable_to_non_nullable
                      as String,
            nameEn: freezed == nameEn
                ? _value.nameEn
                : nameEn // ignore: cast_nullable_to_non_nullable
                      as String?,
            category: freezed == category
                ? _value.category
                : category // ignore: cast_nullable_to_non_nullable
                      as String?,
            priceThb: null == priceThb
                ? _value.priceThb
                : priceThb // ignore: cast_nullable_to_non_nullable
                      as double,
            spicyLevel: null == spicyLevel
                ? _value.spicyLevel
                : spicyLevel // ignore: cast_nullable_to_non_nullable
                      as int,
            confidence: null == confidence
                ? _value.confidence
                : confidence // ignore: cast_nullable_to_non_nullable
                      as String,
            crustaceans: null == crustaceans
                ? _value.crustaceans
                : crustaceans // ignore: cast_nullable_to_non_nullable
                      as int,
            fish: null == fish
                ? _value.fish
                : fish // ignore: cast_nullable_to_non_nullable
                      as int,
            milk: null == milk
                ? _value.milk
                : milk // ignore: cast_nullable_to_non_nullable
                      as int,
            eggs: null == eggs
                ? _value.eggs
                : eggs // ignore: cast_nullable_to_non_nullable
                      as int,
            peanuts: null == peanuts
                ? _value.peanuts
                : peanuts // ignore: cast_nullable_to_non_nullable
                      as int,
            treeNuts: null == treeNuts
                ? _value.treeNuts
                : treeNuts // ignore: cast_nullable_to_non_nullable
                      as int,
            wheat: null == wheat
                ? _value.wheat
                : wheat // ignore: cast_nullable_to_non_nullable
                      as int,
            soy: null == soy
                ? _value.soy
                : soy // ignore: cast_nullable_to_non_nullable
                      as int,
            sesame: null == sesame
                ? _value.sesame
                : sesame // ignore: cast_nullable_to_non_nullable
                      as int,
            molluscs: null == molluscs
                ? _value.molluscs
                : molluscs // ignore: cast_nullable_to_non_nullable
                      as int,
            containsMeat: null == containsMeat
                ? _value.containsMeat
                : containsMeat // ignore: cast_nullable_to_non_nullable
                      as int,
            containsPork: null == containsPork
                ? _value.containsPork
                : containsPork // ignore: cast_nullable_to_non_nullable
                      as int,
            containsBeef: null == containsBeef
                ? _value.containsBeef
                : containsBeef // ignore: cast_nullable_to_non_nullable
                      as int,
            containsAlcohol: null == containsAlcohol
                ? _value.containsAlcohol
                : containsAlcohol // ignore: cast_nullable_to_non_nullable
                      as int,
            containsPungentVeg: null == containsPungentVeg
                ? _value.containsPungentVeg
                : containsPungentVeg // ignore: cast_nullable_to_non_nullable
                      as int,
            isVegetarian: null == isVegetarian
                ? _value.isVegetarian
                : isVegetarian // ignore: cast_nullable_to_non_nullable
                      as bool,
            isVegan: null == isVegan
                ? _value.isVegan
                : isVegan // ignore: cast_nullable_to_non_nullable
                      as bool,
            isPescatarian: null == isPescatarian
                ? _value.isPescatarian
                : isPescatarian // ignore: cast_nullable_to_non_nullable
                      as bool,
            isJay: null == isJay
                ? _value.isJay
                : isJay // ignore: cast_nullable_to_non_nullable
                      as bool,
            safetyTier: freezed == safetyTier
                ? _value.safetyTier
                : safetyTier // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$MenuItemImplCopyWith<$Res>
    implements $MenuItemCopyWith<$Res> {
  factory _$$MenuItemImplCopyWith(
    _$MenuItemImpl value,
    $Res Function(_$MenuItemImpl) then,
  ) = __$$MenuItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    int id,
    @JsonKey(name: 'restaurant_id') String restaurantId,
    @JsonKey(name: 'name_th') String nameTh,
    @JsonKey(name: 'name_en') String? nameEn,
    String? category,
    @JsonKey(name: 'price_thb') double priceThb,
    @JsonKey(name: 'spicy_level') int spicyLevel,
    String confidence,
    int crustaceans,
    int fish,
    int milk,
    int eggs,
    int peanuts,
    @JsonKey(name: 'tree_nuts') int treeNuts,
    int wheat,
    int soy,
    int sesame,
    int molluscs,
    @JsonKey(name: 'contains_meat') int containsMeat,
    @JsonKey(name: 'contains_pork') int containsPork,
    @JsonKey(name: 'contains_beef') int containsBeef,
    @JsonKey(name: 'contains_alcohol') int containsAlcohol,
    @JsonKey(name: 'contains_pungent_veg') int containsPungentVeg,
    @JsonKey(name: 'is_vegetarian') bool isVegetarian,
    @JsonKey(name: 'is_vegan') bool isVegan,
    @JsonKey(name: 'is_pescatarian') bool isPescatarian,
    @JsonKey(name: 'is_jay') bool isJay,
    @JsonKey(name: 'safety_tier') String? safetyTier,
  });
}

/// @nodoc
class __$$MenuItemImplCopyWithImpl<$Res>
    extends _$MenuItemCopyWithImpl<$Res, _$MenuItemImpl>
    implements _$$MenuItemImplCopyWith<$Res> {
  __$$MenuItemImplCopyWithImpl(
    _$MenuItemImpl _value,
    $Res Function(_$MenuItemImpl) _then,
  ) : super(_value, _then);

  /// Create a copy of MenuItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? restaurantId = null,
    Object? nameTh = null,
    Object? nameEn = freezed,
    Object? category = freezed,
    Object? priceThb = null,
    Object? spicyLevel = null,
    Object? confidence = null,
    Object? crustaceans = null,
    Object? fish = null,
    Object? milk = null,
    Object? eggs = null,
    Object? peanuts = null,
    Object? treeNuts = null,
    Object? wheat = null,
    Object? soy = null,
    Object? sesame = null,
    Object? molluscs = null,
    Object? containsMeat = null,
    Object? containsPork = null,
    Object? containsBeef = null,
    Object? containsAlcohol = null,
    Object? containsPungentVeg = null,
    Object? isVegetarian = null,
    Object? isVegan = null,
    Object? isPescatarian = null,
    Object? isJay = null,
    Object? safetyTier = freezed,
  }) {
    return _then(
      _$MenuItemImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as int,
        restaurantId: null == restaurantId
            ? _value.restaurantId
            : restaurantId // ignore: cast_nullable_to_non_nullable
                  as String,
        nameTh: null == nameTh
            ? _value.nameTh
            : nameTh // ignore: cast_nullable_to_non_nullable
                  as String,
        nameEn: freezed == nameEn
            ? _value.nameEn
            : nameEn // ignore: cast_nullable_to_non_nullable
                  as String?,
        category: freezed == category
            ? _value.category
            : category // ignore: cast_nullable_to_non_nullable
                  as String?,
        priceThb: null == priceThb
            ? _value.priceThb
            : priceThb // ignore: cast_nullable_to_non_nullable
                  as double,
        spicyLevel: null == spicyLevel
            ? _value.spicyLevel
            : spicyLevel // ignore: cast_nullable_to_non_nullable
                  as int,
        confidence: null == confidence
            ? _value.confidence
            : confidence // ignore: cast_nullable_to_non_nullable
                  as String,
        crustaceans: null == crustaceans
            ? _value.crustaceans
            : crustaceans // ignore: cast_nullable_to_non_nullable
                  as int,
        fish: null == fish
            ? _value.fish
            : fish // ignore: cast_nullable_to_non_nullable
                  as int,
        milk: null == milk
            ? _value.milk
            : milk // ignore: cast_nullable_to_non_nullable
                  as int,
        eggs: null == eggs
            ? _value.eggs
            : eggs // ignore: cast_nullable_to_non_nullable
                  as int,
        peanuts: null == peanuts
            ? _value.peanuts
            : peanuts // ignore: cast_nullable_to_non_nullable
                  as int,
        treeNuts: null == treeNuts
            ? _value.treeNuts
            : treeNuts // ignore: cast_nullable_to_non_nullable
                  as int,
        wheat: null == wheat
            ? _value.wheat
            : wheat // ignore: cast_nullable_to_non_nullable
                  as int,
        soy: null == soy
            ? _value.soy
            : soy // ignore: cast_nullable_to_non_nullable
                  as int,
        sesame: null == sesame
            ? _value.sesame
            : sesame // ignore: cast_nullable_to_non_nullable
                  as int,
        molluscs: null == molluscs
            ? _value.molluscs
            : molluscs // ignore: cast_nullable_to_non_nullable
                  as int,
        containsMeat: null == containsMeat
            ? _value.containsMeat
            : containsMeat // ignore: cast_nullable_to_non_nullable
                  as int,
        containsPork: null == containsPork
            ? _value.containsPork
            : containsPork // ignore: cast_nullable_to_non_nullable
                  as int,
        containsBeef: null == containsBeef
            ? _value.containsBeef
            : containsBeef // ignore: cast_nullable_to_non_nullable
                  as int,
        containsAlcohol: null == containsAlcohol
            ? _value.containsAlcohol
            : containsAlcohol // ignore: cast_nullable_to_non_nullable
                  as int,
        containsPungentVeg: null == containsPungentVeg
            ? _value.containsPungentVeg
            : containsPungentVeg // ignore: cast_nullable_to_non_nullable
                  as int,
        isVegetarian: null == isVegetarian
            ? _value.isVegetarian
            : isVegetarian // ignore: cast_nullable_to_non_nullable
                  as bool,
        isVegan: null == isVegan
            ? _value.isVegan
            : isVegan // ignore: cast_nullable_to_non_nullable
                  as bool,
        isPescatarian: null == isPescatarian
            ? _value.isPescatarian
            : isPescatarian // ignore: cast_nullable_to_non_nullable
                  as bool,
        isJay: null == isJay
            ? _value.isJay
            : isJay // ignore: cast_nullable_to_non_nullable
                  as bool,
        safetyTier: freezed == safetyTier
            ? _value.safetyTier
            : safetyTier // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc
@JsonSerializable()
class _$MenuItemImpl implements _MenuItem {
  const _$MenuItemImpl({
    required this.id,
    @JsonKey(name: 'restaurant_id') required this.restaurantId,
    @JsonKey(name: 'name_th') required this.nameTh,
    @JsonKey(name: 'name_en') this.nameEn,
    this.category,
    @JsonKey(name: 'price_thb') required this.priceThb,
    @JsonKey(name: 'spicy_level') this.spicyLevel = 0,
    this.confidence = 'high',
    this.crustaceans = 0,
    this.fish = 0,
    this.milk = 0,
    this.eggs = 0,
    this.peanuts = 0,
    @JsonKey(name: 'tree_nuts') this.treeNuts = 0,
    this.wheat = 0,
    this.soy = 0,
    this.sesame = 0,
    this.molluscs = 0,
    @JsonKey(name: 'contains_meat') this.containsMeat = 0,
    @JsonKey(name: 'contains_pork') this.containsPork = 0,
    @JsonKey(name: 'contains_beef') this.containsBeef = 0,
    @JsonKey(name: 'contains_alcohol') this.containsAlcohol = 0,
    @JsonKey(name: 'contains_pungent_veg') this.containsPungentVeg = 0,
    @JsonKey(name: 'is_vegetarian') this.isVegetarian = false,
    @JsonKey(name: 'is_vegan') this.isVegan = false,
    @JsonKey(name: 'is_pescatarian') this.isPescatarian = false,
    @JsonKey(name: 'is_jay') this.isJay = false,
    @JsonKey(name: 'safety_tier') this.safetyTier,
  });

  factory _$MenuItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$MenuItemImplFromJson(json);

  @override
  final int id;
  @override
  @JsonKey(name: 'restaurant_id')
  final String restaurantId;
  @override
  @JsonKey(name: 'name_th')
  final String nameTh;
  @override
  @JsonKey(name: 'name_en')
  final String? nameEn;
  @override
  final String? category;
  @override
  @JsonKey(name: 'price_thb')
  final double priceThb;
  @override
  @JsonKey(name: 'spicy_level')
  final int spicyLevel;
  @override
  @JsonKey()
  final String confidence;
  // Allergen Flags
  @override
  @JsonKey()
  final int crustaceans;
  @override
  @JsonKey()
  final int fish;
  @override
  @JsonKey()
  final int milk;
  @override
  @JsonKey()
  final int eggs;
  @override
  @JsonKey()
  final int peanuts;
  @override
  @JsonKey(name: 'tree_nuts')
  final int treeNuts;
  @override
  @JsonKey()
  final int wheat;
  @override
  @JsonKey()
  final int soy;
  @override
  @JsonKey()
  final int sesame;
  @override
  @JsonKey()
  final int molluscs;
  // Constraint Flags
  @override
  @JsonKey(name: 'contains_meat')
  final int containsMeat;
  @override
  @JsonKey(name: 'contains_pork')
  final int containsPork;
  @override
  @JsonKey(name: 'contains_beef')
  final int containsBeef;
  @override
  @JsonKey(name: 'contains_alcohol')
  final int containsAlcohol;
  @override
  @JsonKey(name: 'contains_pungent_veg')
  final int containsPungentVeg;
  // Pre-derived Diet Booleans
  @override
  @JsonKey(name: 'is_vegetarian')
  final bool isVegetarian;
  @override
  @JsonKey(name: 'is_vegan')
  final bool isVegan;
  @override
  @JsonKey(name: 'is_pescatarian')
  final bool isPescatarian;
  @override
  @JsonKey(name: 'is_jay')
  final bool isJay;
  // Contract M1+ Safety Tier
  @override
  @JsonKey(name: 'safety_tier')
  final String? safetyTier;

  @override
  String toString() {
    return 'MenuItem(id: $id, restaurantId: $restaurantId, nameTh: $nameTh, nameEn: $nameEn, category: $category, priceThb: $priceThb, spicyLevel: $spicyLevel, confidence: $confidence, crustaceans: $crustaceans, fish: $fish, milk: $milk, eggs: $eggs, peanuts: $peanuts, treeNuts: $treeNuts, wheat: $wheat, soy: $soy, sesame: $sesame, molluscs: $molluscs, containsMeat: $containsMeat, containsPork: $containsPork, containsBeef: $containsBeef, containsAlcohol: $containsAlcohol, containsPungentVeg: $containsPungentVeg, isVegetarian: $isVegetarian, isVegan: $isVegan, isPescatarian: $isPescatarian, isJay: $isJay, safetyTier: $safetyTier)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MenuItemImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.restaurantId, restaurantId) ||
                other.restaurantId == restaurantId) &&
            (identical(other.nameTh, nameTh) || other.nameTh == nameTh) &&
            (identical(other.nameEn, nameEn) || other.nameEn == nameEn) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.priceThb, priceThb) ||
                other.priceThb == priceThb) &&
            (identical(other.spicyLevel, spicyLevel) ||
                other.spicyLevel == spicyLevel) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            (identical(other.crustaceans, crustaceans) ||
                other.crustaceans == crustaceans) &&
            (identical(other.fish, fish) || other.fish == fish) &&
            (identical(other.milk, milk) || other.milk == milk) &&
            (identical(other.eggs, eggs) || other.eggs == eggs) &&
            (identical(other.peanuts, peanuts) || other.peanuts == peanuts) &&
            (identical(other.treeNuts, treeNuts) ||
                other.treeNuts == treeNuts) &&
            (identical(other.wheat, wheat) || other.wheat == wheat) &&
            (identical(other.soy, soy) || other.soy == soy) &&
            (identical(other.sesame, sesame) || other.sesame == sesame) &&
            (identical(other.molluscs, molluscs) ||
                other.molluscs == molluscs) &&
            (identical(other.containsMeat, containsMeat) ||
                other.containsMeat == containsMeat) &&
            (identical(other.containsPork, containsPork) ||
                other.containsPork == containsPork) &&
            (identical(other.containsBeef, containsBeef) ||
                other.containsBeef == containsBeef) &&
            (identical(other.containsAlcohol, containsAlcohol) ||
                other.containsAlcohol == containsAlcohol) &&
            (identical(other.containsPungentVeg, containsPungentVeg) ||
                other.containsPungentVeg == containsPungentVeg) &&
            (identical(other.isVegetarian, isVegetarian) ||
                other.isVegetarian == isVegetarian) &&
            (identical(other.isVegan, isVegan) || other.isVegan == isVegan) &&
            (identical(other.isPescatarian, isPescatarian) ||
                other.isPescatarian == isPescatarian) &&
            (identical(other.isJay, isJay) || other.isJay == isJay) &&
            (identical(other.safetyTier, safetyTier) ||
                other.safetyTier == safetyTier));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hashAll([
    runtimeType,
    id,
    restaurantId,
    nameTh,
    nameEn,
    category,
    priceThb,
    spicyLevel,
    confidence,
    crustaceans,
    fish,
    milk,
    eggs,
    peanuts,
    treeNuts,
    wheat,
    soy,
    sesame,
    molluscs,
    containsMeat,
    containsPork,
    containsBeef,
    containsAlcohol,
    containsPungentVeg,
    isVegetarian,
    isVegan,
    isPescatarian,
    isJay,
    safetyTier,
  ]);

  /// Create a copy of MenuItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MenuItemImplCopyWith<_$MenuItemImpl> get copyWith =>
      __$$MenuItemImplCopyWithImpl<_$MenuItemImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MenuItemImplToJson(this);
  }
}

abstract class _MenuItem implements MenuItem {
  const factory _MenuItem({
    required final int id,
    @JsonKey(name: 'restaurant_id') required final String restaurantId,
    @JsonKey(name: 'name_th') required final String nameTh,
    @JsonKey(name: 'name_en') final String? nameEn,
    final String? category,
    @JsonKey(name: 'price_thb') required final double priceThb,
    @JsonKey(name: 'spicy_level') final int spicyLevel,
    final String confidence,
    final int crustaceans,
    final int fish,
    final int milk,
    final int eggs,
    final int peanuts,
    @JsonKey(name: 'tree_nuts') final int treeNuts,
    final int wheat,
    final int soy,
    final int sesame,
    final int molluscs,
    @JsonKey(name: 'contains_meat') final int containsMeat,
    @JsonKey(name: 'contains_pork') final int containsPork,
    @JsonKey(name: 'contains_beef') final int containsBeef,
    @JsonKey(name: 'contains_alcohol') final int containsAlcohol,
    @JsonKey(name: 'contains_pungent_veg') final int containsPungentVeg,
    @JsonKey(name: 'is_vegetarian') final bool isVegetarian,
    @JsonKey(name: 'is_vegan') final bool isVegan,
    @JsonKey(name: 'is_pescatarian') final bool isPescatarian,
    @JsonKey(name: 'is_jay') final bool isJay,
    @JsonKey(name: 'safety_tier') final String? safetyTier,
  }) = _$MenuItemImpl;

  factory _MenuItem.fromJson(Map<String, dynamic> json) =
      _$MenuItemImpl.fromJson;

  @override
  int get id;
  @override
  @JsonKey(name: 'restaurant_id')
  String get restaurantId;
  @override
  @JsonKey(name: 'name_th')
  String get nameTh;
  @override
  @JsonKey(name: 'name_en')
  String? get nameEn;
  @override
  String? get category;
  @override
  @JsonKey(name: 'price_thb')
  double get priceThb;
  @override
  @JsonKey(name: 'spicy_level')
  int get spicyLevel;
  @override
  String get confidence; // Allergen Flags
  @override
  int get crustaceans;
  @override
  int get fish;
  @override
  int get milk;
  @override
  int get eggs;
  @override
  int get peanuts;
  @override
  @JsonKey(name: 'tree_nuts')
  int get treeNuts;
  @override
  int get wheat;
  @override
  int get soy;
  @override
  int get sesame;
  @override
  int get molluscs; // Constraint Flags
  @override
  @JsonKey(name: 'contains_meat')
  int get containsMeat;
  @override
  @JsonKey(name: 'contains_pork')
  int get containsPork;
  @override
  @JsonKey(name: 'contains_beef')
  int get containsBeef;
  @override
  @JsonKey(name: 'contains_alcohol')
  int get containsAlcohol;
  @override
  @JsonKey(name: 'contains_pungent_veg')
  int get containsPungentVeg; // Pre-derived Diet Booleans
  @override
  @JsonKey(name: 'is_vegetarian')
  bool get isVegetarian;
  @override
  @JsonKey(name: 'is_vegan')
  bool get isVegan;
  @override
  @JsonKey(name: 'is_pescatarian')
  bool get isPescatarian;
  @override
  @JsonKey(name: 'is_jay')
  bool get isJay; // Contract M1+ Safety Tier
  @override
  @JsonKey(name: 'safety_tier')
  String? get safetyTier;

  /// Create a copy of MenuItem
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MenuItemImplCopyWith<_$MenuItemImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
