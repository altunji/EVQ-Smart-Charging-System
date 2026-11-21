import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:evq_smart_charging/main.dart';
void main() {
  testWidgets('EVQ app shows simulation warning', (tester) async {
    await tester.pumpWidget(const EVQApp());
    expect(find.textContaining('ACADEMIC SIMULATION'), findsOneWidget);
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
