import 'dart:async';
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../../../data/models/history.dart';
import '../../auth/auth_provider.dart';

class HistoryBuffer {
  static const int batchThreshold = 5;
  static const Duration flushInterval = Duration(seconds: 3);
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  final Ref _ref;
  final List<HistoryEvent> _queue = [];
  Timer? _timer;

  HistoryBuffer(this._ref) {
    _startTimer();
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(flushInterval, (_) => flush(_ref));
  }

  /// Fire-and-forget logging (never blocks UI)
  void track({
    required String sessionId,
    required String restaurantId,
    required HistoryActionType actionType,
    Map<String, dynamic>? context,
  }) {
    _queue.add(
      HistoryEvent(
        sessionId: sessionId,
        restaurantId: restaurantId,
        actionType: actionType,
        context: context,
      ),
    );

    if (_queue.length >= batchThreshold) {
      flush(_ref);
    }
  }

  /// Flush queued events to POST /history. Identity comes from the bearer
  /// token; without a token the batch is dropped — anonymous history writes
  /// are rejected by the backend anyway.
  Future<void> flush(Ref? ref) async {
    if (_queue.isEmpty) return;

    final token = ref?.read(authProvider.notifier).currentToken;
    if (token == null) {
      _queue.clear();
      return;
    }

    final batch = List<HistoryEvent>.from(_queue);
    _queue.clear();

    try {
      await http.post(
        Uri.parse('$baseUrl/history'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'events': batch.map((e) => e.toJson()).toList(),
        }),
      );
    } catch (_) {
      // Intentionally silent: buffer never fails or interrupts UI flow
    }
  }

  void dispose() {
    _timer?.cancel();
    flush(_ref);
  }
}

final historyBufferProvider = Provider<HistoryBuffer>((ref) {
  final buffer = HistoryBuffer(ref);
  ref.onDispose(() => buffer.dispose());
  return buffer;
});
