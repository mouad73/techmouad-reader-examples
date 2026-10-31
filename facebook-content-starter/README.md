# محضر منشورات فيسبوك بسيط

لإعداد النشر الاختياري على صفحتك وتحديد Page ID وApp ID وApp Secret وPage access token، اتبع [دليل إعداد Meta بالصور](META-SETUP.ar.md). يتضمن `publish.py` طلب نشر حقيقياً، ويعمل بمعاينة محلية حتى تختار النشر صراحة.

مثال مستقل لإنشاء حزمة محلية: صورة PNG عربية 1080×1350، نص، مصادر، معاينة HTML وقائمة مراجعة. لا يحتاج `build.py` توكنات ولا يستدعي أي API للذكاء الاصطناعي. بعد مراجعة مادة حقيقية، تستطيع النشر يدوياً أو تشغيل `publish.py` مع إعدادات صفحتك وخيار النشر الصريح.

## التشغيل

من هذا المجلد، مع Python 3.11+:

على Windows، من PowerShell داخل هذا المجلد:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe build.py --input story.example.json --out output/demo
```

على Linux/macOS استخدم `.venv/bin/python` بدلاً من `.venv\Scripts\python.exe` بعد إنشاء البيئة. لا يلزم تفعيل البيئة إذا استخدمت مسار مفسرها مباشرة. استخدم المفسر نفسه في بقية أوامر الدليل.

افتح `output/demo/preview.html`. هذه بيانات ومصادر تجريبية؛ لا تنشرها كخبر. يحتاج الرسم خطاً عربياً وPillow مع دعم libraqm. يمكن تحديد الخط:

```sh
.venv\Scripts\python.exe build.py --input story.example.json --out output/demo-font --font /path/to/arabic-font.ttf
```

## مادة حقيقية

1. انسخ `prompts/01-research.ar.txt` إلى مساعدك، وحدد موضوعك. افتح المصادر الأصلية بنفسك.
2. استخدم `02-write.ar.txt` مع البحث الذي راجعته، واحفظ JSON الناتج باسم `story.json`.
3. راجع العنوان والنص والمصادر. اجعل `reviewed` يساوي `true` بعد المراجعة فقط، مع `demo=false`.
4. شغّل `.venv\Scripts\python.exe build.py --input story.json --out output/my-post` على Windows، أو مسار مفسر البيئة الموافق لنظامك.
5. افتح المعاينة، ثم انشر يدوياً أو اتبع أوامر `publish.py` في دليل Meta. بيانات العرض `demo=true` مرفوضة في الناشر.

التحقق من اختلاف نطاقين لا يثبت استقلالهما أو صحة الخبر. لا يعيد السكربت الكتابة فوق مجلد موجود. `state.sqlite3` سجل للحزمة المحلية. يحتفظ الناشر بسجل نشر مشترك منفصل وبإيصال عند نجاح الطلب. أمر بناء واحد ينشئ حزمة واحدة؛ لا توجد مهمة يومية سحابية مدمجة أو توليد آلي بالذكاء الاصطناعي. أجريت اختبارات محلية ومحاكاة API فقط؛ لم يُنشر منشور حي ضمن الاختبار.
