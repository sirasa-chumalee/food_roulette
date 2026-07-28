// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'menu_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$MenuItemImpl _$$MenuItemImplFromJson(Map<String, dynamic> json) =>
    _$MenuItemImpl(
      id: (json['id'] as num).toInt(),
      restaurantId: json['restaurant_id'] as String,
      nameTh: json['name_th'] as String,
      nameEn: json['name_en'] as String?,
      category: json['category'] as String?,
      priceThb: (json['price_thb'] as num).toDouble(),
      spicyLevel: (json['spicy_level'] as num?)?.toInt() ?? 0,
      confidence: json['confidence'] as String? ?? 'high',
      crustaceans: (json['crustaceans'] as num?)?.toInt() ?? 0,
      fish: (json['fish'] as num?)?.toInt() ?? 0,
      milk: (json['milk'] as num?)?.toInt() ?? 0,
      eggs: (json['eggs'] as num?)?.toInt() ?? 0,
      peanuts: (json['peanuts'] as num?)?.toInt() ?? 0,
      treeNuts: (json['tree_nuts'] as num?)?.toInt() ?? 0,
      wheat: (json['wheat'] as num?)?.toInt() ?? 0,
      soy: (json['soy'] as num?)?.toInt() ?? 0,
      sesame: (json['sesame'] as num?)?.toInt() ?? 0,
      molluscs: (json['molluscs'] as num?)?.toInt() ?? 0,
      containsMeat: (json['contains_meat'] as num?)?.toInt() ?? 0,
      containsPork: (json['contains_pork'] as num?)?.toInt() ?? 0,
      containsBeef: (json['contains_beef'] as num?)?.toInt() ?? 0,
      containsAlcohol: (json['contains_alcohol'] as num?)?.toInt() ?? 0,
      containsPungentVeg: (json['contains_pungent_veg'] as num?)?.toInt() ?? 0,
      isVegetarian: json['is_vegetarian'] as bool? ?? false,
      isVegan: json['is_vegan'] as bool? ?? false,
      isPescatarian: json['is_pescatarian'] as bool? ?? false,
      isJay: json['is_jay'] as bool? ?? false,
      safetyTier: json['safety_tier'] as String?,
    );

Map<String, dynamic> _$$MenuItemImplToJson(_$MenuItemImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'restaurant_id': instance.restaurantId,
      'name_th': instance.nameTh,
      'name_en': instance.nameEn,
      'category': instance.category,
      'price_thb': instance.priceThb,
      'spicy_level': instance.spicyLevel,
      'confidence': instance.confidence,
      'crustaceans': instance.crustaceans,
      'fish': instance.fish,
      'milk': instance.milk,
      'eggs': instance.eggs,
      'peanuts': instance.peanuts,
      'tree_nuts': instance.treeNuts,
      'wheat': instance.wheat,
      'soy': instance.soy,
      'sesame': instance.sesame,
      'molluscs': instance.molluscs,
      'contains_meat': instance.containsMeat,
      'contains_pork': instance.containsPork,
      'contains_beef': instance.containsBeef,
      'contains_alcohol': instance.containsAlcohol,
      'contains_pungent_veg': instance.containsPungentVeg,
      'is_vegetarian': instance.isVegetarian,
      'is_vegan': instance.isVegan,
      'is_pescatarian': instance.isPescatarian,
      'is_jay': instance.isJay,
      'safety_tier': instance.safetyTier,
    };
