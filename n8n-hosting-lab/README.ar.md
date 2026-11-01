# مختبر n8n مصغر ودليل Hostinger VPS

هذا مختبر تعلم منفصل عن موقع WordPress. يتطلب Docker يعمل بالفعل؛ على Windows شغل Docker Desktop بواجهة Linux/WSL2 أولاً. لا يحتوي مفاتيح أو اتصالات أو جدولة. لا يثبت هذا المختبر جاهزية إنتاجية أو نشر Hostinger الفعلي، ولا يضم n8n Assistant أو بيئة sandbox كاملة.

## تجربة محلية في PowerShell

```powershell
docker version
docker run -d --name n8n-reader-lab -p 127.0.0.1:15678:5678 -e GENERIC_TIMEZONE=UTC -e TZ=UTC -e N8N_DIAGNOSTICS_ENABLED=false -v n8n_reader_lab:/home/node/.n8n docker.n8n.io/n8nio/n8n:2.45.7
```

انتظر اكتمال بدء الخدمة وترحيل قاعدة البيانات. هذا ليس أمراً لتشغيل خدمة عامة على الإنترنت. عند ظهور خطأ اسم مستخدم سابقاً افحص الحاوية الموجودة بدلاً من حذفها. افحص الصحة ثم افتح العنوان المحلي:

```powershell
Invoke-RestMethod http://localhost:15678/healthz
Start-Process http://localhost:15678
```

أكمل حساب المالك داخل نسختك، ثم أنشئ workflow واستورد `manual-workflow.json` من خيار الاستيراد في المحرر. يربط الملف Manual Trigger بعقدة Edit Fields لإخراج `message=TechMouad reader test`. راجع العقد واضغط التنفيذ اليدوي. القالب غير نشط ولا يرسل رسائل أو ينشر محتوى؛ اختبره قبل إضافة أي اعتماد أو مشغّل مجدول.

## التوقف والنسخ الاحتياطي

```powershell
docker stop n8n-reader-lab
docker cp n8n-reader-lab:/home/node/.n8n ./n8n-backup
docker start n8n-reader-lab
```

اختر اسم نسخ جديداً لكل تاريخ، ولا تخلط نسخة قديمة بجديدة داخل المجلد نفسه. أبق مجلد النسخ خاصاً وخارج GitHub: يضم قاعدة SQLite ومفتاح تشفير الاعتمادات وبيانات الحساب. هذا نسخ لمختبر SQLite المتوقف؛ لا يغني عن نسخ PostgreSQL أو التخزين الخارجي في التركيبات التي تستخدمهما. لا تنسخ SQLite أثناء الكتابة. اختبر الاستعادة إلى مختبر منفصل بالإصدار نفسه قبل الاعتماد على النسخ.

## مسار Hostinger

استخدم VPS جديداً مخصصاً أو خادماً فارغاً تملك نسخه؛ قالب نظام التشغيل يمسح الملفات الموجودة. من قسم VPS افتح إدارة الخادم، ثم OS & Panel → Operating System وابحث عن n8n. راجع تحذير تغيير النظام بنفسك قبل المتابعة. بعد الإعداد افتح Manage App، وأكمل حساب المالك وتهيئة النطاق وHTTPS كما في التوثيق الحالي للخطة والقالب. لا تستخدم إعدادات N8N_BASIC_AUTH القديمة ولا تعطل secure cookies لحل مشكلة HTTPS.

المثال المحلي ذو المنفذ المحلي لا يكوّن DNS أو TLS أو reverse proxy. يتطلب نشر الويب الحقيقي هذه الخطوات وإعداد WEBHOOK_URL صحيحاً والتحقق من webhook منفصل. لا تفتح منفذ المحرر الخام للعامة. إعداد Assistant/sandbox الكامل الحالي مختلف وأثقل؛ توثيقه يطلب 4GB RAM و2vCPU على الأقل، وليس جزءاً من هذا المختبر.

المصادر: [Hostinger VPS](https://www.hostinger.com/tutorials/how-to-self-host-n8n/)، [Compose الحالي](https://docs.n8n.io/deploy/host-n8n/install-options/install-using-docker-compose.md)، [النسخ والاستعادة](https://docs.n8n.io/deploy/host-n8n/keep-n8n-running/backup-and-restore.md).
