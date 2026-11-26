# شفاء | Shifa — Local Super App MVP for Mallawi, Minya

Arabic RTL local services and delivery MVP for Mallawi, Minya. Built with React, TypeScript, Vite and Capacitor.

## Current status
- Android Debug APK builds successfully in GitHub Actions.
- iOS Simulator app builds successfully in GitHub Actions. This is not an installable iPhone IPA.
- Supabase project URL and publishable key are configured in the CI build environment.
- Database migrations are committed in `supabase/migrations/` but have **not** been executed against the live Supabase project from this repository.
- The UI is still an MVP/demo in important areas. Do not treat a successful mobile build as proof that live orders, auth, uploads, notifications or tracking are operational.

## Supabase setup
Project URL: `https://qfweejmqooojsedsypen.supabase.co`

Apply the SQL files in this exact order using Supabase Dashboard → SQL Editor:
1. `supabase/migrations/202611270001_initial_schema.sql`
2. `supabase/migrations/202611270002_checkout_security.sql`
3. `supabase/migrations/202611270003_storage_profiles_and_seed.sql`

Review each script before running it. The migrations create the baseline tables, RLS policies, trusted checkout RPC, profile bootstrap, private prescription/partner-document buckets and starter categories. After applying, test with separate customer, merchant, courier and admin accounts. Never put the Supabase `service_role` or secret key in the mobile app or a public repository.

The browser/mobile publishable key is public by design. Data protection depends on correctly configured RLS, Storage policies and server-side authorization. Phone OTP/SMS, admin provisioning, push notifications, dispatch, payment providers and production monitoring still require separate setup.

## Run locally
Requires Node.js 20+ and npm.

```bash
npm install
npm run dev
```

## Android
The GitHub Actions workflow produces a **Debug APK**. Release distribution requires an Android signing key stored securely as a GitHub Actions secret and a signed release build.

## iOS
The GitHub Actions workflow produces an **iOS Simulator app** only. An installable IPA requires Apple Developer signing, certificates and provisioning profiles.

## Before real launch
- Apply and test all Supabase migrations and RLS/Storage policies.
- Complete live Supabase authentication and connect every app data flow to the backend.
- Verify merchants, pharmacies, couriers and clinic listings in Mallawi.
- Complete prescription upload/review with licensed pharmacists.
- Add secure order status transitions, dispatch and audit logs.
- Configure FCM/APNs, maps, support, privacy/terms, cancellations and backups.
- Field-test on real Android/iOS devices and monitor production errors.

**Honesty note:** This is an MVP foundation, not yet a production-ready marketplace. Successful CI builds verify packaging/compilation only; they do not prove live backend behavior.
