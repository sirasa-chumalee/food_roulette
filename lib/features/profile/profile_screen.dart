import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../state/providers.dart';
import '../../data/models/user_preferences.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  // 0 = Preference, 1 = History
  int _selectedSegment = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => context.pop(),
        ),
        title: const Text(
          'Profile',
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 16),

            // Profile Avatar
            const Center(
              child: CircleAvatar(
                radius: 80,
                backgroundColor: Colors.black, // Black circle background
                foregroundColor: Colors.white, // White icon inside
                child: Icon(Icons.person, size: 80),
              ),
            ),

            const SizedBox(height: 16),

            // Segmented Toggle Buttons (Preference / History)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ChoiceChip(
                  label: const Text('Preference'),
                  selected: _selectedSegment == 0,
                  showCheckmark: false,
                  selectedColor: Colors.black,
                  backgroundColor: Colors.white,
                  surfaceTintColor: Colors.transparent,
                  side: const BorderSide(color: Colors.black, width: 1.0),
                  labelStyle: TextStyle(
                    color: _selectedSegment == 0 ? Colors.white : Colors.black,
                    fontWeight: FontWeight.w500,
                  ),
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedSegment = 0);
                  },
                ),
                const SizedBox(width: 12),
                ChoiceChip(
                  label: const Text('History'),
                  selected: _selectedSegment == 1,
                  showCheckmark: false,
                  selectedColor: Colors.black,
                  backgroundColor: Colors.white,
                  surfaceTintColor: Colors.transparent,
                  side: const BorderSide(color: Colors.black, width: 1.0),
                  labelStyle: TextStyle(
                    color: _selectedSegment == 1 ? Colors.white : Colors.black,
                    fontWeight: FontWeight.w500,
                  ),
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedSegment = 1);
                  },
                ),
              ],
            ),

            const SizedBox(height: 20),

            // Conditionally display content based on toggle
            _selectedSegment == 0
                ? const PreferenceView()
                : const HistoryView(),
          ],
        ),
      ),
    );
  }
}

class PreferenceView extends ConsumerWidget {
  const PreferenceView({super.key});

  static const availableAllergens = [
    'peanuts',
    'tree_nuts',
    'shellfish',
    'fish',
    'wheat',
    'soy',
    'milk',
    'eggs',
    'sesame',
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncPrefs = ref.watch(profileProvider);

    return asyncPrefs.when(
      loading: () =>
          const Center(child: CircularProgressIndicator(color: Colors.black)),
      error: (err, stack) => Text('Error loading preferences: $err'),
      data: (prefs) {
        final hard = prefs.hard;
        final soft = prefs.soft;

        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. ALLERGENS (Multi-select)
              const Text(
                'Hard Constraints (Allergens)',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 12),

              // WRAP WITH SPREAD-OUT SPACING & MARGINS
              Wrap(
                spacing: 8.0, // Horizontal space between chips
                runSpacing: 12.0, // Vertical space between rows
                children: availableAllergens.map((allergen) {
                  final isSelected = hard.allergens.contains(allergen);
                  return Padding(
                    // THIS FORCE-SEPARATES THE ROWS VERTICALLY
                    padding: const EdgeInsets.symmetric(
                      vertical: 4.0,
                      horizontal: 2.0,
                    ),
                    child: FilterChip(
                      // Remove Flutter's invisible extra padding around tap targets
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      visualDensity: const VisualDensity(
                        horizontal: 0,
                        vertical: 0,
                      ),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 8,
                      ),
                      label: Text(
                        allergen,
                        style: TextStyle(
                          color: isSelected ? Colors.white : Colors.black,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      selected: isSelected,
                      selectedColor: Colors.black,
                      backgroundColor: Colors.white,
                      surfaceTintColor: Colors.transparent,
                      checkmarkColor: Colors.white,
                      side: const BorderSide(color: Colors.black, width: 1.0),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      onSelected: (selected) {
                        final updated = List<String>.from(hard.allergens);
                        selected
                            ? updated.add(allergen)
                            : updated.remove(allergen);
                        ref
                            .read(profileProvider.notifier)
                            .updatePreferences(
                              UserPreferences(
                                hard: hard.copyWith(allergens: updated),
                                soft: soft,
                              ),
                            );
                      },
                    ),
                  );
                }).toList(),
              ),

              const SizedBox(height: 24),

              // 2. DIET & RELIGIOUS TOGGLES
              Theme(
                data: ThemeData(
                  unselectedWidgetColor: Colors.black,
                  checkboxTheme: CheckboxThemeData(
                    fillColor: WidgetStateProperty.resolveWith((states) {
                      if (states.contains(WidgetState.selected)) {
                        return Colors.black;
                      }
                      return Colors.white;
                    }),
                    checkColor: WidgetStateProperty.all(Colors.white),
                    side: const BorderSide(color: Colors.black, width: 1.5),
                  ),
                ),
                child: Column(
                  children: [
                    CheckboxListTile(
                      activeColor: Colors.black,
                      title: const Text(
                        'Halal (No Pork / No Alcohol)',
                        style: TextStyle(fontWeight: FontWeight.w500),
                      ),
                      value: hard.halal,
                      onChanged: (val) => ref
                          .read(profileProvider.notifier)
                          .updatePreferences(
                            UserPreferences(
                              hard: hard.copyWith(halal: val ?? false),
                              soft: soft,
                            ),
                          ),
                    ),
                    CheckboxListTile(
                      activeColor: Colors.black,
                      title: const Text(
                        'Celiac (Wheat / Gluten Free)',
                        style: TextStyle(fontWeight: FontWeight.w500),
                      ),
                      value: hard.celiac,
                      onChanged: (val) => ref
                          .read(profileProvider.notifier)
                          .updatePreferences(
                            UserPreferences(
                              hard: hard.copyWith(celiac: val ?? false),
                              soft: soft,
                            ),
                          ),
                    ),
                    CheckboxListTile(
                      activeColor: Colors.black,
                      title: const Text(
                        'Jay (เจ)',
                        style: TextStyle(fontWeight: FontWeight.w500),
                      ),
                      value: hard.jay,
                      onChanged: (val) => ref
                          .read(profileProvider.notifier)
                          .updatePreferences(
                            UserPreferences(
                              hard: hard.copyWith(jay: val ?? false),
                              soft: soft,
                            ),
                          ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // 3. SPICY TOLERANCE SLIDER
              const Text(
                'Spicy Tolerance',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 8),
              SliderTheme(
                data: SliderTheme.of(context).copyWith(
                  activeTrackColor: Colors.black,
                  inactiveTrackColor: const Color(0xFFE0E0E0),
                  thumbColor: Colors.black,
                  overlayColor: const Color(0x11000000),
                  activeTickMarkColor: Colors.white,
                  inactiveTickMarkColor: Colors.black26,
                ),
                child: Slider(
                  value: soft.spicyTolerance.toDouble(),
                  min: 0,
                  max: 3,
                  divisions: 3,
                  label: [
                    'Level 0',
                    'Level 1',
                    'Level 2',
                    'Level 3',
                  ][soft.spicyTolerance],
                  onChanged: (val) {
                    ref
                        .read(profileProvider.notifier)
                        .updatePreferences(
                          UserPreferences(
                            hard: hard,
                            soft: soft.copyWith(spicyTolerance: val.round()),
                          ),
                        );
                  },
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        );
      },
    );
  }
}

class HistoryView extends StatelessWidget {
  const HistoryView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(24.0),
      child: Center(
        child: Text(
          'Recent Search History Go Here',
          style: TextStyle(color: Colors.grey, fontSize: 16),
        ),
      ),
    );
  }
}
