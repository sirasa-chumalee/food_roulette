import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../../../data/models/history.dart';

const String baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

/// Model holding both history record and resolved display name
class HistoryDisplayItem {
  final String restaurantId;
  final String restaurantName;
  final String ts;

  const HistoryDisplayItem({
    required this.restaurantId,
    required this.restaurantName,
    required this.ts,
  });
}

final historyListProvider =
    FutureProvider.autoDispose<List<HistoryDisplayItem>>((ref) async {
  try {
    // 1. Fetch History
    final historyResponse =
        await http.get(Uri.parse('$baseUrl/history?user_id=1&limit=50'));
    // 2. Fetch Restaurants for Name Lookup
    final restaurantsResponse =
        await http.get(Uri.parse('$baseUrl/restaurants'));

    if (historyResponse.statusCode == 200) {
      final historyData = jsonDecode(historyResponse.body);
      final rawEvents = (historyData['history'] as List? ?? [])
          .map((e) => HistoryEventOut.fromJson(e))
          .where((e) => e.actionType == HistoryActionType.click)
          .toList();

      // Build ID -> Name lookup map
      final nameMap = <String, String>{};
      if (restaurantsResponse.statusCode == 200) {
        final List restaurantsList = jsonDecode(restaurantsResponse.body);
        for (final r in restaurantsList) {
          final id = r['id']?.toString() ?? '';
          final name = r['name_th']?.toString() ??
              r['name_en']?.toString() ??
              id;
          nameMap[id] = name;
        }
      }

      // Deduplicate: Keep only the most recent visit per restaurant
      final seenIds = <String>{};
      final uniqueItems = <HistoryDisplayItem>[];

      for (final event in rawEvents) {
        if (!seenIds.contains(event.restaurantId)) {
          seenIds.add(event.restaurantId);
          
          final resolvedName = (event.context != null &&
                  event.context!['name'] != null &&
                  event.context!['name'].toString().isNotEmpty)
              ? event.context!['name'].toString()
              : (nameMap[event.restaurantId] ?? event.restaurantId);

          uniqueItems.add(
            HistoryDisplayItem(
              restaurantId: event.restaurantId,
              restaurantName: resolvedName,
              ts: event.ts,
            ),
          );
        }
        if (uniqueItems.length >= 20) break;
      }

      return uniqueItems;
    }
  } catch (_) {}
  return [];
});