# Mastrix Media — إعلان Reels (30 ثانية)

الفيديو مبني بالكود: كل فريم هو `renderAt(t)` داخل `scene/index.html`، بيتصوّر بـChromium وبيتجمّع بـffmpeg.
أي تعديل على النص أو الأرقام أو الألوان بيطلع بفيديو جديد بدقائق.

## الملفات الجاهزة
- `out/mastrix_reel_A.mp4` — هوك «اللايكات ما بتدفع إيجار.»
- `out/mastrix_reel_B.mp4` — هوك «دفعت على إعلانات… وما رنّ ولا تلفون؟»
- `out/mastrix_reel_C.mp4` — هوك «صفحتك حلوة. بس مين بيشتري؟»
- `out/storyboard.png` — الفريمات الأساسية

## قبل النشر — لازم تتعدّل
| شو | وين | ليش |
|---|---|---|
| أرقام جدول النتائج | `config.json` → `ledger.rows` | الأرقام الحالية توضيحية. حط أرقام عميل حقيقي وخلّي `placeholder: false` |
| عدد العملاء بالشهر | `config.json` → `seats` | الدواير (8، منهم 6 محجوزين) لازم تطابق الحقيقة |
| اللوغو | `scene/index.html` → `M_PATTERN` | الـM المبني من النقاط مؤقت لحد ما يوصل لوغو الشركة |

## إعادة الإنتاج
```bash
npm install
pip install scipy numpy
python3 -I scripts/build_audio.py      # تقطيع الصوت + مؤثرات + timeline لكل نسخة
python3 -I scripts/normalize.py A B C  # -14 LUFS
node scripts/render.mjs video A        # أو B / C
node scripts/render.mjs stills A 0,5.6,16.9 --guides   # فريمات مع مناطق Reels الآمنة
```

## المواصفات
1080×1920، 30fps، H.264 High، AAC 48kHz، −14 LUFS. كل النصوص ضمن المنطقة الآمنة لـReels
(بعيد عن أعلى 14% وأسفل 35%) وضمن قصّة 4:5 بالفيد.

## اللوغوهات (20 اتجاه)
- `logos/out/overview.png`: كل الـ20 بنظرة وحدة
- `logos/out/sheet_1..5.png`: كل اتجاه لحاله، مع اختبار صورة البروفايل والأيقونة الصغيرة والخلفية الفاتحة
- `logos/out/svg/NN.svg`: كل رمز vector
- الرموز مرسومة بالكود بـ`logos/marks.js`. لوغو 17 مبني من خط Amiri نفسه
  (`scripts/ijam_svg.py`)، والنقاط مفصولة عن الحروف بشكل vector حقيقي.

```bash
python3 -I scripts/ijam_svg.py   # يحتاج: pip install uharfbuzz fonttools brotli
node logos/render.mjs
```

## الصوت
التعليق الصوتي: ElevenLabs، صوت «Mohammad – Warm Arabic Commercial» (لهجة شامية)، take 1.
الموسيقى والمؤثرات مولّدة بالكود (`build_audio.py`) — بدون حقوق ملكية لطرف تالت.
