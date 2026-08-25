import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme.dart';
import 'features/auth/auth_provider.dart';
import 'features/auth/login_screen.dart';
import 'features/chat/chat_screen.dart';
import 'features/detail/detail_screen.dart';
import 'features/profile/profile_screen.dart';

/// Bridges authProvider changes into go_router's refreshListenable so every
/// auth flip (restore at boot, login, 401-logout) re-runs the redirect.
class _AuthListenable extends ChangeNotifier {
  _AuthListenable(Ref ref) {
    ref.listen(authProvider, (_, __) => notifyListeners());
    ref.onDispose(dispose);
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final listenable = _AuthListenable(ref);

  return GoRouter(
    initialLocation: '/chat',
    refreshListenable: listenable,
    redirect: (context, state) {
      final status = ref.read(authProvider).status;
      final location = state.matchedLocation;

      // Still restoring the session from secure storage — hold on splash.
      if (status == AuthStatus.unknown) {
        return location == '/splash' ? null : '/splash';
      }

      final loggingIn = location == '/login';
      switch (status) {
        case AuthStatus.loggedOut:
          return loggingIn ? null : '/login';
        case AuthStatus.loggedIn:
          // Signed-in users never see the login screen again until they
          // explicitly log out (or a 401 logs them out).
          return (loggingIn || location == '/splash') ? '/chat' : null;
        case AuthStatus.unknown:
          return null; // unreachable; handled above
      }
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
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
});

void main() {
  runApp(const ProviderScope(child: FoodRouletteApp()));
}

class FoodRouletteApp extends ConsumerWidget {
  const FoodRouletteApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'Food Roulette',
      theme: FoodTheme.lightTheme,
      routerConfig: ref.watch(routerProvider),
      debugShowCheckedModeBanner: false,
    );
  }
}
