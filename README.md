# شفاء | Shifa — Local Super App MVP for Malawy, Minya

A single Arabic RTL application for customers, merchants/pharmacies, delivery drivers and administrators. Built with React + TypeScript + Vite + Capacitor 7, with an optional Supabase backend.

## Included in this starter
- Customer storefront with restaurants, cafes, grocery, vegetables/fruit and pharmacies.
- Single-merchant cart, quantities, order summary and cash-on-delivery checkout.
- Flexible Malawy address fields (area/village, street, landmark) and optional device GPS.
- Special courier / `ابعتلي` request form.
- Prescription image/PDF attachment and camera capture UI. Prescription files are not transmitted until a private backend upload flow is configured; a licensed pharmacist must review every prescription.
- Doctors directory UI. All names and phone numbers in the sample dataset are clearly marked as demo data and must be replaced with verified clinic data.
- Merchant inventory/product management and order status workflow demo.
- Driver availability, delivery task and earnings demo.
- Admin dashboard, partner activation controls, order overview and operational settings demo.
- Local browser persistence for the demo. The demo is not a production multi-user backend.
- Capacitor Android/iOS project configuration and a GitHub Actions build workflow.
- Supabase schema with role-safe profile trigger, RLS baseline and atomic server-side order creation RPC.

## Run locally
Requirements: Node.js 20+, npm.

```bash
npm install
npm run dev
```

The UI runs in local demo mode when Supabase credentials are absent. Demo orders and edits are saved only in the current browser/device.

## Configure Supabase
1. Create a Supabase project.
2. Copy `.env.example` to `.env.local` and set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
3. Review and run `supabase/schema.sql` in the Supabase SQL editor.
4. Create private Storage buckets named `prescriptions` and `partner-documents`; create `product-images` with an explicit public/private decision. Never expose prescription files publicly.
5. Configure phone OTP/SMS, trusted admin provisioning, Edge Functions for status transitions, dispatch, notifications, and payment verification.
6. Use short-lived signed URLs for medical files. Do not put a Supabase `service_role` key in the app.

Important: The schema includes `create_customer_order(...)`, which calculates prices and delivery from database records. Do not create orders by trusting client-provided totals. Add and test merchant/driver/admin status-transition functions before production. Review all RLS policies with a security engineer.

## Android

```bash
npm install
npx cap add android
npm run cap:sync
npx cap open android
```

Build a debug APK in Android Studio, or use the repository's GitHub Actions workflow after pushing to `main`. Release distribution requires signing keys stored as GitHub secrets or configured securely in Android Studio.

## iOS

Requires macOS and Xcode:

```bash
npm install
npx cap add ios
npm run cap:sync
npx cap open ios
```

The CI workflow builds an iOS simulator app only. An App Store IPA requires Apple Developer signing and provisioning.

## Required before real launch
- Real Supabase project, phone OTP and role provisioning.
- Verified merchant, pharmacy, driver and clinic data.
- Secure prescription upload, access controls, retention and pharmacist review.
- Server-side order state transitions, driver dispatch and audit log.
- Firebase Cloud Messaging/APNs credentials and server-side notification sender.
- Google Maps or another mapping provider key and cost controls.
- Vodafone Cash/Instapay integration through an approved provider/merchant agreement; COD remains the initial payment method.
- Terms, privacy policy, refund/cancellation policy, customer support and local operating agreements.
- Field testing in Malawy and its villages, then production monitoring/backups.

## Important honesty note
This repository starter is a feature-rich **MVP prototype**. Without backend credentials, provider accounts, verified partner data and deployment, it does not yet create real cross-device orders, process electronic payments, send push notifications, or provide live driver tracking.
