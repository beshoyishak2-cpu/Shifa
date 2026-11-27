-- Add an optional merchant storefront image URL. Existing rows remain unchanged.
alter table public.merchants
  add column if not exists image_url text;

comment on column public.merchants.image_url is
  'Optional public URL of the merchant storefront image stored in the product-images bucket.';
