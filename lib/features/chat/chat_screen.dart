import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:food_roulette/features/chat/providers/chat_provider.dart';
import 'package:food_roulette/features/chat/widgets/chat_feed.dart';
import 'package:food_roulette/features/chat/widgets/message_input.dart';
import 'package:food_roulette/features/chat/widgets/recommendation_grid.dart';
import 'package:go_router/go_router.dart';
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

            //temporary refresh button
            IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: "New chat",
              onPressed: () async {

                // Clear conversation
                ref.read(chatProvider.notifier).reset();

                // Reload initial recommendations
                await ref
                    .read(recommendationsProvider.notifier)
                    .refreshRecommendations();

              },
            ),
          //profile button
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
        error: (err, stack) =>
            Center(child: Text(err.toString(),),),
        data: (initialData) {
          return Column(
            children: [

              // 4 initial recommendations cards before user prompt :3
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 350),

                child: chat.showInitialGrid
                  ? RecommendationGrid(
                    key: const ValueKey("initial-grid"),
                    restaurants: initialData.recommendations,
                  )
                  : const SizedBox.shrink(),
              ),

              if (chat.showInitialGrid)
                const Divider(height:1),

              Expanded(
                child: ChatFeed(
                  messages: chat.messages,
                ),
              ),

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

  Future<void> _sendMessage(String text) async {
    final chatNotifier = ref.read(chatProvider.notifier);

    //add user msg + typing indicator
    chatNotifier.sendUserMessage(text);

    try {
      final recommendationFuture  = await ref
        .read(recommendationsProvider.notifier)
        .refreshRecommendations(
          prompt: text,
        );

      await Future.delayed(const Duration(milliseconds: 1200));

      final reply = recommendationFuture;

      chatNotifier.addBotResponse(
        message: _generateBotReply(text),
        restaurants: reply.recommendations,
      );
    } catch (_) {
      chatNotifier.addError(
        "Sorry, I couldn't get recommendations right now.",
      );
    }
  }

  // this is only the message above to accompany the new recommended widgets, if we can connect this to backend so the logic is there later would be nice :) 
  String _generateBotReply(String prompt) {
    final lower = prompt.toLowerCase();

    if (lower.contains("spicy")) {
      return "🌶️ I found some spicy restaurants that match your preferences.";
    }

    if (lower.contains("cheap") ||
        lower.contains("budget") ||
        lower.contains("affordable")) {
      return "💰 Here are some budget-friendly places you might enjoy.";
    }

    if (lower.contains("seafood")) {
      return "🐟 I filtered the recommendations based on your seafood request.";
    }

    if (lower.contains("dessert")) {
      return "🍰 Here are some great dessert spots.";
    }

    if (lower.contains("coffee") ||
        lower.contains("cafe")) {
      return "☕ Here are some cafés you might like.";
    }

    if (lower.contains("japanese")) {
      return "🍣 I found some Japanese restaurants for you.";
    }

    if (lower.contains("korean")) {
      return "🇰🇷 Here are some Korean restaurants you might enjoy.";
    }

    if (lower.contains("thai")) {
      return "🇹🇭 Here are some Thai restaurants that fit your request.";
    }

    return "✨ I updated your recommendations based on your request.";
  }
}