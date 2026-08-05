import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../data/models/recommendation.dart';

class RecommendationGrid extends StatelessWidget {
  final List<RecommendedRestaurant> restaurants;

  const RecommendationGrid({
    super.key,
    required this.restaurants,
  });

  @override
  Widget build(BuildContext context) {
    // Strictly cap the display list to a maximum of 4 cards
    final displayList = restaurants.take(4).toList();

    if (displayList.isEmpty) {
      return const SizedBox();
    }

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
            itemCount: displayList.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: .78,
            ),
            itemBuilder: (context, index) {
              final restaurant = displayList[index];

              return _RestaurantCard(
                restaurant: restaurant,
              );
            },
          ),
        ],
      ),
    );
  }
}

class _RestaurantCard extends StatelessWidget {
  final RecommendedRestaurant restaurant;

  const _RestaurantCard({
    required this.restaurant,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: () {
        context.push('/restaurant/${restaurant.restaurantId}');
      },
      child: Ink(
        decoration: BoxDecoration(
          color: const Color.fromARGB(255, 83, 83, 83), // Dark card surface
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: const Color.fromARGB(255, 92, 92, 92).withValues(alpha: .15),
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
                child: restaurant.photoUrl != null &&
                        restaurant.photoUrl!.isNotEmpty
                    ? Image.network(
                        restaurant.photoUrl!,
                        width: double.infinity,
                        fit: BoxFit.cover,
                        errorBuilder: (context, index, _) {
                          return _placeholder();
                        },
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
                        color: Colors.white, // White text on dark card
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(
                          Icons.star,
                          color: Color.fromARGB(255, 241, 241, 241), // Darker monochrome star
                          size: 16,
                        ),
                        const SizedBox(width: 3),
                        Text(
                          restaurant.rating != null && restaurant.rating! > 0
                              ? restaurant.rating!.toStringAsFixed(1)
                              : "4.2",
                          style: const TextStyle(
                            color: Color.fromARGB(255, 241, 241, 241),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                    const Spacer(),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          backgroundColor: const Color.fromARGB(255, 31, 31, 31), // Dark/Black button
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                        ),
                        onPressed: () {
                          context.push(
                              '/restaurant/${restaurant.restaurantId}');
                        },
                        child: const Text("View"),
                      ),
                    )
                  ],
                ),
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget _placeholder() {
    return Container(
      color: const Color.fromARGB(255, 216, 216, 216), // Dark placeholder background
      child: const Center(
        child: Icon(
          Icons.restaurant,
          size: 45,
          color: Color.fromARGB(255, 112, 112, 112),
        ),
      ),
    );
  }
}