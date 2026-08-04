import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../data/models/recommendation.dart';

class RecommendationGrid extends StatelessWidget{
  final List<RecommendedRestaurant> restaurants;

  const RecommendationGrid({
    super.key,
    required this.restaurants,
  });

  @override
  Widget build(BuildContext context) {
      if (restaurants.isEmpty) {
        return const SizedBox();
      }

      return Padding(
        padding: const EdgeInsetsGeometry.fromLTRB(16, 8, 16, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Padding(
              padding: EdgeInsetsGeometry.only(bottom: 12),
              child: Text(
                "Here are some restaurants I recommend",
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                ),
              ),
            ),

            GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              shrinkWrap: true,
              itemCount: restaurants.length,
              gridDelegate:
                const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: .78,
                ),
              itemBuilder: (context, index) {
                final restaurant = restaurants[index];

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
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(.06),
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
                        errorBuilder: (_,__,___) {
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
                  crossAxisAlignment: 
                    CrossAxisAlignment.start,
                  children: [
                    Text(
                      restaurant.displayName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),

                    const SizedBox(height: 4),

                    Row(
                      children: [
                        const Icon(
                          Icons.star,
                          color: Colors.amber,
                          size: 16,
                        ),

                        const SizedBox(width: 3),

                        Text(
                          restaurant.rating
                              ?.toStringAsFixed(1) ??
                            "-",
                        ),
                      ],
                    ),

                    const Spacer(),

                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: () {
                          context.push(
                            '/restaurant/${restaurant.restaurantId}');
                        }, 
                        child: const Text("View"),
                      ),
                    )
                  ],
                ),
              )
            )
          ],
        ),
      ),
    );
  }

  Widget _placeholder() {
    return Container(
      color: const Color(0xFFF3F3F3),
      child: const Center(
        child: Icon(
          Icons.restaurant,
          size: 45,
          color: Colors.grey,
        ),
      ),
    );
  }
}