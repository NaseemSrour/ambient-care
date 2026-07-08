import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../state/providers.dart';

/// Manage the Bible verses that rotate on the elder's screen (one per day).
class VersesScreen extends ConsumerWidget {
  const VersesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final verses = ref.watch(versesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('آيات الكتاب المقدّس')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _addVerse(context, ref),
        icon: const Icon(Icons.add),
        label: const Text('آية جديدة'),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 90),
              children: [
                Card(
                  color: const Color(0xFFE0F2F1),
                  child: const Padding(
                    padding: EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Icon(Icons.info_outline, color: Color(0xFF00695C)),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'تظهر آية واحدة على الشاشة وتتغيّر تلقائياً عدّة مرّات '
                            'في اليوم (مع كل فترة: الصباح، الظهر، المساء، الليل)، '
                            'وتُختار عشوائياً من هذه القائمة.',
                            style: TextStyle(fontSize: 16),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                verses.when(
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (_, _) => const Text('تعذّر تحميل الآيات'),
                  data: (list) => list.isEmpty
                      ? const Padding(
                          padding: EdgeInsets.symmetric(vertical: 20),
                          child: Text(
                            'لا توجد آيات — اضغط «آية جديدة» للإضافة',
                            style:
                                TextStyle(color: Colors.black54, fontSize: 16),
                          ),
                        )
                      : Column(
                          children: [
                            for (final v in list)
                              Card(
                                child: ListTile(
                                  title: Text(v.text,
                                      style: const TextStyle(fontSize: 18)),
                                  subtitle: v.reference.isEmpty
                                      ? null
                                      : Text(v.reference,
                                          style: const TextStyle(
                                              fontSize: 14,
                                              color: Colors.black54)),
                                  trailing: IconButton(
                                    icon: const Icon(Icons.delete_outline,
                                        color: Colors.red),
                                    onPressed: () async {
                                      await ref
                                          .read(apiProvider)
                                          .deleteVerse(v.id);
                                      ref.invalidate(versesProvider);
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

  Future<void> _addVerse(BuildContext context, WidgetRef ref) async {
    final textCtrl = TextEditingController();
    final refCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('آية جديدة'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: textCtrl,
              autofocus: true,
              maxLines: 3,
              maxLength: 160,
              decoration: const InputDecoration(hintText: 'نصّ الآية'),
            ),
            TextField(
              controller: refCtrl,
              maxLength: 60,
              decoration:
                  const InputDecoration(hintText: 'المرجع (مثال: مزمور ٢٣: ١)'),
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
    );
    if (ok == true && textCtrl.text.trim().isNotEmpty) {
      await ref
          .read(apiProvider)
          .addVerse(textCtrl.text.trim(), refCtrl.text.trim());
      ref.invalidate(versesProvider);
    }
  }
}
