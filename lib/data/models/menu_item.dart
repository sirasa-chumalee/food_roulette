import 'package:freezed_annotation/freezed_annotation.dart';

part 'menu_item.freezed.dart';
part 'menu_item.g.dart';

@freezed
class MenuItem with _$MenuItem {
  const factory MenuItem({
    required int id,
    @JsonKey(name: 'restaurant_id') required String restaurantId,
    @JsonKey(name: 'name_th') required String nameTh,
    @JsonKey(name: 'name_en') String? nameEn,
    String? category,
    @JsonKey(name: 'price_thb') required double priceThb,
    @JsonKey(name: 'spicy_level') @Default(0) int spicyLevel,
    @Default('high') String confidence,

    // Allergen Flags
    @Default(0) int crustaceans,
    @Default(0) int fish,
    @Default(0) int milk,
    @Default(0) int eggs,
    @Default(0) int peanuts,
    @JsonKey(name: 'tree_nuts') @Default(0) int treeNuts,
    @Default(0) int wheat,
    @Default(0) int soy,
    @Default(0) int sesame,
    @Default(0) int molluscs,

    // Constraint Flags
    @JsonKey(name: 'contains_meat') @Default(0) int containsMeat,
    @JsonKey(name: 'contains_pork') @Default(0) int containsPork,
    @JsonKey(name: 'contains_beef') @Default(0) int containsBeef,
    @JsonKey(name: 'contains_alcohol') @Default(0) int containsAlcohol,
    @JsonKey(name: 'contains_pungent_veg') @Default(0) int containsPungentVeg,

    // Pre-derived Diet Booleans
    @JsonKey(name: 'is_vegetarian') @Default(false) bool isVegetarian,
    @JsonKey(name: 'is_vegan') @Default(false) bool isVegan,
    @JsonKey(name: 'is_pescatarian') @Default(false) bool isPescatarian,
    @JsonKey(name: 'is_jay') @Default(false) bool isJay,

    // Contract M1+ Safety Tier
    @JsonKey(name: 'safety_tier') String? safetyTier,
  }) = _MenuItem;

  factory MenuItem.fromJson(Map<String, dynamic> json) => _$MenuItemFromJson(json);
}

extension MenuItemX on MenuItem {
  String get effectiveSafetyTier => safetyTier ?? (confidence == 'high' ? 'verified' : 'unverified');

  List<String> get activeAllergens {
    final list = <String>[];
    if (crustaceans == 1) list.add('Crustaceans');
    if (fish == 1) list.add('Fish');
    if (milk == 1) list.add('Milk');
    if (eggs == 1) list.add('Eggs');
    if (peanuts == 1) list.add('Peanuts');
    if (treeNuts == 1) list.add('Tree Nuts');
    if (wheat == 1) list.add('Wheat');
    if (soy == 1) list.add('Soy');
    if (sesame == 1) list.add('Sesame');
    if (molluscs == 1) list.add('Molluscs');
    return list;
  }
}