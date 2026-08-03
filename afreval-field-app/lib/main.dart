// Milimo AfrEval field app — entry point.
// Image-prompted speech elicitation + on-device eval telemetry (§3.4).
// NOTE: scaffold/spec — build once the Flutter SDK is available.

import 'package:flutter/material.dart';

import 'elicitation_screen.dart';
import 'telemetry.dart';

void main() {
  runApp(const AfrevalFieldApp());
}

class AfrevalFieldApp extends StatelessWidget {
  const AfrevalFieldApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AfrEval Field',
      theme: ThemeData(colorSchemeSeed: Colors.teal, useMaterial3: true),
      home: const HomeShell(),
    );
  }
}

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  final _telemetry = OnDeviceTelemetry();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AfrEval Field')),
      body: ElicitationScreen(telemetry: _telemetry),
    );
  }
}
