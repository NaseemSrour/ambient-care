import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/config.dart';
import 'models.dart';

/// Raised on any non-2xx response; carries an Arabic-friendly message.
class ApiException implements Exception {
  final int statusCode;
  final String messageAr;
  ApiException(this.statusCode, this.messageAr);
  @override
  String toString() => 'ApiException($statusCode): $messageAr';
}

/// Thin REST wrapper around the FastAPI backend.
class ApiClient {
  ApiClient({this.token});

  final String? token;
  final _base = AppConfig.apiBase;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  Uri _uri(String path) => Uri.parse('$_base$path');

  dynamic _decode(http.Response r) {
    if (r.statusCode >= 200 && r.statusCode < 300) {
      return r.body.isEmpty ? null : jsonDecode(utf8.decode(r.bodyBytes));
    }
    String detail = 'حدث خطأ، حاول مرة أخرى';
    try {
      final body = jsonDecode(utf8.decode(r.bodyBytes));
      if (body is Map && body['detail'] is String) detail = body['detail'];
    } catch (_) {}
    if (r.statusCode == 401) detail = 'انتهت الجلسة، سجّل الدخول من جديد';
    throw ApiException(r.statusCode, detail);
  }

  // --- Auth -----------------------------------------------------------------
  Future<String> login(String passcode) async {
    final r = await http.post(_uri('/api/auth/login'),
        headers: _headers, body: jsonEncode({'passcode': passcode}));
    return _decode(r)['token'] as String;
  }

  // --- Messages -------------------------------------------------------------
  Future<List<FamilyMessage>> getMessages() async {
    final r = await http.get(_uri('/api/messages'), headers: _headers);
    return (_decode(r) as List)
        .map((e) => FamilyMessage.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<FamilyMessage> sendMessage(String text) async {
    final r = await http.post(_uri('/api/messages'),
        headers: _headers, body: jsonEncode({'text': text}));
    return FamilyMessage.fromJson(_decode(r) as Map<String, dynamic>);
  }

  Future<void> deleteMessage(int id) async =>
      _decode(await http.delete(_uri('/api/messages/$id'), headers: _headers));

  // --- Tasks ----------------------------------------------------------------
  Future<List<CareTask>> getTasks() async {
    final r = await http.get(_uri('/api/tasks'), headers: _headers);
    return (_decode(r) as List)
        .map((e) => CareTask.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CareTask> addTask(String title, TaskPeriod period) async {
    final r = await http.post(_uri('/api/tasks'),
        headers: _headers,
        body: jsonEncode({'title': title, 'period': period.name}));
    return CareTask.fromJson(_decode(r) as Map<String, dynamic>);
  }

  Future<CareTask> setTaskDone(int id, bool done) async {
    final r = await http.patch(_uri('/api/tasks/$id'),
        headers: _headers, body: jsonEncode({'done': done}));
    return CareTask.fromJson(_decode(r) as Map<String, dynamic>);
  }

  Future<void> deleteTask(int id) async =>
      _decode(await http.delete(_uri('/api/tasks/$id'), headers: _headers));

  // --- Events ---------------------------------------------------------------
  Future<List<CareEvent>> getEvents() async {
    final r = await http.get(_uri('/api/events'), headers: _headers);
    return (_decode(r) as List)
        .map((e) => CareEvent.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CareEvent> addEvent(String title, String date, String timeText) async {
    final r = await http.post(_uri('/api/events'),
        headers: _headers,
        body: jsonEncode(
            {'title': title, 'event_date': date, 'time_text': timeText}));
    return CareEvent.fromJson(_decode(r) as Map<String, dynamic>);
  }

  Future<void> deleteEvent(int id) async =>
      _decode(await http.delete(_uri('/api/events/$id'), headers: _headers));

  // --- Bible verses ---------------------------------------------------------
  Future<List<BibleVerse>> getVerses() async {
    final r = await http.get(_uri('/api/verses'), headers: _headers);
    return (_decode(r) as List)
        .map((e) => BibleVerse.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<BibleVerse> addVerse(String text, String reference) async {
    final r = await http.post(_uri('/api/verses'),
        headers: _headers,
        body: jsonEncode({'text': text, 'reference': reference}));
    return BibleVerse.fromJson(_decode(r) as Map<String, dynamic>);
  }

  Future<void> deleteVerse(int id) async =>
      _decode(await http.delete(_uri('/api/verses/$id'), headers: _headers));

  // --- Device status --------------------------------------------------------
  Future<DeviceStatus> getStatus() async {
    final r = await http.get(_uri('/api/status'), headers: _headers);
    return DeviceStatus.fromJson(_decode(r) as Map<String, dynamic>);
  }
}
