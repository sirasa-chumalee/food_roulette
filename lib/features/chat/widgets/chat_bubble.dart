import 'package:flutter/material.dart';

class ChatBubble extends StatelessWidget {
  final String text;
  final bool isUser;
  final bool isError;

  const ChatBubble({
    super.key,
    required this.text,
    required this.isUser,
    this.isError = false,
  });

  @override
  Widget build(BuildContext context) {
    final bubbleColor = isError ? Colors.red.shade100
      : isUser
        ? const Color(0xFF2D2D2D)
        : Colors.white;

    final textColor = isUser ? Colors.white : Colors.black87;

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: 16,
        vertical: 6,
      ),
      child: Row(
        mainAxisAlignment: 
          isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser)
            const CircleAvatar(
              radius: 16,
              backgroundColor: Color(0xFFEAEAEA),
              child: Icon(
                Icons.smart_toy_rounded,
                size: 18,
                color: Colors.black54,
              ),
            ),

          if (!isUser) const SizedBox(width: 8),

          Flexible(
            child: Container(
              constraints: const BoxConstraints(maxWidth: 300),
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 12,
              ),
              decoration: BoxDecoration(
                color: bubbleColor,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(18),
                  topRight: const Radius.circular(18),
                  bottomLeft: Radius.circular(isUser ? 18 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 18),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(.05),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Text(
                text,
                style: TextStyle(
                  fontSize: 15,
                  height: 1.45,
                  color: textColor,
                ),
              ),
            ),
          ),

          if (isUser) const SizedBox(width: 8),

          if (isUser)
            const CircleAvatar(
              radius: 16,
              backgroundColor: Colors.black,
              child: Icon(
                Icons.person,
                size: 18,
                color: Colors.white,
              ),
            ),
        ],
      ),
    );
  }
}