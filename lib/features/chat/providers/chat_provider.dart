import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/chat_message.dart';
import '../../../data/models/recommendation.dart';

/// State for the chat screen.
class ChatState {
  final bool showInitialGrid;
  final bool isTyping;
  final List<ChatMessage> messages;

  const ChatState({
    required this.showInitialGrid,
    required this.isTyping,
    required this.messages,
  });

  factory ChatState.initial() {
    return ChatState(
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
    bool? showInitialGrid,
    bool? isTyping,
    List<ChatMessage>? messages,
  }) {
    return ChatState(
      showInitialGrid: showInitialGrid ?? this.showInitialGrid,
      isTyping: isTyping ?? this.isTyping,
      messages: messages ?? this.messages,
    );
  }
}

class ChatNotifier extends Notifier<ChatState> {
  @override
  ChatState build() {
    return ChatState.initial();
  }

  /// User presses Send
  void sendUserMessage(String text) {
    final updated = List<ChatMessage>.from(state.messages);

    updated.add(
      ChatMessage.user(text),
    );

    updated.add(
      ChatMessage.loading(),
    );

    state = state.copyWith(
      showInitialGrid: false,
      isTyping: true,
      messages: updated,
    );
  }

  /// Called after backend returns recommendations
  void addBotResponse({
    required String message,
    required List<RecommendedRestaurant> restaurants,
  }) {
    final updated = List<ChatMessage>.from(state.messages);

    // Remove typing indicator
    updated.removeWhere(
      (m) => m.type == ChatMessageType.loading,
    );

    // Bot text
    updated.add(
      ChatMessage.bot(message),
    );

    // Recommendation widget
    updated.add(
      ChatMessage.recommendations(restaurants),
    );

    state = state.copyWith(
      isTyping: false,
      messages: updated,
    );
  }

  /// Backend/API failed
  void addError(String message) {
    final updated = List<ChatMessage>.from(state.messages);

    updated.removeWhere(
      (m) => m.type == ChatMessageType.loading,
    );

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
    state = ChatState.initial();
  }
}

final chatProvider =
    NotifierProvider<ChatNotifier, ChatState>(
  ChatNotifier.new,
);