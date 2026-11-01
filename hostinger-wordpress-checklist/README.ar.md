# قائمة إطلاق WordPress على Hostinger

راجع الخطة الحالية في Hostinger: إجمالي الدفع ومدة الالتزام والتجديد والتخزين وحدود الموارد والنسخ الاحتياطي وميزة staging إن احتجتها. لا يتضمن هذا المجلد شراء استضافة أو تثبيت WordPress تلقائياً.

1. حدد نطاقاً وهدف تثبيت جديداً أو بيئة staging؛ لا تعِد التثبيت فوق موقع يعمل.
2. من Websites اختر إنشاء موقع WordPress أو افتح مثبت WordPress في لوحة الموقع الصحيح. راجع المسار وقاعدة البيانات وحساب المدير قبل التأكيد.
3. أكمل إعداد النطاق وHTTPS ثم افحص لوحة WordPress واللغة والقالب والروابط الدائمة.
4. افحص مسودة في الهاتف قبل النشر. عند الإطلاق راجع Settings → Reading → Search engine visibility.
5. تحقق من النسخ الاحتياطي وجدوله داخل حسابك، واحتفظ بنسخة خارجية واختبر استعادة على نسخة منفصلة.

فاحص الصفحة التالي يستخدم Python 3.11+ والمكتبة القياسية فقط. افتح PowerShell في هذا المجلد واستبدل العنوان بموقعك العام:

```powershell
python check.py --site https://techmouad.com/
```

يقرأ طلب HTTPS واحداً مع إعادة توجيه إلى عناوين عامة فقط، ويعرض حالة HTTP ووجود عنوان وcanonical وتوجيه noindex صريحاً إن وجده. لا يدخل حساب Hostinger ولا يغير الموقع ولا يتحقق من النسخ الاحتياطية أو Search Console. غياب noindex لا يثبت أن Google فهرس الصفحة. التشغيل المحلي ليس مراقبة مستمرة عندما يكون الكمبيوتر مغلقاً.

المصادر: [إعداد WordPress](https://www.hostinger.com/tutorials/how-to-install-wordpress)، [مقارنة الخطط](https://www.hostinger.com/wordpress-hosting)، [إعدادات القراءة](https://wordpress.org/documentation/article/settings-reading-screen/).
