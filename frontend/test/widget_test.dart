// Basic smoke test: the app boots and shows the login screen.
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:ambient_care/main.dart';
import 'package:ambient_care/state/providers.dart';

void main() {
  testWidgets('shows login screen when logged out', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [sharedPreferencesProvider.overrideWithValue(prefs)],
        child: const AmbientCareApp(),
      ),
    );
    await tester.pump();

    expect(find.text('دخول'), findsOneWidget); // login button
  });
}
