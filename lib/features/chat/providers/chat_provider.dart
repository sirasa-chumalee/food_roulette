import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/chat_message.dart';
import '../../../data/models/recommendation.dart';

/// State for the chat screen.
class ChatState {
  final bool showInitialGrid;
  final bool isTyping;
  final String? currentPrompt;
  final List<ChatMessage> messages;

  const ChatState({
    required this.showInitialGrid,
    required this.isTyping,
    required this.messages,
    this.currentPrompt,
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
    String? currentPrompt,
    List<ChatMessage>? messages,
  }) {
    return ChatState(
      showInitialGrid: showInitialGrid ?? this.showInitialGrid,
      isTyping: isTyping ?? this.isTyping,
      currentPrompt: currentPrompt ?? this.currentPrompt,
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
    state = state.copyWith(
      showInitialGrid: false,
      isTyping: true,
      currentPrompt: text,
      messages: [
        ChatMessage.user(text),
        ChatMessage.loading(),
      ],
    );
  }

  /// Called after backend returns recommendations
  void addBotResponse({
    required String message,
    required List<RecommendedRestaurant> restaurants,
  }) {
    state = state.copyWith(
      isTyping: false,
      messages: [
        ChatMessage.user(state.currentPrompt ?? ""),
        ChatMessage.bot(message),
        ChatMessage.recommendations(restaurants),
      ],
    );
  }

  /// Backend/API failed
  void addError(String message) {
    state = state.copyWith(
      isTyping: false,
      messages: [
        ChatMessage.user(state.currentPrompt ?? ""),
        ChatMessage.error(message),
      ],
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