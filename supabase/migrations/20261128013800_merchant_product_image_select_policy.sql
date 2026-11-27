-- Allow authenticated merchant members to select their own objects for Storage upsert.
-- The bucket remains public for storefront image delivery; this policy does not expose private buckets.
drop policy if exists "merchant reads product images" on storage.objects;
create policy "merchant reads product images"
on storage.objects for select to authenticated
using (
  bucket_id = 'product-images'
  and (
    public.shifa_is_admin()
    or public.shifa_is_merchant_member(((storage.foldername(name))[1])::uuid)
  )
);
