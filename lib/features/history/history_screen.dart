import 'package:flutter/material.dart';

class MyHistoryScreen extends StatelessWidget { // <--- Changed here
  const MyHistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: Text('History')),
    );
  }
}