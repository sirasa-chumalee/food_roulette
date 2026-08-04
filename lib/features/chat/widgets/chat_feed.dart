import 'package:flutter/material.dart';

import '../models/chat_message.dart';
import 'chat_bubble.dart';
import 'recommendation_grid.dart';
import 'typing_indicator.dart';

class ChatFeed extends StatefulWidget {
  final List<ChatMessage> messages;

  const ChatFeed({
    super.key,
    required this.messages,
  });

  @override
  State<ChatFeed> createState() => _ChatFeedState();
}

class _ChatFeedState extends State<ChatFeed> {
  final ScrollController _controller = ScrollController();

  @override
  void didUpdateWidget(covariant ChatFeed oldWidget) {
    super.didUpdateWidget(oldWidget);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_controller.hasClients) {
        _controller.animateTo(
          _controller.position.maxScrollExtent,
          duration: const Duration(microseconds: 250), 
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: _controller,
      padding: const EdgeInsets.symmetric(vertical: 12),
      itemCount: widget.messages.length,
      itemBuilder: (context, index) {
        final message = widget.messages[index];

        switch (message.type) {
          case ChatMessageType.user:
            return ChatBubble(
              text: message.text ?? '',
              isUser: true,
            );

          case ChatMessageType.bot:
            return ChatBubble(
              text: message.text ?? '',
              isUser: false,
            );

          case ChatMessageType.error:
            return ChatBubble(
              text: message.text ?? 'Something went wrong.',
              isUser: false,
              isError: true,
            );

          case ChatMessageType.loading:
            return const TypingIndicator();

          case ChatMessageType.recommendations:
            return RecommendationGrid(
              restaurants: message.restaurants ?? [],
            );
        }
      },
    );
  }
}