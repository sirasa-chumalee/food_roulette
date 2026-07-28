import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

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
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
        title: const Text('Profile'),
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 16),

            // Profile Avatar
            const Center(
              child: CircleAvatar(
                radius: 40,
                backgroundColor: Colors.black, // <-- Black circle background
                foregroundColor: Colors.white, // <-- White icon inside
                child: Icon(Icons.person, size: 40),
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
      showCheckmark: false, // <-- Hides the green checkmark
      selectedColor: const Color(0xFF333333), // Dark grey when selected
      backgroundColor: Colors.transparent, // Outline style when unselected
      side: const BorderSide(color: Color(0xFF333333)), // Always show clear border
      labelStyle: TextStyle(
        color: _selectedSegment == 0 ? Colors.white : Colors.black, // High contrast text
        fontWeight: FontWeight.w500,
      ),
      onSelected: (selected) {
        if (selected) setState(() => _selectedSegment = 0);
      },
    ),
    const SizedBox(width: 8),
    ChoiceChip(
      label: const Text('History'),
      selected: _selectedSegment == 1,
      showCheckmark: false, // <-- Hides the green checkmark
      selectedColor: const Color(0xFF333333),
      backgroundColor: Colors.transparent,
      side: const BorderSide(color: Color(0xFF333333)),
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

            const SizedBox(height: 16),

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

// Temporary Placeholders for the two toggle views:
class PreferenceView extends StatelessWidget {
  const PreferenceView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(16.0),
      child: Center(child: Text('Dietary & Preference Options Go Here')),
    );
  }
}

class HistoryView extends StatelessWidget {
  const HistoryView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(16.0),
      child: Center(child: Text('Recent Search History Go Here')),
    );
  }
}