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
      title: 'ZionPattern Solver',
      debugShowCheckedModeBanner: false,
      theme: buildLightTheme(),
      darkTheme: buildDarkTheme(),
      themeMode: ThemeMode.system,
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

  @override
  Widget build(BuildContext context) {
    final capped = capConfidence(_raw);
    final uncertainty = 1.0 - capped;
    final floorOk = uncertainty + 1e-9 >= floor;
    return Scaffold(
      appBar: AppBar(
        title: const Text('ZionPattern Solver'),
        actions: const [
          Padding(
            padding: EdgeInsets.only(right: 16),
            child: Center(child: Text('Aziel Eliab')),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
        children: [
          Text(
            'Set a raw confidence. The displayed number stays at or below 75%, and the uncertainty floor stays at 25%.',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 20),
          Text('Raw confidence  ${_raw.toStringAsFixed(2)}'),
          Slider(
            value: _raw,
            min: 0,
            max: 1,
            divisions: 100,
            label: _raw.toStringAsFixed(2),
            onChanged: (v) => setState(() => _raw = v),
          ),
          const SizedBox(height: 8),
          Text(
            'Displayed confidence  ${capped.toStringAsFixed(2)}',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: kGold),
          ),
          const SizedBox(height: 8),
          Text(
            floorOk
                ? 'Uncertainty ${uncertainty.toStringAsFixed(2)} meets the 25% floor.'
                : 'Uncertainty ${uncertainty.toStringAsFixed(2)} is below the 25% floor.',
          ),
          const SizedBox(height: 12),
          const ExpansionTile(
            title: Text('Advanced'),
            childrenPadding: EdgeInsets.fromLTRB(8, 0, 8, 12),
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Text('Nine patterns from the 1936 public record.'),
              ),
              _PatternList(),
            ],
          ),
          const ExpansionTile(
            title: Text('About'),
            childrenPadding: EdgeInsets.fromLTRB(16, 0, 16, 16),
            children: [
              Text(
                'A finished walk is provisional and assistive. It does not solve Zioncheck or any case. You decide what the record supports.\n\nAuthor: Aziel Eliab.',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PatternList extends StatelessWidget {
  const _PatternList();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (final p in patterns)
          ListTile(
            dense: true,
            title: Text('${p.id}  ${p.name}'),
            subtitle: Text(p.priority),
          ),
      ],
    );
  }
}
