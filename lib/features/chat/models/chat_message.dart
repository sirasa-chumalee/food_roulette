import 'package:flutter/foundation.dart';
import '../../../data/models/recommendation.dart';

enum ChatMessageType {
  user,
  bot,
  recommendations,
  loading,
  error,
}

@immutable
class ChatMessage {
  final String id;
  final ChatMessageType type;
  final String? text;
  final List<RecommendedRestaurant>? restaurants;

  // Milestone 2 Additive Fields
  final bool fallbackUsed;
  final String? degradedCode;

  const ChatMessage({
    required this.id,
    required this.type,
    this.text,
    this.restaurants,
    this.fallbackUsed = false,
    this.degradedCode,
  });

  bool get isDegraded => degradedCode != null;

  factory ChatMessage.user(String text) {
    return ChatMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      type: ChatMessageType.user,
      text: text,
    );
  }

  factory ChatMessage.bot(
    String text, {
    List<RecommendedRestaurant>? restaurants,
    bool fallbackUsed = false,
    String? degradedCode,
  }) {
    return ChatMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      type: ChatMessageType.bot,
      text: text,
      restaurants: restaurants,
      fallbackUsed: fallbackUsed,
      degradedCode: degradedCode,
    );
  }

  factory ChatMessage.loading() {
    return const ChatMessage(
      id: "loading...",
      type: ChatMessageType.loading,
    );
  }

  factory ChatMessage.error(String text) {
    return ChatMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      type: ChatMessageType.error,
      text: text,
    );
  }

  factory ChatMessage.recommendations(
    List<RecommendedRestaurant> restaurants, {
    bool fallbackUsed = false,
    String? degradedCode,
  }) {
    return ChatMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      type: ChatMessageType.recommendations,
      restaurants: restaurants,
      fallbackUsed: fallbackUsed,
      degradedCode: degradedCode,
    );
  }
}