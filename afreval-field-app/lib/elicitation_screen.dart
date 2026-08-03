// §3.4 elicitation screen — image-prompted speech collection.
// Shows an image, records the speaker's description (>=15s), captures
// metadata (age/gender/language/environment). Spec scaffold.

import 'package:flutter/material.dart';

import 'telemetry.dart';

class ElicitationScreen extends StatefulWidget {
  const ElicitationScreen({super.key, required this.telemetry});

  final OnDeviceTelemetry telemetry;

  @override
  State<ElicitationScreen> createState() => _ElicitationScreenState();
}

class _ElicitationScreenState extends State<ElicitationScreen> {
  String? _imagePath;
  String _language = 'swa';
  bool _recording = false;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _imagePath == null
            ? const Center(child: Text('Pick an image prompt'))
            : Image.asset(_imagePath!),
        TextButton(
          onPressed: () => _pickImage(context),
          child: const Text('Choose image prompt'),
        ),
        DropdownButton<String>(
          value: _language,
          items: ['swa', 'amh', 'yor', 'lin', 'lug']
              .map((l) => DropdownMenuItem(value: l, child: Text(l)))
              .toList(),
          onChanged: (v) => setState(() => _language = v!),
        ),
        FilledButton.icon(
          onPressed: _recording ? _stop : _start,
          icon: Icon(_recording ? Icons.stop : Icons.mic),
          label: Text(_recording ? 'Stop' : 'Record description'),
        ),
      ],
    );
  }

  Future<void> _pickImage(BuildContext context) async {
    // Scaffold for image_picker; wire in build.
  }

  Future<void> _start() async {
    setState(() => _recording = true);
    // record >= 15s clip, then:
    // widget.telemetry.transcribeLocally(path, _language);
  }

  Future<void> _stop() async {
    setState(() => _recording = false);
  }
}
