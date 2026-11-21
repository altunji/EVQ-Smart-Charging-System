import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';

void main() => runApp(const EVQApp());

class Api {
  Api(this.base);
  final String base;
  Future<dynamic> request(String path, {Map<String, dynamic>? body}) async {
    final client = HttpClient();
    try {
      final uri = Uri.parse('$base$path');
      final req = body == null ? await client.getUrl(uri) : await client.postUrl(uri);
      req.headers.contentType = ContentType.json;
      if (body != null) req.write(jsonEncode(body));
      final res = await req.close();
      final text = await utf8.decoder.bind(res).join();
      final data = jsonDecode(text);
      if (res.statusCode >= 400) throw Exception(data['error'] ?? 'HTTP ${res.statusCode}');
      return data;
    } finally {
      client.close();
    }
  }
}

class EVQApp extends StatelessWidget {
  const EVQApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'EVQ Smart Charging', debugShowCheckedModeBanner: false,
    theme: ThemeData(colorSchemeSeed: const Color(0xFF147F90), useMaterial3: true),
    home: const ChargingPage(),
  );
}

class ChargingPage extends StatefulWidget {
  const ChargingPage({super.key});
  @override
  State<ChargingPage> createState() => _ChargingPageState();
}
class _ChargingPageState extends State<ChargingPage> {
  // Android emulator: 10.0.2.2; real phone: laptop LAN address.
  final address = TextEditingController(text: 'http://10.0.2.2:8000');
  final energy = TextEditingController(text: '20');
  String station = 'A', tariff = 'standard';
  String message = 'Connect to the Python simulation server';
  Map<String, dynamic>? session;
  List<dynamic> stations = [], history = [];
  bool busy = false;
  Api get api => Api(address.text.trim().replaceAll(RegExp(r'/$'), ''));

  @override
  void dispose() { address.dispose(); energy.dispose(); super.dispose(); }
  Future<void> perform(Future<void> Function() fn) async {
    if (busy) return;
    setState(() => busy = true);
    try { await fn(); } catch (e) { setState(() => message = 'Error: $e'); }
    finally { if (mounted) setState(() => busy = false); }
  }
  Future<void> refresh() => perform(() async {
    final s = await api.request('/api/stations');
    final h = await api.request('/api/sessions');
    if (mounted) setState(() { stations = s; history = h; message = 'Connected · simulated stations'; });
  });
  Future<void> begin() => perform(() async {
    final kwh = double.tryParse(energy.text.trim());
    if (kwh == null) throw Exception('Enter a valid energy amount (kWh)');
    final d = await api.request('/api/sessions', body: {
      'station': station, 'kwh': kwh, 'tariff': tariff,
    });
    final s = await api.request('/api/stations');
    if (mounted) setState(() { session = Map<String, dynamic>.from(d); stations = s; message = 'Charging session started (simulation)'; });
  });
  Future<void> change(String action) => perform(() async {
    if (session == null) return;
    final d = await api.request('/api/sessions/${session!['id']}/$action',
      body: action == 'advance' ? {'kwh': 5} : {});
    final s = await api.request('/api/stations');
    final h = await api.request('/api/sessions');
    if (mounted) setState(() { session = Map<String, dynamic>.from(d); stations = s; history = h; message = 'Updated: ${d['status']}'; });
  });
  @override
  Widget build(BuildContext context) {
    final charging = session?['status'] == 'charging';
    final percent = session == null ? 0.0 :
      ((session!['delivered_kwh'] as num) / (session!['target_kwh'] as num)).toDouble().clamp(0.0, 1.0);
    return Scaffold(
      appBar: AppBar(title: const Text('EVQ Smart Charging')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        const Card(child: Padding(padding: EdgeInsets.all(12),
          child: Text('ACADEMIC SIMULATION — No real EV charging or payment.'))),
        TextField(controller: address,
          decoration: const InputDecoration(labelText: 'Python API address', hintText: 'http://10.0.2.2:8000')),
        const SizedBox(height: 8),
        OutlinedButton.icon(onPressed: busy ? null : refresh,
          icon: const Icon(Icons.sync), label: const Text('Connect / Refresh')),
        const SizedBox(height: 10),
        Text('Stations', style: Theme.of(context).textTheme.titleLarge),
        if (stations.isEmpty) const Text('Connect to load stations'),
        for (final s in stations) ListTile(
          leading: const Icon(Icons.ev_station), title: Text('${s['name']}'),
          subtitle: Text('${s['status']}'), trailing: Text('${s['id']}')),
        const Divider(),
        DropdownButtonFormField<String>(value: station,
          decoration: const InputDecoration(labelText: 'Select charger'),
          items: const [DropdownMenuItem(value: 'A', child: Text('Station A')),
            DropdownMenuItem(value: 'B', child: Text('Station B'))],
          onChanged: charging ? null : (v) => setState(() => station = v!)),
        TextField(controller: energy, enabled: !charging,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Requested energy (kWh)', helperText: 'Simulation accepts 0–100 kWh')),
        DropdownButtonFormField<String>(value: tariff,
          decoration: const InputDecoration(labelText: 'Tariff'),
          items: const [DropdownMenuItem(value: 'standard', child: Text('Standard · 3.5 TRY/kWh')),
            DropdownMenuItem(value: 'off_peak', child: Text('Off peak · 2.5 TRY/kWh'))],
          onChanged: charging ? null : (v) => setState(() => tariff = v!)),
        const SizedBox(height: 12),
        FilledButton.icon(onPressed: busy || charging ? null : begin,
          icon: const Icon(Icons.play_arrow), label: const Text('Start simulated charging')),
        if (session != null) ...[
          const SizedBox(height: 14),
          Text('Session: ${session!['status']}', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          LinearProgressIndicator(value: percent),
          Text('${session!['delivered_kwh']} / ${session!['target_kwh']} kWh'),
          Text('Cost: ${session!['cost_try']} TRY'),
          Wrap(spacing: 8, children: [
            ElevatedButton(onPressed: busy || !charging ? null : () => change('advance'),
              child: const Text('Simulate +5 kWh')),
            OutlinedButton(onPressed: busy || !charging ? null : () => change('stop'),
              child: const Text('Stop')),
          ]),
        ],
        const Divider(),
        Text('Recent invoices / sessions', style: Theme.of(context).textTheme.titleLarge),
        for (final h in history.take(8)) ListTile(
          title: Text('${h['station']} · ${h['status']}'),
          subtitle: Text('${h['delivered_kwh']} kWh'),
          trailing: Text('${h['cost_try']} TRY')),
        const SizedBox(height: 10), Text(message),
      ]),
    );
  }
}
