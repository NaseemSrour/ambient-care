import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../data/api_client.dart';
import '../data/models.dart';

/// Overridden in main() once SharedPreferences is ready.
final sharedPreferencesProvider = Provider<SharedPreferences>(
  (ref) => throw UnimplementedError('SharedPreferences not initialised'),
);

const _tokenKey = 'family_token';

/// Holds the login token (persisted). null == logged out.
class AuthController extends StateNotifier<String?> {
  AuthController(this._prefs) : super(_prefs.getString(_tokenKey));

  final SharedPreferences _prefs;

  bool get isLoggedIn => state != null;

  Future<void> login(String passcode) async {
    final token = await ApiClient().login(passcode);
    await _prefs.setString(_tokenKey, token);
    state = token;
  }

  Future<void> logout() async {
    await _prefs.remove(_tokenKey);
    state = null;
  }
}

final authProvider = StateNotifierProvider<AuthController, String?>(
  (ref) => AuthController(ref.watch(sharedPreferencesProvider)),
);

/// An authenticated API client, rebuilt whenever the token changes.
final apiProvider = Provider<ApiClient>(
  (ref) => ApiClient(token: ref.watch(authProvider)),
);

/// Device online status — auto-refreshable.
final statusProvider = FutureProvider.autoDispose<DeviceStatus>(
  (ref) => ref.watch(apiProvider).getStatus(),
);

/// Recent (non-expired) family messages.
final messagesProvider =
    FutureProvider.autoDispose<List<FamilyMessage>>(
  (ref) => ref.watch(apiProvider).getMessages(),
);

/// All routine tasks.
final tasksProvider = FutureProvider.autoDispose<List<CareTask>>(
  (ref) => ref.watch(apiProvider).getTasks(),
);

/// All upcoming events.
final eventsProvider = FutureProvider.autoDispose<List<CareEvent>>(
  (ref) => ref.watch(apiProvider).getEvents(),
);

/// Bible verses that rotate on the elder's screen.
final versesProvider = FutureProvider.autoDispose<List<BibleVerse>>(
  (ref) => ref.watch(apiProvider).getVerses(),
);
