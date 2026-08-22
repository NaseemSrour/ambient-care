/// Plain data models mirroring the backend's Pydantic API contract.
library;

class FamilyMessage {
  final int id;
  final String text;
  final DateTime createdAt;
  final DateTime expiresAt;

  FamilyMessage({
    required this.id,
    required this.text,
    required this.createdAt,
    required this.expiresAt,
  });

  factory FamilyMessage.fromJson(Map<String, dynamic> j) => FamilyMessage(
        id: j['id'] as int,
        text: j['text'] as String,
        createdAt: DateTime.parse(j['created_at'] as String),
        expiresAt: DateTime.parse(j['expires_at'] as String),
      );
}

class DeviceStatus {
  final bool online;
  final DateTime? lastSeen;
  final int? minutesSinceLastSeen;

  DeviceStatus({
    required this.online,
    required this.lastSeen,
    required this.minutesSinceLastSeen,
  });

  factory DeviceStatus.fromJson(Map<String, dynamic> j) => DeviceStatus(
        online: j['online'] as bool,
        lastSeen: j['last_seen'] != null
            ? DateTime.parse(j['last_seen'] as String)
            : null,
        minutesSinceLastSeen: j['minutes_since_last_seen'] as int?,
      );
}
