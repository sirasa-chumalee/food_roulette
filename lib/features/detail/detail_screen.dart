import 'package:flutter/material.dart';
class DetailScreen extends StatelessWidget {
  final String id;

  const DetailScreen({super.key, required this.id});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Restaurant Detail #$id'),
      ),
      body: Center(
        child: Text(
          'Details for Restaurant ID: $id',
          style: const TextStyle(fontSize: 18),
        ),
      ),
    );
  }
}