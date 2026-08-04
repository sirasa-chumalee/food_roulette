import 'package:flutter/material.dart';
import 'restaurant_card.dart';
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
        padding: const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 6,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              shrinkWrap: true,
              itemCount: restaurants.length,
              gridDelegate:
                const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: .95
                ),
              itemBuilder: (context, index) {
                return SafetyRestaurantCard(
                 rec: restaurants[index],
                );
              },
            ),
          ],
        ),
      );
  }
}