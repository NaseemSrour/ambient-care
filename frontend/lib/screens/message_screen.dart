import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/config.dart';
import '../data/api_client.dart';
import '../state/providers.dart';

/// Single-action screen: type one warm note (max 120 chars) and send it.
class MessageScreen extends ConsumerStatefulWidget {
  const MessageScreen({super.key});

  @override
  ConsumerState<MessageScreen> createState() => _MessageScreenState();
}

class _MessageScreenState extends ConsumerState<MessageScreen> {
  final _controller = TextEditingController();
  bool _sending = false;
  int _cooldown = 0; // seconds remaining on the double-tap guard
  Timer? _timer;

  @override
  void dispose() {
    _controller.dispose();
    _timer?.cancel();
    super.dispose();
  }

  void _startCooldown() {
    setState(() => _cooldown = AppConfig.sendCooldownSeconds);
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (_cooldown <= 1) {
        t.cancel();
        setState(() => _cooldown = 0);
      } else {
        setState(() => _cooldown--);
      }
    });
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (_sending || _cooldown > 0 || text.isEmpty) return;
    setState(() => _sending = true);
    try {
      await ref.read(apiProvider).sendMessage(text);
      _controller.clear();
      ref.invalidate(messagesProvider);
      if (mounted) {
        _startCooldown(); // prevent accidental double-send
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('تم الإرسال إلى الشاشة ✅')),
        );
      }
    } on ApiException catch (e) {
      _showError(e.messageAr);
    } catch (_) {
      _showError('تعذّر الاتصال بالخادم');
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg), backgroundColor: Colors.red));
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(messagesProvider);
    final disabled = _sending || _cooldown > 0;

    return Scaffold(
      appBar: AppBar(title: const Text('إرسال رسالة')),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                TextField(
                  controller: _controller,
                  autofocus: true,
                  maxLines: 4,
                  maxLength: AppConfig.messageMaxChars,
                  style: const TextStyle(fontSize: 22),
                  decoration: const InputDecoration(
                    hintText: 'مثال: مرحباً يا جدّتي، سارة قادمة لزيارتك الساعة ٣',
                  ),
                  onChanged: (_) => setState(() {}), // refresh send-enabled state
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  onPressed:
                      disabled || _controller.text.trim().isEmpty ? null : _send,
                  icon: _sending
                      ? const SizedBox(
                          height: 24,
                          width: 24,
                          child: CircularProgressIndicator(
                              strokeWidth: 3, color: Colors.white))
                      : const Icon(Icons.send, size: 26),
                  label: Text(
                    _sending
                        ? 'جارٍ الإرسال…'
                        : _cooldown > 0
                            ? 'انتظر $_cooldown ثانية'
                            : 'إرسال إلى الشاشة',
                  ),
                ),
                const SizedBox(height: 28),
                const Text('الرسائل الأخيرة',
                    style:
                        TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                messages.when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (_, _) => const Text('تعذّر تحميل الرسائل'),
                  data: (list) => list.isEmpty
                      ? const Text('لا توجد رسائل حالية',
                          style: TextStyle(color: Colors.black54, fontSize: 16))
                      : Column(
                          children: [
                            for (final m in list)
                              Card(
                                child: ListTile(
                                  title: Text(m.text,
                                      style: const TextStyle(fontSize: 18)),
                                  trailing: IconButton(
                                    icon: const Icon(Icons.delete_outline,
                                        color: Colors.red),
                                    onPressed: () async {
                                      await ref
                                          .read(apiProvider)
                                          .deleteMessage(m.id);
                                      ref.invalidate(messagesProvider);
                                    },
                                  ),
                                ),
                              ),
                          ],
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
