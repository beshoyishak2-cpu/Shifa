-- Keep RPC wrappers invoker-safe; privileged implementation lives in the non-exposed private schema.
create or replace function private.saree_search_pharmacy_stock_impl(
 p_search text,p_area text default null
) returns table(
 product_id uuid,product_name text,pharmacy_name text,area_name text,
 unit_price numeric,available_quantity bigint,nearest_expiry date
) language sql stable security definer set search_path=''
as $$
 select p.id,p.name,m.name,
   coalesce(nullif(trim(p_area),''),(select min(z.area_name) from public.saree_delivery_zones z where z.merchant_id=m.id and z.is_active)),
   p.price,sum(b.quantity)::bigint,min(b.expiry_date)
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
revoke all on function private.saree_search_pharmacy_stock_impl(text,text) from public;
grant usage on schema private to anon,authenticated;
grant execute on function private.saree_search_pharmacy_stock_impl(text,text) to anon,authenticated;

create or replace function public.saree_search_pharmacy_stock(p_search text,p_area text default null)
returns table(product_id uuid,product_name text,pharmacy_name text,area_name text,unit_price numeric,available_quantity bigint,nearest_expiry date)
language sql stable security invoker set search_path=''
as $$ select * from private.saree_search_pharmacy_stock_impl(p_search,p_area) $$;
revoke all on function public.saree_search_pharmacy_stock(text,text) from public;
grant execute on function public.saree_search_pharmacy_stock(text,text) to anon,authenticated;

create or replace function private.saree_submit_refund_request_impl(
 p_order_id uuid,p_amount numeric,p_reason text
) returns uuid language plpgsql security definer set search_path=''
as $$
declare v_order public.orders%rowtype; v_id uuid;
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 if p_amount is null or p_amount<=0 then raise exception 'invalid refund amount'; end if;
 if length(trim(coalesce(p_reason,'')))<3 or length(trim(p_reason))>1000 then raise exception 'refund reason is required'; end if;
 select * into v_order from public.orders where id=p_order_id and customer_id=auth.uid() for update;
 if not found or v_order.status<>'delivered' then raise exception 'only delivered orders can be submitted for refund'; end if;
 if p_amount>v_order.total then raise exception 'refund amount exceeds order total'; end if;
 if exists(select 1 from public.saree_refund_requests r where r.order_id=p_order_id and r.status in ('pending','approved','paid')) then
   raise exception 'an active refund request already exists for this order';
 end if;
 insert into public.saree_refund_requests(order_id,customer_id,amount,reason)
 values(p_order_id,auth.uid(),p_amount,trim(p_reason)) returning id into v_id;
 return v_id;
end $$;
revoke all on function private.saree_submit_refund_request_impl(uuid,numeric,text) from public,anon;
grant execute on function private.saree_submit_refund_request_impl(uuid,numeric,text) to authenticated;

create or replace function public.saree_submit_refund_request(p_order_id uuid,p_amount numeric,p_reason text)
returns uuid language sql security invoker set search_path=''
as $$ select private.saree_submit_refund_request_impl(p_order_id,p_amount,p_reason) $$;
revoke all on function public.saree_submit_refund_request(uuid,numeric,text) from public,anon;
grant execute on function public.saree_submit_refund_request(uuid,numeric,text) to authenticated;
