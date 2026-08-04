import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../data/models/recommendation.dart';

class SafetyRestaurantCard extends StatelessWidget {
  final RecommendedRestaurant rec;

  const SafetyRestaurantCard({super.key, required this.rec});

  @override
  Widget build(BuildContext context) {
    final isVerified = rec.isVerified;

    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: () {
        if (rec.needsAck) {
          _showCautionDialog(context, rec);
        } else {
          context.push('/restaurant/${rec.restaurantId}');
        }
      },
      child: Card(
        color: const Color.fromRGBO(240, 238, 238, 1),

        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: isVerified
              ? BorderSide.none
              : const BorderSide(color: Color.fromARGB(255, 235, 234, 231), width: 2),
        ),
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.star, size: 16, color: Color.fromARGB(255, 0, 0, 0)),
                      Text(' ${rec.rating ?? 4.5}'),
                    ],
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: isVerified ? const Color.fromARGB(255, 119, 119, 119) : const Color.fromARGB(255, 0, 0, 0),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          isVerified ? Icons.verified_user : Icons.warning_amber,
                          size: 14,
                          color: isVerified
                              ? const Color.fromARGB(255, 255, 255, 255)
                              : const Color.fromARGB(255, 2, 2, 2),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          isVerified ? 'Verified Safe' : 'Unverified Caution',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: isVerified
                                ? const Color.fromARGB(255, 255, 255, 255)
                                : const Color.fromARGB(255, 0, 0, 0),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                rec.displayName,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              if (rec.safeDishes.isNotEmpty)
                Text(
                  rec.safeDishes.map((d) => d.nameTh ?? d.nameEn ?? '').join(', '),
                  style: const TextStyle(color: Colors.grey),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    rec.priceTier ?? '฿฿',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  IconButton(
                    icon: const Icon(Icons.arrow_circle_right),
                    onPressed: () {
                      if (rec.needsAck) {
                        _showCautionDialog(context, rec);
                      } else {
                        context.push('/restaurant/${rec.restaurantId}');
                      }
                    },
                  ),
                ],
              )
            ],
          ),
        ),
      )
    );
  }

  void _showCautionDialog(BuildContext context, RecommendedRestaurant rec) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Unverified Safety Caution'),
        content: Text(
          rec.ackReason ??
              'This dish has incomplete allergen records. Please confirm ingredients with restaurant staff before consuming.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              context.push('/restaurant/${rec.restaurantId}');
            },
            child: const Text('Acknowledge & View'),
          ),
        ],
      ),
    );
  }
}