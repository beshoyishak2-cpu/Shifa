-- Verified doctor directory and stricter prescription confidentiality.
-- Errand dispatch and pharmacy review functions are in migration 008.

create table if not exists public.medical_providers (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  specialty text not null,
  address text not null,
  phone text not null,
  working_days text,
  is_active boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (length(trim(full_name)) between 2 and 160),
  check (length(trim(specialty)) between 2 and 120),
  check (length(trim(address)) between 3 and 300),
  check (length(trim(phone)) between 7 and 30)
);
alter table public.medical_providers enable row level security;
drop policy if exists "active medical providers public" on public.medical_providers;
drop policy if exists "admin manages medical providers" on public.medical_providers;
create policy "active medical providers public"
on public.medical_providers for select
using (is_active = true or public.shifa_is_admin());
create policy "admin manages medical providers"
on public.medical_providers for all to authenticated
using (public.shifa_is_admin())
with check (public.shifa_is_admin());
grant select on public.medical_providers to anon, authenticated;
grant insert, update, delete on public.medical_providers to authenticated;

drop trigger if exists medical_providers_set_updated_at on public.medical_providers;
create trigger medical_providers_set_updated_at
before update on public.medical_providers
for each row execute function public.shifa_set_updated_at();

-- A prescription can be submitted only to an active pharmacy.
drop policy if exists "customer submits own prescription" on public.pharmacy_prescriptions;
create policy "customer submits own prescription"
on public.pharmacy_prescriptions for insert to authenticated
with check (
  customer_id = auth.uid()
  and status = 'submitted'
  and pharmacy_merchant_id is not null
  and exists (
    select 1 from public.merchants m
    where m.id = pharmacy_merchant_id
      and m.service_type = 'pharmacy'
      and m.is_active = true
  )
);

-- The customer, admin, or a member of the assigned pharmacy whose licence
-- was verified by an administrator can read the prescription metadata.
drop policy if exists "prescriptions visible to owner pharmacist or admin" on public.pharmacy_prescriptions;
drop policy if exists "prescriptions visible to owner verified pharmacy or admin" on public.pharmacy_prescriptions;
create policy "prescriptions visible to owner verified pharmacy or admin"
on public.pharmacy_prescriptions for select to authenticated
using (
  customer_id = auth.uid()
  or public.shifa_is_admin()
  or (
    pharmacy_merchant_id is not null
    and public.shifa_is_merchant_member(pharmacy_merchant_id)
    and exists (
      select 1 from public.merchants m
      where m.id = pharmacy_merchant_id
        and m.service_type = 'pharmacy'
        and m.pharmacist_verified = true
    )
  )
);

-- Apply the same gate to signed URLs and direct Storage reads.
drop policy if exists "prescription owner pharmacist admin reads" on storage.objects;
drop policy if exists "prescription owner verified pharmacy admin reads" on storage.objects;
create policy "prescription owner verified pharmacy admin reads"
on storage.objects for select to authenticated
using (
  bucket_id = 'prescriptions'
  and (
    (storage.foldername(name))[1] = auth.uid()::text
    or public.shifa_is_admin()
    or exists (
      select 1
      from public.pharmacy_prescriptions pp
      join public.merchants m on m.id = pp.pharmacy_merchant_id
      where pp.storage_path = storage.objects.name
        and m.service_type = 'pharmacy'
        and m.pharmacist_verified = true
        and public.shifa_is_merchant_member(m.id)
    )
  )
);

create index if not exists medical_providers_active_name_idx
on public.medical_providers(is_active, full_name);
