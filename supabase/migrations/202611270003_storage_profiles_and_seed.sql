-- Shifa operational baseline: profile bootstrap, timestamps and private file storage.
-- Apply after 202611270001_initial_schema.sql and 202611270002_checkout_security.sql.

-- Create a profile automatically for every newly registered auth user.
create or replace function public.shifa_handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, phone)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'full_name', ''),
    nullif(new.phone, '')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists shifa_on_auth_user_created on auth.users;
create trigger shifa_on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.shifa_handle_new_user();

-- Keep updated_at consistent on mutable records.
create or replace function public.shifa_set_updated_at()
returns trigger language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at before update on public.profiles
for each row execute procedure public.shifa_set_updated_at();

drop trigger if exists products_set_updated_at on public.products;
create trigger products_set_updated_at before update on public.products
for each row execute procedure public.shifa_set_updated_at();

drop trigger if exists orders_set_updated_at on public.orders;
create trigger orders_set_updated_at before update on public.orders
for each row execute procedure public.shifa_set_updated_at();

-- Storage buckets: prescription and partner documents are private.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('prescriptions', 'prescriptions', false, 10485760,
   array['image/jpeg','image/png','image/webp','application/pdf']),
  ('partner-documents', 'partner-documents', false, 10485760,
   array['image/jpeg','image/png','application/pdf']),
  ('product-images', 'product-images', true, 5242880,
   array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

-- A customer stores prescription files only in their own UUID folder.
drop policy if exists "customer uploads own prescriptions" on storage.objects;
create policy "customer uploads own prescriptions"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'prescriptions'
  and (storage.foldername(name))[1] = auth.uid()::text
);

-- Customers can read their own files; the assigned pharmacy team and admins
-- can read only files associated with their prescription records.
drop policy if exists "prescription owner pharmacist admin reads" on storage.objects;
create policy "prescription owner pharmacist admin reads"
on storage.objects for select to authenticated
using (
  bucket_id = 'prescriptions'
  and (
    (storage.foldername(name))[1] = auth.uid()::text
    or public.shifa_is_admin()
    or exists (
      select 1 from public.pharmacy_prescriptions pp
      where pp.storage_path = storage.objects.name
        and pp.pharmacy_merchant_id is not null
        and public.shifa_is_merchant_member(pp.pharmacy_merchant_id)
    )
  )
);

-- Private partner documents are scoped to a merchant UUID folder.
drop policy if exists "merchant uploads own partner documents" on storage.objects;
create policy "merchant uploads own partner documents"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'partner-documents'
  and (
    public.shifa_is_admin()
    or public.shifa_is_merchant_member(((storage.foldername(name))[1])::uuid)
  )
);

drop policy if exists "merchant team reads own partner documents" on storage.objects;
create policy "merchant team reads own partner documents"
on storage.objects for select to authenticated
using (
  bucket_id = 'partner-documents'
  and (
    public.shifa_is_admin()
    or public.shifa_is_merchant_member(((storage.foldername(name))[1])::uuid)
  )
);

-- Product images are intentionally public for storefront rendering.
drop policy if exists "merchant uploads product images" on storage.objects;
create policy "merchant uploads product images"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'product-images'
  and (
    public.shifa_is_admin()
    or public.shifa_is_merchant_member(((storage.foldername(name))[1])::uuid)
  )
);

drop policy if exists "merchant updates product images" on storage.objects;
create policy "merchant updates product images"
on storage.objects for update to authenticated
using (
  bucket_id = 'product-images'
  and (
    public.shifa_is_admin()
    or public.shifa_is_merchant_member(((storage.foldername(name))[1])::uuid)
  )
)
with check (
  bucket_id = 'product-images'
  and (
    public.shifa_is_admin()
    or public.shifa_is_merchant_member(((storage.foldername(name))[1])::uuid)
  )
);

drop policy if exists "merchant deletes product images" on storage.objects;
create policy "merchant deletes product images"
on storage.objects for delete to authenticated
using (
  bucket_id = 'product-images'
  and (
    public.shifa_is_admin()
    or public.shifa_is_merchant_member(((storage.foldername(name))[1])::uuid)
  )
);

-- Initial local categories for the Mallawi launch. Safe to re-run.
insert into public.categories (name_ar, slug, sort_order)
values
  ('مطاعم', 'restaurants', 1),
  ('كافيهات', 'cafes', 2),
  ('سوبر ماركت', 'supermarkets', 3),
  ('خضار وفاكهة', 'vegetables-fruits', 4),
  ('صيدليات', 'pharmacies', 5),
  ('مشاوير خاصة', 'private-rides', 6)
on conflict (slug) do nothing;
