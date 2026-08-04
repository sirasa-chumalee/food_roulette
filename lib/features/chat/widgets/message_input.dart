import 'package:flutter/material.dart';

class MessageInput extends StatefulWidget {
  final ValueChanged<String> onSend;
  final bool enabled;

  const MessageInput({
    super.key,
    required this.onSend,
    this.enabled = true,
  });

  @override
  State<MessageInput> createState() => _MessageInputState();
}

class _MessageInputState extends State<MessageInput> {
  late final TextEditingController _controller;
  late final FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _focusNode = FocusNode();
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    widget.onSend(text);
    _controller.clear();
    _focusNode.requestFocus();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(
            top: BorderSide(
              color: Color(0xFFE8E8E8),
            ),
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _controller,
                focusNode: _focusNode,
                enabled : widget.enabled,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(),
                decoration: InputDecoration(
                  hintText: "Type a response here...",
                  filled: true,
                  fillColor: const Color(0xFFF5F5F5),
                  border : OutlineInputBorder(
                    borderRadius : BorderRadius.circular(30),
                    borderSide : BorderSide.none,                    
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 14,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
            CircleAvatar(
              radius: 24,
              backgroundColor: Colors.black,
              child: IconButton(
                onPressed: widget.enabled ? _send : null, 
                icon: const Icon(
                  Icons.send_rounded,
                  color: Colors.white,
                )
              ),
            )
          ],
        ),
      )
    );
  }
}