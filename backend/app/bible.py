"""Seed list of famous, comforting Bible verses in Arabic.

These are only used to SEED the database on first run (see database.init_db).
After that, verses live in the `verses` table and are managed from the family
app, and daily rotation is done by repository.verse_for_day.

Verses are drawn from widely-loved passages (Psalms, Gospels) suitable for a
Catholic elder.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Verse:
    text: str
    reference: str  # Arabic reference, e.g. "مزمور ٢٣"


# Kept short and reassuring so they fit the calm, low-stimulation layout.
SEED_VERSES: list[Verse] = [
    Verse("الرَّبُّ راعيَّ فلا يُعوِزُني شيء", "مزمور ٢٣: ١"),
    Verse("لا تخف لأنّي معك", "إشعياء ٤١: ١٠"),
    Verse("تعالَوا إليَّ يا جميع المُتعَبين وأنا أُريحُكم", "متّى ١١: ٢٨"),
    Verse("الرَّبُّ نوري وخلاصي فممّن أخاف؟", "مزمور ٢٧: ١"),
    Verse("سلامي أُعطيكم، لا تضطرب قلوبكم ولا ترتَعِب", "يوحنّا ١٤: ٢٧"),
    Verse("أحبِبْ قريبَك كنفسِك", "متّى ٢٢: ٣٩"),
    Verse("الله محبّة", "يوحنّا الأولى ٤: ٨"),
    Verse("كلّ شيءٍ أستطيعه في الذي يقوّيني", "فيلبّي ٤: ١٣"),
    Verse("ارمِ على الرَّبِّ همّك وهو يعولك", "مزمور ٥٥: ٢٢"),
    Verse("الرَّبُّ قريبٌ من المُنكسِري القلوب", "مزمور ٣٤: ١٨"),
    Verse("افرحوا في الرَّبِّ كلَّ حين", "فيلبّي ٤: ٤"),
    Verse("رحمةُ الرَّبِّ إلى الأبد", "مزمور ١٠٣: ١٧"),
    Verse("أنا هو نور العالم", "يوحنّا ٨: ١٢"),
    Verse("طوبى للرُّحماء فإنّهم يُرحَمون", "متّى ٥: ٧"),
    Verse("في بيت أبي منازلُ كثيرة", "يوحنّا ١٤: ٢"),
]


