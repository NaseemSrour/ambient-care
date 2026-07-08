/// Plain data models mirroring the backend's Pydantic API contract.
library;

enum TaskPeriod { morning, afternoon, evening, night, anytime }

TaskPeriod taskPeriodFromString(String v) =>
    TaskPeriod.values.firstWhere((e) => e.name == v,
        orElse: () => TaskPeriod.anytime);

/// Arabic labels for the period dropdown in the schedule screen.
const Map<TaskPeriod, String> taskPeriodLabelsAr = {
  TaskPeriod.morning: 'الصباح',
  TaskPeriod.afternoon: 'الظهر',
  TaskPeriod.evening: 'المساء',
  TaskPeriod.night: 'الليل',
  TaskPeriod.anytime: 'طوال اليوم',
};

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

class CareTask {
  final int id;
  final String title;
  final TaskPeriod period;
  final bool done;

  CareTask({
    required this.id,
    required this.title,
    required this.period,
    required this.done,
  });

  factory CareTask.fromJson(Map<String, dynamic> j) => CareTask(
        id: j['id'] as int,
        title: j['title'] as String,
        period: taskPeriodFromString(j['period'] as String),
        done: j['done'] as bool,
      );
}

class CareEvent {
  final int id;
  final String title;
  final String eventDate; // "YYYY-MM-DD"
  final String timeText;

  CareEvent({
    required this.id,
    required this.title,
    required this.eventDate,
    required this.timeText,
  });

  factory CareEvent.fromJson(Map<String, dynamic> j) => CareEvent(
        id: j['id'] as int,
        title: j['title'] as String,
        eventDate: j['event_date'] as String,
        timeText: j['time_text'] as String? ?? '',
      );
}

class BibleVerse {
  final int id;
  final String text;
  final String reference;

  BibleVerse({required this.id, required this.text, required this.reference});

  factory BibleVerse.fromJson(Map<String, dynamic> j) => BibleVerse(
        id: j['id'] as int,
        text: j['text'] as String,
        reference: j['reference'] as String? ?? '',
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
