# شفاء | Shifa — Android + iOS starter

مشروع موحد بـ React + Vite + Capacitor ليعمل كتطبيق Android وiPhone، مع واجهة RTL مبدئية لمنظومة الصيدليات والتوصيل في ملوي، المنيا.

## الحالة الحالية بوضوح
- واجهات العميل والصيدلية والمندوب والإدارة موجودة كـ **نموذج تفاعلي تجريبي**.
- تمت إضافة إعداد Capacitor ومنصتي Android وiOS، وملفات تكامل الكاميرا والموقع والمشاركة، وعميل Supabase اختياري.
- تمت إضافة مخطط SQL أولي للجداول وسياسات وصول أساسية.
- **لا يوجد خادم متصل افتراضيًا**: المنتجات والطلبات والأرقام المعروضة تجريبية. لا توجد مدفوعات أو توصيل حي أو OCR/ذكاء اصطناعي فعلي أو إشعارات خادمية جاهزة للإنتاج.
- يجب استكمال سياسات RLS واختبارات الأمان وتدفقات مراجعة الصيدلي قبل إدخال بيانات صحية حقيقية.

## المتطلبات
- Node.js 20 أو أحدث وnpm.
- Android: Android Studio + Android SDK.
- iOS: جهاز Mac + Xcode. لا يمكن إنشاء أو توقيع IPA من Windows أو Linux.

## تشغيل الويب
```bash
npm install
npm run dev
```

## إعداد Android
```bash
npm install
npx cap add android
npm run cap:sync
npm run android:open
```
من Android Studio اختر جهازًا أو محاكيًا ثم Run. لإنتاج APK/AAB استخدم Build > Generate Signed Bundle / APK، وأضف مفاتيح التوقيع بأمان.

## إعداد iOS (على Mac فقط)
```bash
npm install
npx cap add ios
npm run cap:sync
npm run ios:open
```
افتح المشروع في Xcode، اضبط Bundle Identifier وSigning Team وCapabilities، ثم شغّله على محاكي أو iPhone. التوزيع يحتاج حساب Apple Developer وشهادات/ملفات توقيع.

## ربط Supabase
1. أنشئ مشروع Supabase.
2. انسخ `.env.example` إلى `.env` وضع `Project URL` و`anon/public key`.
3. شغّل `supabase/schema.sql` من SQL Editor بعد مراجعته.
4. أنشئ Storage buckets خاصة للروشتات ومستندات التحقق، مع سياسات تمنع الوصول العام.
5. نفّذ وظائف خادمية موثوقة لإنشاء الطلبات وحساب السعر والتحقق من الكوبونات وتغيير الحالات واعتماد الصيدليات والمندوبين.

لا تضع `service_role` key داخل التطبيق. لا تجعل الذكاء الاصطناعي يقرر صرف دواء أو جرعة أو بديل تلقائيًا؛ كل وصفة وبديل يحتاج مراجعة صيدلي مرخص.

## مكونات Capacitor المضافة
Camera, Geolocation, Share, Push Notifications, Haptics, Status Bar, Splash Screen. اطلب الأذونات وقت الحاجة واشرح للمستخدم سبب استخدامها.

## الخطوات المطلوبة قبل الإطلاق
- مصادقة هاتف/OTP وإدارة جلسات وأدوار موثوقة.
- لوحات حقيقية مع صلاحيات منفصلة للصيدليات والمندوبين والإدارة.
- مخزون وأسعار لحظية وطلب متعدد الصيدليات أو تحديد صيدلية واحدة لكل طلب.
- بوابة دفع مرخصة أو الدفع عند الاستلام وتسويات المندوبين.
- OCR للروشتة مع موافقة صيدلي، وتخزين طبي خاص ومشفر وسياسة احتفاظ.
- خرائط ومسارات وإشعارات Push من الخادم.
- اختبارات Android/iOS، اختبارات اختراق ومراجعة قانونية وتشغيلية داخل مصر.

## بناء تلقائي عبر GitHub Actions
يوجد workflow في `.github/workflows/mobile-build.yml`. بعد رفع المشروع إلى مستودع GitHub على فرع `main`، سيبني APK تجريبيًا لأندرويد ونسخة iOS للمحاكي (وليست IPA صالحة للنشر). افتح تبويب Actions لتنزيل الـ artifacts. نشر iOS يحتاج توقيعًا وحساب Apple Developer.
