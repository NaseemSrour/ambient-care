import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/models.dart';
import '../state/providers.dart';

/// Manage routine tasks (checklist) and upcoming visits/appointments.
class ScheduleScreen extends ConsumerWidget {
  const ScheduleScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tasks = ref.watch(tasksProvider);
    final events = ref.watch(eventsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('المهام والزيارات')),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                _SectionHeader(
                  title: 'المهام اليومية',
                  onAdd: () => _addTask(context, ref),
                ),
                tasks.when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (_, _) => const Text('تعذّر تحميل المهام'),
                  data: (list) => list.isEmpty
                      ? const _Empty('لا مهام بعد — اضغط + لإضافة مهمة')
                      : Column(
                          children: [for (final t in list) _TaskTile(task: t)],
                        ),
                ),
                const SizedBox(height: 28),
                _SectionHeader(
                  title: 'الزيارات والمواعيد',
                  onAdd: () => _addEvent(context, ref),
                ),
                events.when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (_, _) => const Text('تعذّر تحميل الزيارات'),
                  data: (list) => list.isEmpty
                      ? const _Empty('لا زيارات مُقرّرة — اضغط + لإضافة موعد')
                      : Column(
                          children: [for (final e in list) _EventTile(event: e)],
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _addTask(BuildContext context, WidgetRef ref) async {
    final titleCtrl = TextEditingController();
    TaskPeriod period = TaskPeriod.anytime;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('مهمة جديدة'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleCtrl,
                autofocus: true,
                maxLength: 60,
                decoration: const InputDecoration(hintText: 'مثال: تناول دواء الصباح'),
              ),
              DropdownButtonFormField<TaskPeriod>(
                initialValue: period,
                decoration: const InputDecoration(labelText: 'الوقت'),
                items: [
                  for (final p in TaskPeriod.values)
                    DropdownMenuItem(value: p, child: Text(taskPeriodLabelsAr[p]!)),
                ],
                onChanged: (v) => setLocal(() => period = v ?? TaskPeriod.anytime),
              ),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('إلغاء')),
            FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('إضافة')),
          ],
        ),
      ),
    );
    if (ok == true && titleCtrl.text.trim().isNotEmpty) {
      await ref.read(apiProvider).addTask(titleCtrl.text.trim(), period);
      ref.invalidate(tasksProvider);
    }
  }

  Future<void> _addEvent(BuildContext context, WidgetRef ref) async {
    final titleCtrl = TextEditingController();
    final timeCtrl = TextEditingController();
    DateTime date = DateTime.now();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('زيارة / موعد جديد'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleCtrl,
                autofocus: true,
                maxLength: 80,
                decoration: const InputDecoration(hintText: 'مثال: زيارة يوسف'),
              ),
              TextField(
                controller: timeCtrl,
                maxLength: 40,
                decoration:
                    const InputDecoration(hintText: 'الوقت: مثال حوالي الساعة ٥'),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.calendar_today, size: 20),
                  const SizedBox(width: 8),
                  Text('${date.year}-${date.month.toString().padLeft(2, '0')}'
                      '-${date.day.toString().padLeft(2, '0')}'),
                  const Spacer(),
                  TextButton(
                    onPressed: () async {
                      final picked = await showDatePicker(
                        context: ctx,
                        initialDate: date,
                        firstDate: DateTime.now().subtract(const Duration(days: 1)),
                        lastDate: DateTime.now().add(const Duration(days: 365)),
                      );
                      if (picked != null) setLocal(() => date = picked);
                    },
                    child: const Text('اختر اليوم'),
                  ),
                ],
              ),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('إلغاء')),
            FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('إضافة')),
          ],
        ),
      ),
    );
    if (ok == true && titleCtrl.text.trim().isNotEmpty) {
      final dateStr = '${date.year}-${date.month.toString().padLeft(2, '0')}'
          '-${date.day.toString().padLeft(2, '0')}';
      await ref
          .read(apiProvider)
          .addEvent(titleCtrl.text.trim(), dateStr, timeCtrl.text.trim());
      ref.invalidate(eventsProvider);
    }
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.onAdd});
  final String title;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Text(title,
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        ),
        IconButton.filled(
          iconSize: 28,
          onPressed: onAdd,
          icon: const Icon(Icons.add),
        ),
      ],
    );
  }
}

class _TaskTile extends ConsumerWidget {
  const _TaskTile({required this.task});
  final CareTask task;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      child: CheckboxListTile(
        value: task.done,
        title: Text(task.title,
            style: TextStyle(
              fontSize: 20,
              decoration: task.done ? TextDecoration.lineThrough : null,
            )),
        subtitle: Text(taskPeriodLabelsAr[task.period]!),
        secondary: IconButton(
          icon: const Icon(Icons.delete_outline, color: Colors.red),
          onPressed: () async {
            await ref.read(apiProvider).deleteTask(task.id);
            ref.invalidate(tasksProvider);
          },
        ),
        onChanged: (v) async {
          await ref.read(apiProvider).setTaskDone(task.id, v ?? false);
          ref.invalidate(tasksProvider);
        },
      ),
    );
  }
}

class _EventTile extends ConsumerWidget {
  const _EventTile({required this.event});
  final CareEvent event;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final subtitle = [event.eventDate, if (event.timeText.isNotEmpty) event.timeText]
        .join(' • ');
    return Card(
      child: ListTile(
        leading: const Icon(Icons.event, size: 30),
        title: Text(event.title, style: const TextStyle(fontSize: 20)),
        subtitle: Text(subtitle),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, color: Colors.red),
          onPressed: () async {
            await ref.read(apiProvider).deleteEvent(event.id);
            ref.invalidate(eventsProvider);
          },
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Text(text,
            style: const TextStyle(color: Colors.black54, fontSize: 16)),
      );
}
