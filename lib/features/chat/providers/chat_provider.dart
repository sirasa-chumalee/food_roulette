import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';

import '../models/chat_message.dart';
import '../../../data/models/recommendation.dart';
import '../../../core/constants.dart';
import '../../auth/auth_provider.dart';

// ignore: non_constant_identifier_names
final String baseUrl = AppConfig.baseUrl;
/// State for the chat screen.
class ChatState {
  final String sessionId;
  final bool showInitialGrid;
  final bool isTyping;
  final List<ChatMessage> messages;

  const ChatState({
    required this.sessionId,
    required this.showInitialGrid,
    required this.isTyping,
    required this.messages,
  });

  factory ChatState.initial([String? sessionId]) {
    final activeSessionId = sessionId ?? const Uuid().v4();
    return ChatState(
      sessionId: activeSessionId,
      showInitialGrid: true,
      isTyping: false,
      messages: [
        ChatMessage.bot(
          "Hi! 👋 Here are some restaurants based on your preferences. "
          "Tell me what you're craving and I'll refine the recommendations.",
        ),
      ],
    );
  }

  ChatState copyWith({
    String? sessionId,
    bool? showInitialGrid,
    bool? isTyping,
    List<ChatMessage>? messages,
  }) {
    return ChatState(
      sessionId: sessionId ?? this.sessionId,
      showInitialGrid: showInitialGrid ?? this.showInitialGrid,
      isTyping: isTyping ?? this.isTyping,
      messages: messages ?? this.messages,
    );
  }
}

class ChatNotifier extends Notifier<ChatState> {
  final _uuid = const Uuid();

  /// Identity travels in the Authorization header; the backend derives the
  /// user from the signed JWT, never from a body field.
  Map<String, String> _authHeaders() {
    final token = ref.read(authProvider.notifier).currentToken;
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  @override
  ChatState build() {
    return ChatState.initial();
  }

  /// Alias method for ChatScreen callers
  Future<void> sendMessage(String text) async {
    await sendUserMessage(text);
  }

  /// User presses Send - executes live POST /chat API call
  Future<void> sendUserMessage(String text) async {
    final trimmedText = text.trim();
    if (trimmedText.isEmpty) return;

    // Start with a clean message list for the new turn
    final updated = <ChatMessage>[];

    // Add only current user prompt and loading state
    updated.add(ChatMessage.user(trimmedText));
    updated.add(ChatMessage.loading());

    state = state.copyWith(
      showInitialGrid: false,
      isTyping: true,
      messages: updated,
    );

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: _authHeaders(),
        body: jsonEncode({
          'session_id': state.sessionId,
          'text': trimmedText,
          'limit': 4,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        final String? replyText = data['reply'];
        final String? degradedCode = data['degraded'];
        final bool fallbackUsed = data['fallback_used'] ?? false;

        final restaurants = (data['recommendations'] as List? ?? [])
            .map((r) => RecommendedRestaurant.fromJson(r, baseUrl))
            .take(4)
            .toList();

        addBotResponse(
          message: replyText ?? '',
          restaurants: restaurants,
          fallbackUsed: fallbackUsed,
          degradedCode: degradedCode,
        );
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        // Dead token: sessionExpired throws, caught below as a quiet no-op —
        // the router is already bouncing to /login.
        await ref.read(authProvider.notifier).sessionExpired();
      } else {
        await _fallbackToPlainResults('LLM_UNAVAILABLE');
      }
    } catch (e) {
      if (e is AuthRequiredError) return; // logged out; screen is going away
      await _fallbackToPlainResults('LLM_UNAVAILABLE');
    }
  }

  /// Called after backend returns recommendations
  void addBotResponse({
    required String message,
    required List<RecommendedRestaurant> restaurants,
    bool fallbackUsed = false,
    String? degradedCode,
  }) {
    final updated = List<ChatMessage>.from(state.messages);

    // 1. Remove typing indicator
    updated.removeWhere((m) => m.type == ChatMessageType.loading);

    // 2. Remove old recommendation grids
    updated.removeWhere((m) => m.type == ChatMessageType.recommendations);

    // 3. Add bot text response (if non-empty)
    if (message.isNotEmpty) {
      updated.add(
        ChatMessage.bot(
          message,
          fallbackUsed: fallbackUsed,
          degradedCode: degradedCode,
        ),
      );
    }

    // 4. Append ONLY the new 4 recommendation cards
    if (restaurants.isNotEmpty) {
      updated.add(
        ChatMessage.recommendations(
          restaurants.take(4).toList(),
          fallbackUsed: fallbackUsed,
          degradedCode: message.isEmpty ? degradedCode : null,
        ),
      );
    }

    state = state.copyWith(
      isTyping: false,
      messages: updated,
    );
  }

  /// Fallback handler when LLM/Gemini is degraded or offline
  Future<void> _fallbackToPlainResults(String degradedReason) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/recommend'),
        headers: _authHeaders(),
        body: jsonEncode({
          'limit': 4,
        }),
      );

      List<RecommendedRestaurant> recs = [];
      bool fallbackUsed = false;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        fallbackUsed = data['fallback_used'] ?? false;

        recs = (data['recommendations'] as List? ?? [])
            .map((r) => RecommendedRestaurant.fromJson(r, baseUrl))
            .take(4)
            .toList();
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        // Dead token — same quiet no-op as above: logout is in flight and
        // the router redirect takes over from here.
        await ref.read(authProvider.notifier).sessionExpired();
      }

      final updated = List<ChatMessage>.from(state.messages);

      // Remove typing indicator AND previous recommendation grids
      updated.removeWhere((m) => m.type == ChatMessageType.loading);
      updated.removeWhere((m) => m.type == ChatMessageType.recommendations);

      updated.add(
        ChatMessage.recommendations(
          recs,
          fallbackUsed: fallbackUsed,
          degradedCode: degradedReason,
        ),
      );

      state = state.copyWith(
        isTyping: false,
        messages: updated,
      );
    } on AuthRequiredError {
      // Dead token: logout is in flight and the router redirect takes over
      // from here — nothing left for this fallback to do.
      return;
    } catch (_) {
      addError('Unable to connect to recommendation service at this time.');
    }
  }

  /// Backend/API failed
  void addError(String message) {
    final updated = List<ChatMessage>.from(state.messages);

    updated.removeWhere((m) => m.type == ChatMessageType.loading);

    updated.add(
      ChatMessage.error(message),
    );

    state = state.copyWith(
      isTyping: false,
      messages: updated,
    );
  }

  /// New conversation
  void reset() {
    state = ChatState.initial(_uuid.v4());
  }
}

final chatProvider = NotifierProvider<ChatNotifier, ChatState>(
  ChatNotifier.new,
);