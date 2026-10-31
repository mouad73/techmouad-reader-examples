# فيديو نصي عمودي دون ظهور

Python 3.11+، وFFmpeg مثبت مع دعم libass/subtitles وخط يدعم العربية. لا توجد مكتبات Python إضافية. المخرجات فيديو صامت 1080×1920؛ لا توليد صور أو أصوات أو رفع إلى YouTube/Facebook.

افتح الطرفية داخل هذا المجلد، وتحقق أولاً من ظهور إصدار عبر `ffmpeg -version` ومن توفر مرشح `subtitles` ضمن `ffmpeg -filters`. إذا لم يُعثر على الأمر، ثبّت FFmpeg من [المصدر الرسمي](https://ffmpeg.org/download.html) واجعله متاحاً في PATH، ثم افتح طرفية جديدة قبل تجربة الرسم. وجود Python وحده لا يكفي لإنشاء MP4.

```sh
python render.py --input scenes.example.json --out output/demo --render
```

افتح `output/demo/video.mp4` وافحص اتجاه العربية قبل الاستخدام. إذا أردت ملف الترجمة فقط، احذف `--render`.

انسخ `prompts/script.ar.txt` إلى مساعدك مع موضوع موثق. راجع الناتج واحفظه في `scenes.json` ثم مرره إلى `--input`. ملف `prompts/visual.en.txt` اختياري ولا يستدعي API. لا تُضمّن أسراراً في البرومبتات. لا يشغّل المثال خدمة سحابية ولا ينشر تلقائياً؛ الرفع يدوي بعد المراجعة.
