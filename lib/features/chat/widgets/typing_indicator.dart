import 'package:flutter/material.dart';

class TypingIndicator extends StatefulWidget{
  const TypingIndicator({super.key});

  @override
  State<StatefulWidget> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator>
  with SingleTickerProviderStateMixin {
    late final AnimationController _controller;

    @override
    void initState() {
      super.initState();

      _controller = AnimationController(
        vsync: this,
        duration: const Duration(microseconds: 900),
      )..repeat();
    }

    @override
    void dispose() {
      _controller.dispose();
      super.dispose();
    }

    Widget dot(int index) {
      return AnimatedBuilder(
        animation: _controller, 
        builder: (_, __) {
          final value = (_controller.value * 3 - index).clamp(0.0, 1.0);

          return Opacity(
            opacity: .3 + (.7 * value),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2),
              child: Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: Colors.grey,
                  shape: BoxShape.circle,
                ),
              ),
            )
          );
        }
      );
    }

    @override
    Widget build(BuildContext context) {
      return Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const CircleAvatar(
              radius: 16,
              backgroundColor: Color(0xFFEAEAEA),
              child: Icon(
                Icons.smart_toy,
                size: 18,
                color: Colors.black,
              ),
            ),

            const SizedBox(width: 8),

            Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 14,
              ),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(18),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(.05),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  dot(0),
                  dot(1),
                  dot(2),
                ],
              ),
            ),
          ],
        ),
      );
    }
  }