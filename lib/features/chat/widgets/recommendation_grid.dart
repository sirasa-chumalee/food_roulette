import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../data/models/history.dart';
import '../../../data/models/recommendation.dart';
import '../providers/chat_provider.dart';
import '../../history/services/history_buffer.dart';

class RecommendationGrid extends ConsumerWidget {
  final List<RecommendedRestaurant> restaurants;

  const RecommendationGrid({
    super.key,
    required this.restaurants,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final displayedList = restaurants.take(4).toList();
    if (displayedList.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(bottom: 12),
            child: Text(
              "Here are some restaurants I recommend",
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 15,
                color: Colors.black,
              ),
            ),
          ),
          GridView.builder(
            physics: const NeverScrollableScrollPhysics(),
            shrinkWrap: true,
            itemCount: displayedList.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: .78,
            ),
            itemBuilder: (context, index) {
              final restaurant = displayedList[index];
              return _RestaurantCard(restaurant: restaurant);
            },
          ),
        ],
      ),
    );
  }
}

class _RestaurantCard extends ConsumerWidget {
  final RecommendedRestaurant restaurant;

  const _RestaurantCard({
    required this.restaurant,
  });

  void _onCardTap(BuildContext context, WidgetRef ref) {
    final sessionId = ref.read(chatProvider).sessionId;
    
    // Pass restaurant name in context
    ref.read(historyBufferProvider).track(
      sessionId: sessionId,
      restaurantId: restaurant.restaurantId,
      actionType: HistoryActionType.click,
      context: {
        'name': restaurant.displayName,
      },
    );
    context.push('/restaurant/${restaurant.restaurantId}');
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: () => _onCardTap(context, ref),
      child: Ink(
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E1E),
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: .15),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Column(
          children: [
            Expanded(
              flex: 6,
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(18),
                ),
                child: restaurant.photoUrl != null && restaurant.photoUrl!.isNotEmpty
                    ? Image.network(
                        restaurant.photoUrl!,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => _placeholder(),
                      )
                    : _placeholder(),
              ),
            ),
            Expanded(
              flex: 5,
              child: Padding(
                padding: const EdgeInsets.all(10),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      restaurant.displayName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(
                          Icons.star,
                          color: Color(0xFFB0B0B0),
                          size: 16,
                        ),
                        const SizedBox(width: 3),
                        Text(
                          restaurant.rating != null && restaurant.rating! > 0
                              ? restaurant.rating!.toStringAsFixed(1)
                              : "4.2",
                          style: const TextStyle(
                            color: Color(0xFFCCCCCC),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                    const Spacer(),
                    SizedBox(
                      width: double.infinity,
                      height: 32,
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          backgroundColor: Colors.black,
                          foregroundColor: Colors.white,
                          padding: EdgeInsets.zero,
                          minimumSize: const Size(double.infinity, 32),
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                        ),
                        onPressed: () => _onCardTap(context, ref),
                        child: const Text("View", style: TextStyle(fontSize: 12)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _placeholder() {
    return Container(
      color: const Color(0xFF2A2A2A),
      child: const Center(
        child: Icon(
          Icons.restaurant,
          size: 45,
          color: Color(0xFF666666),
        ),
      ),
    );
  }
}