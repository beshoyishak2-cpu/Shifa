-- Customer-facing pharmacy stock lookup. Only currently available, non-expired, dated batches are counted.
create or replace function public.saree_search_pharmacy_stock(
 p_search text,p_area text default null
) returns table(
 product_id uuid,product_name text,pharmacy_name text,area_name text,
 unit_price numeric,available_quantity bigint,nearest_expiry date
) language sql stable security definer set search_path=''
as $$
 select p.id,p.name,m.name,
   coalesce(nullif(trim(p_area),''),(select min(z.area_name) from public.saree_delivery_zones z where z.merchant_id=m.id and z.is_active)),
   p.price,
   sum(b.quantity)::bigint,
   min(b.expiry_date)
 from public.products p
 join public.merchants m on m.id=p.merchant_id
 join public.product_inventory_batches b on b.product_id=p.id and b.merchant_id=m.id
 where m.is_active=true and m.service_type='pharmacy' and p.is_available=true
   and b.quantity>0 and b.expiry_date is not null and b.expiry_date>=current_date
   and length(trim(coalesce(p_search,'')))>=2
   and p.name ilike '%'||left(trim(p_search),100)||'%'
   and (nullif(trim(p_area),'') is null or exists(
     select 1 from public.saree_delivery_zones z where z.merchant_id=m.id
      and z.is_active=true and z.area_name ilike trim(p_area)
   ))
 group by p.id,p.name,m.id,m.name,p.price
 order by p.name,m.name
 limit 50
$$;
revoke all on function public.saree_search_pharmacy_stock(text,text) from public;
grant execute on function public.saree_search_pharmacy_stock(text,text) to anon,authenticated;
