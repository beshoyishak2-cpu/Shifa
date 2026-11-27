# تجهيز إصدار Android Release لتطبيق سريع

تم إعداد Workflow لبناء Debug APK وRelease APK وAndroid App Bundle (AAB) موقّع. يقوم مسار Android بترقية حزم Capacitor إلى الإصدار 8 المتوافق مع Android 16 / API 36، ويولّد رقم إصدار فريدًا لكل تشغيل. لن يُنشأ إصدار Release/AAB قبل توفير مفتاح توقيع دائم؛ هذا مقصود حتى لا يتغير مفتاح التطبيق بين التحديثات.

## 1) إنشاء مفتاح التوقيع مرة واحدة

على جهاز موثوق مثبت عليه Java JDK، نفّذ:

```bash
keytool -genkeypair -v -keystore saree3-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias saree3
```

احتفظ بملف `saree3-release.jks` وكلمات المرور في مكان آمن مع نسخة احتياطية. لا ترفع ملف المفتاح إلى GitHub ولا ترسله في محادثة.

## 2) إضافة GitHub Actions Secrets

افتح المستودع ثم Settings → Secrets and variables → Actions → New repository secret، وأضف:

- `ANDROID_KEYSTORE_BASE64`: محتوى ملف المفتاح بعد تحويله إلى Base64 كسطر واحد.
- `ANDROID_KEYSTORE_PASSWORD`: كلمة مرور ملف المفتاح.
- `ANDROID_KEY_ALIAS`: القيمة `saree3` إذا استخدمت الأمر أعلاه.
- `ANDROID_KEY_PASSWORD`: كلمة مرور المفتاح.

لتحويل الملف إلى Base64:

Linux/macOS:
```bash
base64 -w 0 saree3-release.jks
```

Windows PowerShell:
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("saree3-release.jks"))
```

انسخ الناتج مباشرة إلى Secret ولا تضعه في ملفات المشروع.

## 3) تشغيل البناء

بعد حفظ الأسرار، افتح Actions → Saree3 Android build → Run workflow. سينتج البناء ملف Debug للاختبار، وملف Release APK موقّع، وملف Android App Bundle بصيغة AAB موقّع للنشر على Google Play إذا كانت الأسرار الأربعة موجودة. يضبط Workflow رقم versionCode فريدًا تلقائيًا من رقم تشغيل GitHub Actions ويستهدف API 36 عبر Capacitor 8.

## تنبيه مهم

- لا تفقد ملف المفتاح أو كلمات مروره؛ ستحتاج المفتاح نفسه لتحديث التطبيق المنشور على Google Play.
- ملف Debug ليس مناسبًا للنشر التجاري.
- ملف AAB هو الملف الذي ترفعه إلى Google Play Console، بينما APK الموقّع مناسب للتثبيت والاختبار المباشر.
- تجهيز Google Play يتطلب مراجعة بيانات التطبيق وسياسة الخصوصية وتصنيف المحتوى واختبار النسخة النهائية.
- iOS يحتاج شهادة توزيع وملف Provisioning Profile وحساب Apple Developer؛ بناء المحاكي الحالي ليس IPA للنشر.
