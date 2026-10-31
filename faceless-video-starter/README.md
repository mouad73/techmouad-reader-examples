# فيديو نصي عمودي دون ظهور

Python 3.11+، وFFmpeg مثبت مع دعم libass/subtitles وخط يدعم العربية. لا توجد مكتبات Python إضافية. المخرجات فيديو صامت 1080×1920؛ لا توليد صور أو أصوات أو رفع إلى YouTube/Facebook.

افتح الطرفية داخل هذا المجلد، وتحقق أولاً من ظهور إصدار عبر `ffmpeg -version` ومن توفر مرشح `subtitles` ضمن `ffmpeg -filters`. إذا لم يُعثر على الأمر، ثبّت FFmpeg من [المصدر الرسمي](https://ffmpeg.org/download.html) واجعله متاحاً في PATH، ثم افتح طرفية جديدة قبل تجربة الرسم. وجود Python وحده لا يكفي لإنشاء MP4.

```sh
python -m venv .venv
.venv\Scripts\python.exe render.py --check
.venv\Scripts\python.exe render.py --input scenes.example.json --out output/demo --render
```

هذه أوامر PowerShell على Windows؛ لا يلزم Activate.ps1 أو cmd.exe. على Linux/macOS استبدل مسار المفسر بـ`.venv/bin/python`. لا تحتاج تثبيت حزم pip لهذا المثال. افحص المتطلبات بـ`--check` قبل إنشاء مجلد الناتج. يتحقق من `subtitles` و`libx264` ويشرح النقص قبل إنشاء ملفات. استخدم مجلداً جديداً في كل تشغيل؛ لا يستبدل البرنامج مجلداً موجوداً.

افتح `output/demo/video.mp4` وافحص اتجاه العربية قبل الاستخدام. إذا أردت ملف الترجمة فقط، احذف `--render`.

انسخ `prompts/script.ar.txt` إلى مساعدك مع موضوع موثق. راجع الناتج واحفظه في `scenes.json` ثم مرره إلى `--input`. ملف `prompts/visual.en.txt` اختياري ولا يستدعي API. لا تُضمّن أسراراً في البرومبتات. لا يشغّل المثال خدمة سحابية ولا ينشر تلقائياً؛ الرفع يدوي بعد المراجعة.

يجب أن يكون JSON كائناً يحتوي `scenes` كمصفوفة، وكل مشهد كائناً بـ`text` النصي و`seconds` الرقمي؛ لا تستخدم true/false أو أرقاماً بين علامات اقتباس للمدة. تُرفض المدخلات الخاطئة برسالة قصيرة قبل إنشاء الحزمة.
