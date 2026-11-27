# سريع | Saree — Local Super App for Mallawi, Minya

Arabic RTL local-services and delivery app for Mallawi and nearby villages. Built with React, TypeScript, Vite, Capacitor and Supabase.

## Live backend status

The connected Supabase project is active and migrations through **022** have been applied.

The operational backend now includes:
- Partner applications for merchants and couriers, private document uploads, admin approval/rejection and account activation.
- Private wallet/Instapay payment receipts, admin verification, payment feature flags and configurable transfer phone.
- Wallet account balances and an append-only transaction ledger with server-side credit/debit operations.
- First-come-first-served courier assignment using a row-locked database function; pre-pickup release returns the order to the shared queue and records the reason.
- Courier delivery commissions, settlement accounts, settlement receipt submission and admin settlement confirmation.
- A scheduled pg_cron job that checks overdue/max-debt couriers every minute and applies settlement locks; locked couriers are removed from dispatch and become available again after admin confirms settlement.
- A courier is paused while a submitted settlement receipt awaits admin review.
- RLS enabled on all public tables; operational tables are subscribed to Supabase Realtime.

The new SareeOperationsPanel is mounted by the Android build workflow and provides customer partner/payment actions, courier dispatch/settlement actions and admin review/settings screens.

## Important launch limitations

A successful build proves compilation and packaging only. It does not prove the full system is production-ready. Before accepting real orders:
- Run end-to-end tests using separate customer, merchant, courier and admin accounts.
- Test checkout/payment receipt submission, rejected-receipt retry, wallet partial/full payment, dispatch races, courier cancellations, delivery commissions and settlement unlock.
- Verify every Storage bucket policy and private signed-file access.
- Confirm local address coverage, map accuracy, prescription review by licensed pharmacists and the pharmacy voice-note workflow.
- Keep the agreed phone/password login without SMS OTP. Because the current phone number is mapped to an internal non-deliverable email identity, it does not prove phone ownership; document this limitation and manually verify partner/courier contact details before activation. Configure push notifications, monitoring, backups, privacy/terms and customer support.
- Complete physical-device testing on Android and iOS. The iOS workflow currently produces a Simulator build, not a signed installable IPA.

Phone/password login currently maps Egyptian phone numbers to an internal non-deliverable email identity. It does not prove phone ownership and is not a substitute for production OTP verification. The UI enforces a minimum of 8 password characters; leaked-password protection still needs to be enabled in Supabase Auth settings before launch.

## Supabase

Project URL: https://qfweejmqooojsedsypen.supabase.co

For a fresh environment, apply every SQL file in supabase/migrations/ in filename order. The connected project currently has 22 applied migrations. Never expose a Supabase service-role or secret key in the mobile app or public repository; the app uses a publishable key and relies on RLS and server-side RPC authorization.

## Local development

Requires Node.js 20+ and npm.

```bash
npm install
npm run dev
npm test
npm run build
```

## Android and iOS

GitHub Actions builds the Android Debug APK. The Android workflow upgrades its Capacitor packages to v8 (Android 16 / API 36), assigns a unique versionCode, and can produce a signed Release APK plus Google Play AAB once the permanent Android upload keystore is stored as GitHub Actions secrets. The iOS workflow currently builds an iOS Simulator app; a signed IPA requires Apple Developer certificates and provisioning profiles.

## Operational defaults

- Service launch area: Mallawi, Minya.
- Electronic transfer phone: 01221236118.
- Mobile wallet and InstaPay: enabled by default; each can be disabled in admin settings.
- Courier commission: 0 by default (admin must set the actual business rate before launch).
- Daily settlement cutoff: 22:00 Egypt time.
- Maximum courier debt: EGP 500 by default.
- Automatic settlement lock: enabled by default.
