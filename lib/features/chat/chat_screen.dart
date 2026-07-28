import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../state/providers.dart';
import 'widgets/restaurant_card.dart';

class ChatScreen extends ConsumerWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncRecs = ref.watch(recommendationsProvider);

    return Scaffold(
      backgroundColor: const Color.fromARGB(255, 255, 255, 255),
      appBar: AppBar(
        title: const Text('Ummmm..'),
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.account_circle, size: 32),
            onPressed: () {
              context.push('/profile');
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: asyncRecs.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) =>
            Center(child: Text('Error loading recommendations: $err')),
        data: (data) {
          final totalExcludedCount = data.recommendations.fold<int>(
            0,
            (sum, item) => sum + item.excludedCount,
          );

          return Column(
            children: [
              // 1. Black & White Fallback Banner
              if (data.fallbackUsed || totalExcludedCount > 0)
                Container(
                  width: double.infinity,
                  decoration: const BoxDecoration(
                    color: Color(0xFF222222),
                    border: Border(
                      bottom: BorderSide(color: Color(0xFF444444), width: 1),
                    ),
                  ),
                  padding:
                      const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
                  child: Row(
                    children: [
                      const Icon(Icons.filter_alt, size: 18, color: Colors.white),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          totalExcludedCount > 0
                              ? 'We filtered out $totalExcludedCount unsafe dishes based on your preferences.'
                              : 'Tier-B Fallback active: showing available options.',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w500,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

              // 2. 2x2 Grid Recommendation View
              if (data.recommendations.isEmpty)
                const Expanded(
                  child: Center(
                    child: Text('No safe recommendations found.'),
                  ),
                )
              else
                Expanded(
                  child: GridView.builder(
                    padding: const EdgeInsets.all(12),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2, // 2 cards per row (2x2 layout)
                      crossAxisSpacing: 10, // Horizontal gap
                      mainAxisSpacing: 10, // Vertical gap
                      childAspectRatio: 0.85, // Adjust height-to-width ratio
                    ),
                    itemCount: data.recommendations.length,
                    itemBuilder: (context, index) {
                      final rec = data.recommendations[index];
                      return SafetyRestaurantCard(rec: rec);
                    },
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}