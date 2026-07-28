class HardConstraints {
  final List<String> allergens;
  final bool halal;
  final bool noBeef;
  final bool vegetarian;
  final bool vegan;
  final bool jain;
  final bool jay;
  final bool celiac;

  HardConstraints({
    this.allergens = const [],
    this.halal = false,
    this.noBeef = false,
    this.vegetarian = false,
    this.vegan = false,
    this.jain = false,
    this.jay = false,
    this.celiac = false,
  });

  Map<String, dynamic> toJson() => {
        'allergens': allergens,
        'halal': halal,
        'no_beef': noBeef,
        'vegetarian': vegetarian,
        'vegan': vegan,
        'jain': jain,
        'jay': jay,
        'celiac': celiac,
      };

  factory HardConstraints.fromJson(Map<String, dynamic> json) {
    return HardConstraints(
      allergens: List<String>.from(json['allergens'] ?? []),
      halal: json['halal'] ?? false,
      noBeef: json['no_beef'] ?? false,
      vegetarian: json['vegetarian'] ?? false,
      vegan: json['vegan'] ?? false,
      jain: json['jain'] ?? false,
      jay: json['jay'] ?? false,
      celiac: json['celiac'] ?? false,
    );
  }

  HardConstraints copyWith({
    List<String>? allergens,
    bool? halal,
    bool? noBeef,
    bool? vegetarian,
    bool? vegan,
    bool? jain,
    bool? jay,
    bool? celiac,
  }) {
    return HardConstraints(
      allergens: allergens ?? this.allergens,
      halal: halal ?? this.halal,
      noBeef: noBeef ?? this.noBeef,
      vegetarian: vegetarian ?? this.vegetarian,
      vegan: vegan ?? this.vegan,
      jain: jain ?? this.jain,
      jay: jay ?? this.jay,
      celiac: celiac ?? this.celiac,
    );
  }
}

class SoftPreferences {
  final int spicyTolerance;
  final String? priceTier;
  final String dietStyle;
  final bool wantsParking;

  SoftPreferences({
    this.spicyTolerance = 3,
    this.priceTier,
    this.dietStyle = 'none',
    this.wantsParking = false,
  });

  Map<String, dynamic> toJson() => {
        'spicy_tolerance': spicyTolerance,
        'price_tier': priceTier,
        'diet_style': dietStyle,
        'wants_parking': wantsParking,
      };

  factory SoftPreferences.fromJson(Map<String, dynamic> json) {
    return SoftPreferences(
      spicyTolerance: json['spicy_tolerance'] ?? 3,
      priceTier: json['price_tier'],
      dietStyle: json['diet_style'] ?? 'none',
      wantsParking: json['wants_parking'] ?? false,
    );
  }

  SoftPreferences copyWith({
    int? spicyTolerance,
    String? priceTier,
    String? dietStyle,
    bool? wantsParking,
  }) {
    return SoftPreferences(
      spicyTolerance: spicyTolerance ?? this.spicyTolerance,
      priceTier: priceTier ?? this.priceTier,
      dietStyle: dietStyle ?? this.dietStyle,
      wantsParking: wantsParking ?? this.wantsParking,
    );
  }
}

class UserPreferences {
  final HardConstraints hard;
  final SoftPreferences soft;

  UserPreferences({
    HardConstraints? hard,
    SoftPreferences? soft,
  })  : hard = hard ?? HardConstraints(),
        soft = soft ?? SoftPreferences();

  Map<String, dynamic> toJson() => {
        'hard': hard.toJson(),
        'soft': soft.toJson(),
      };

  factory UserPreferences.fromJson(Map<String, dynamic> json) {
    return UserPreferences(
      hard: HardConstraints.fromJson(json['hard'] ?? {}),
      soft: SoftPreferences.fromJson(json['soft'] ?? {}),
    );
  }
}