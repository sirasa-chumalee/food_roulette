import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:food_roulette/features/chat/providers/chat_provider.dart';
import 'package:food_roulette/features/chat/widgets/chat_feed.dart';
import 'package:food_roulette/features/chat/widgets/message_input.dart';
import 'package:food_roulette/features/chat/widgets/recommendation_grid.dart';
import '../../state/providers.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(chatProvider);
    final recommendations = ref.watch(recommendationsProvider);

    return Scaffold(
      backgroundColor: const Color.fromARGB(255, 255, 255, 255),
      appBar: AppBar(
        title: const Text('Ummmm..'),
        centerTitle: false,
        actions: [
          // Refresh / New Chat Button
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: "New chat",
            onPressed: () async {
              // Clear conversation state
              ref.read(chatProvider.notifier).reset();

              // Reload initial recommendations
              await ref
                  .read(recommendationsProvider.notifier)
                  .refreshRecommendations();
            },
          ),
          // Profile Button
          IconButton(
            icon: const Icon(Icons.account_circle, size: 32),
            onPressed: () {
              context.push('/profile');
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: recommendations.when(
        loading: () {
          return const Center(
            child: CircularProgressIndicator(),
          );
        },
        error: (err, stack) => Center(
          child: Text('Error loading recommendations: $err'),
        ),
        data: (initialData) {
          return Column(
            children: [
              // 1. Initial 2x2 Recommendation Grid (Hidden once prompt is sent)
              // Flexible + SingleChildScrollView: the grid's natural height can
              // exceed a short viewport (small window, landscape, a keyboard
              // eating space) — this scrolls it internally instead of
              // overflowing the Column below.
              Flexible(
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 350),
                        child: chat.showInitialGrid
                            ? RecommendationGrid(
                                key: const ValueKey("initial-grid"),
                                restaurants: initialData.recommendations,
                              )
                            : const SizedBox.shrink(),
                      ),
                      if (chat.showInitialGrid) const Divider(height: 1),
                    ],
                  ),
                ),
              ),

              // 2. Chat Feed (Displays user prompts, bot responses, and updated recommendation cards)
              Expanded(
                child: ChatFeed(
                  messages: chat.messages,
                ),
              ),

              // 3. Bottom Message Input Bar
              MessageInput(
                enabled: !chat.isTyping,
                onSend: _sendMessage,
              ),
            ],
          );
        },
      ),
    );
  }

  /// Sends the prompt to chatProvider to execute POST /chat with live backend response
  Future<void> _sendMessage(String text) async {
    final chatNotifier = ref.read(chatProvider.notifier);

    try {
      await chatNotifier.sendMessage(text);
    } catch (_) {
      chatNotifier.addError(
        "Sorry, I couldn't get recommendations right now.",
      );
    }
  }
}