import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme.dart';
import 'features/chat/chat_screen.dart';
import 'features/detail/detail_screen.dart';
import 'features/profile/profile_screen.dart';

final GoRouter router = GoRouter(
  initialLocation: '/chat',
  routes: [
    GoRoute(
      path: '/chat',
      builder: (context, state) => const ChatScreen(),
    ),
    GoRoute(
      path: '/profile',
      builder: (context, state) => const ProfileScreen(),
    ),
    GoRoute(
      path: '/restaurant/:id',
      builder: (context, state) {
        final id = state.pathParameters['id'] ?? '';
        return DetailScreen(id: id);
      },
    ),
  ],
);

void main() {
  runApp(const ProviderScope(child: FoodRouletteApp()));
}

class FoodRouletteApp extends StatelessWidget {
  const FoodRouletteApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Food Roulette',
      theme: FoodTheme.lightTheme,
      routerConfig: router, // <--- Pass the 'router' variable here
      debugShowCheckedModeBanner: false,
    );
  }

  
}



