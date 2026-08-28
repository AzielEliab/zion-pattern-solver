import 'package:flutter/material.dart';

import 'theme.dart';

const cap = 0.75;
const floor = 0.25;

double capConfidence(double raw) {
  if (raw.isNaN || raw.isInfinite || raw < 0) return 0;
  return raw > cap ? cap : raw;
}

class PatternCat {
  const PatternCat(this.id, this.name, this.priority);
  final String id;
  final String name;
  final String priority;
}

const patterns = [
  PatternCat('P1', 'Kinematic & Timeline Impossibility', 'critical'),
  PatternCat('P2', 'Document Provenance & Integrity', 'critical'),
  PatternCat('P3', 'Witness & Archival Void', 'high'),
  PatternCat('P4', 'Geographic / Location Manipulation', 'medium'),
  PatternCat('P5', 'Pre-Event Discrediting & Suppression', 'high'),
  PatternCat('P6', 'Political / Motive Contextual', 'medium'),
  PatternCat('P7', 'Secondary Encoded Testimony / Rubye', 'critical'),
  PatternCat('P8', 'Rapid Narrative Lock', 'high'),
  PatternCat('P9', 'Forensic / Physical Evidence Gap', 'high'),
];

void main() {
  runApp(const ZionApp());
}

class ZionApp extends StatelessWidget {
  const ZionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ZionPattern',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      home: const CapPage(),
    );
  }
}

class CapPage extends StatefulWidget {
  const CapPage({super.key});

  @override
  State<CapPage> createState() => _CapPageState();
}

class _CapPageState extends State<CapPage> {
  double _raw = 0.62;
  PatternCat _pat = patterns.first;

  @override
  Widget build(BuildContext context) {
    final capped = capConfidence(_raw);
    final uncertainty = 1.0 - capped;
    final floorOk = uncertainty + 1e-9 >= floor;
    return Scaffold(
      appBar: AppBar(title: const Text('ZionPattern')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            color: const Color(0xFF2A1515),
            child: const Padding(
              padding: EdgeInsets.all(12),
              child: Text(
                'Does not “solve” Zioncheck or any case. Outputs are provisional '
                'and assistive only. Maximum displayed confidence is 75%. '
                'Irreducible uncertainty floor is 25%.',
                style: TextStyle(height: 1.4),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text('75% cap   ·   25% floor', style: const TextStyle(color: kGold, fontSize: 18)),
          const SizedBox(height: 8),
          Text('raw confidence  ${_raw.toStringAsFixed(2)}'),
          Slider(
            value: _raw,
            min: 0,
            max: 1,
            divisions: 100,
            label: _raw.toStringAsFixed(2),
            onChanged: (v) => setState(() => _raw = v),
          ),
          Text(
            'capped_confidence  ${capped.toStringAsFixed(2)}   (min(raw, 0.75))',
            style: const TextStyle(color: kGold, fontSize: 16),
          ),
          Text('documented uncertainty  ${uncertainty.toStringAsFixed(2)}   floor held: $floorOk'),
          const SizedBox(height: 16),
          const Text('Anomaly pattern (seeded on the 1936 public record — interrogation, not a verdict)'),
          const SizedBox(height: 8),
          for (final p in patterns)
            RadioListTile<PatternCat>(
              value: p,
              groupValue: _pat,
              onChanged: (v) => setState(() => _pat = v!),
              title: Text('${p.id}  ${p.name}'),
              subtitle: Text('priority ${p.priority}'),
              activeColor: kGold,
            ),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Text(
                'Session note: ${_pat.id} interrogated. Capped confidence '
                '${capped.toStringAsFixed(2)}. Uncertainty '
                '${uncertainty.toStringAsFixed(2)} logged. This is not a '
                'historical conclusion and does not solve the case.',
                style: const TextStyle(height: 1.4),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
