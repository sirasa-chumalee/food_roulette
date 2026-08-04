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

  const ChatMessage({
    required this.id,
    required this.type,
    this.text,
    this.restaurants,
  });

  factory ChatMessage.user(String text) {
    return ChatMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(), 
      type: ChatMessageType.user, 
      text: text
    );
  }

  factory ChatMessage.bot(String text) {
    return ChatMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      type: ChatMessageType.bot,
      text: text,
    );
  } 

  factory ChatMessage.loading() {
    return ChatMessage(
      id: "loading..." ,
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
      List<RecommendedRestaurant> restaurants) {
    return ChatMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      type: ChatMessageType.recommendations,
      restaurants: restaurants,
    );
  }
}