enum HistoryActionType {
  impression('IMPRESSION'),
  click('CLICK'),
  spin('SPIN'),
  rejection('REJECTION');

  final String value;
  const HistoryActionType(this.value);

  static HistoryActionType fromString(String val) {
    return HistoryActionType.values.firstWhere(
      (e) => e.value == val,
      orElse: () => HistoryActionType.impression,
    );
  }
}

class HistoryEvent {
  final String sessionId;
  final String restaurantId;
  final HistoryActionType actionType;
  final Map<String, dynamic>? context;

  const HistoryEvent({
    required this.sessionId,
    required this.restaurantId,
    required this.actionType,
    this.context,
  });

  Map<String, dynamic> toJson() => {
        'session_id': sessionId,
        'restaurant_id': restaurantId,
        'action_type': actionType.value,
        if (context != null) 'context': context,
      };
}

class HistoryEventOut {
  final int id;
  final String sessionId;
  final String userId;
  final String restaurantId;
  final HistoryActionType actionType;
  final String ts;
  final Map<String, dynamic>? context;

  const HistoryEventOut({
    required this.id,
    required this.sessionId,
    required this.userId,
    required this.restaurantId,
    required this.actionType,
    required this.ts,
    this.context,
  });

  factory HistoryEventOut.fromJson(Map<String, dynamic> json) {
    return HistoryEventOut(
      id: json['id'] ?? 0,
      sessionId: json['session_id'] ?? '',
      userId: json['user_id'] ?? '',
      restaurantId: json['restaurant_id'] ?? '',
      actionType: HistoryActionType.fromString(json['action_type'] ?? 'IMPRESSION'),
      ts: json['ts'] ?? '',
      context: json['context'] as Map<String, dynamic>?,
    );
  }
}

class HistoryStatsTotals {
  final int impressions;
  final int clicks;
  final int rejections;
  final int spins;

  const HistoryStatsTotals({
    required this.impressions,
    required this.clicks,
    required this.rejections,
    required this.spins,
  });

  factory HistoryStatsTotals.fromJson(Map<String, dynamic> json) {
    return HistoryStatsTotals(
      impressions: json['impressions'] ?? 0,
      clicks: json['clicks'] ?? 0,
      rejections: json['rejections'] ?? 0,
      spins: json['spins'] ?? 0,
    );
  }
}

class HistoryRestaurantStats {
  final String restaurantId;
  final int impressions;
  final int clicks;
  final int rejections;
  final int spins;
  final double clickThroughRate;

  const HistoryRestaurantStats({
    required this.restaurantId,
    required this.impressions,
    required this.clicks,
    required this.rejections,
    required this.spins,
    required this.clickThroughRate,
  });

  factory HistoryRestaurantStats.fromJson(Map<String, dynamic> json) {
    return HistoryRestaurantStats(
      restaurantId: json['restaurant_id'] ?? '',
      impressions: json['impressions'] ?? 0,
      clicks: json['clicks'] ?? 0,
      rejections: json['rejections'] ?? 0,
      spins: json['spins'] ?? 0,
      clickThroughRate: (json['click_through_rate'] ?? 0.0).toDouble(),
    );
  }
}

class HistoryStatsOut {
  final String userId;
  final HistoryStatsTotals totals;
  final double clickThroughRate;
  final List<HistoryRestaurantStats> restaurants;

  const HistoryStatsOut({
    required this.userId,
    required this.totals,
    required this.clickThroughRate,
    required this.restaurants,
  });

  factory HistoryStatsOut.fromJson(Map<String, dynamic> json) {
    return HistoryStatsOut(
      userId: json['user_id'] ?? '',
      totals: HistoryStatsTotals.fromJson(json['totals'] ?? {}),
      clickThroughRate: (json['click_through_rate'] ?? 0.0).toDouble(),
      restaurants: (json['restaurants'] as List? ?? [])
          .map((r) => HistoryRestaurantStats.fromJson(r))
          .toList(),
    );
  }
}