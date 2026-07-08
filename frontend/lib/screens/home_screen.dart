import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../state/providers.dart';
import 'message_screen.dart';
import 'schedule_screen.dart';
import 'verses_screen.dart';

/// The hub. Shows device status at a glance, then two big actions.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('رعاية العائلة'),
        actions: [
          IconButton(
            tooltip: 'تسجيل الخروج',
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                const _StatusCard(),
                const SizedBox(height: 20),
                _BigAction(
                  emoji: '💌',
                  label: 'إرسال رسالة',
                  subtitle: 'اكتب كلمة حبّ تظهر على الشاشة',
                  onTap: () => _go(context, const MessageScreen()),
                ),
                const SizedBox(height: 16),
                _BigAction(
                  emoji: '🗓️',
                  label: 'المهام والزيارات',
                  subtitle: 'أضِف تذكيرات الروتين ومواعيد الزيارة',
                  onTap: () => _go(context, const ScheduleScreen()),
                ),
                const SizedBox(height: 16),
                _BigAction(
                  emoji: '📖',
                  label: 'آيات الكتاب المقدّس',
                  subtitle: 'أضِف أو احذف الآيات التي تظهر على الشاشة',
                  onTap: () => _go(context, const VersesScreen()),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _go(BuildContext context, Widget screen) =>
      Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
}

/// Simple online / offline indicator for the TRMNL device.
class _StatusCard extends ConsumerWidget {
  const _StatusCard();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(statusProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: status.when(
          loading: () => const _StatusRow(
              color: Colors.grey, icon: Icons.sync, text: 'جارٍ التحقق…'),
          error: (_, _) => const _StatusRow(
              color: Colors.orange,
              icon: Icons.help_outline,
              text: 'تعذّر معرفة حالة الشاشة'),
          data: (s) => _StatusRow(
            color: s.online ? Colors.green : Colors.red,
            icon: s.online ? Icons.check_circle : Icons.cloud_off,
            text: s.online
                ? 'الشاشة متّصلة وتعمل'
                : 'الشاشة غير متّصلة حالياً',
          ),
        ),
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({required this.color, required this.icon, required this.text});
  final Color color;
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: color, size: 34),
        const SizedBox(width: 14),
        Expanded(
          child: Text(text,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
        ),
      ],
    );
  }
}

class _BigAction extends StatelessWidget {
  const _BigAction({
    required this.emoji,
    required this.label,
    required this.subtitle,
    required this.onTap,
  });

  final String emoji;
  final String label;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Row(
            children: [
              Text(emoji, style: const TextStyle(fontSize: 48)),
              const SizedBox(width: 18),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(label,
                        style: const TextStyle(
                            fontSize: 26, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 4),
                    Text(subtitle,
                        style: const TextStyle(
                            fontSize: 16, color: Colors.black54)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_left, size: 32), // RTL: points forward
            ],
          ),
        ),
      ),
    );
  }
}
