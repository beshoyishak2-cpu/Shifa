-- Delivery address persistence and courier handoff for Saree3.
-- Apply this migration in the Supabase SQL Editor before enabling production checkout.

alter table public.customer_addresses
  add column if not exists area text not null default 'غير محدد',
  add column if not exists street text not null default '',
  add column if not exists unit_details text,
  add column if not exists is_default boolean not null default false;

alter table public.orders
  add column if not exists delivery_area text,
  add column if not exists delivery_street text,
  add column if not exists delivery_landmark text,
  add column if not exists delivery_unit_details text,
  add column if not exists delivery_latitude double precision,
  add column if not exists delivery_longitude double precision,
  add column if not exists delivery_map_url text;

create index if not exists customer_addresses_owner_idx
  on public.customer_addresses(customer_id, created_at desc);
create index if not exists customer_addresses_default_idx
  on public.customer_addresses(customer_id, is_default);

-- Assigned couriers can read only the address attached to their assigned order.
drop policy if exists "assigned courier reads delivery address" on public.customer_addresses;
create policy "assigned courier reads delivery address"
  on public.customer_addresses for select to authenticated
  using (exists (
    select 1 from public.orders o
    where o.address_id = customer_addresses.id and o.courier_id = auth.uid()
  ));

-- Preserve a delivery-address snapshot on the order so later edits to a saved
-- customer address cannot change the destination of an order already placed.
create or replace function public.create_shifa_order(
  p_merchant_id uuid,
  p_address_id uuid,
  p_items jsonb,
  p_customer_note text default null
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_customer_id uuid := auth.uid();
  v_order_id uuid;
  v_subtotal numeric(10,2);
  v_delivery_fee numeric(10,2);
  v_rows integer;
  v_unique_rows integer;
  v_address public.customer_addresses%rowtype;
begin
  if v_customer_id is null then
    raise exception 'Authentication required';
  end if;
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
    raise exception 'Order must contain at least one item';
  end if;

  select * into v_address
  from public.customer_addresses a
  where a.id = p_address_id and a.customer_id = v_customer_id;
  if not found then
    raise exception 'Address not found';
  end if;

  select m.delivery_fee into v_delivery_fee
  from public.merchants m
  where m.id = p_merchant_id and m.is_active = true;
  if not found then
    raise exception 'Merchant is unavailable';
  end if;

  select count(*), count(distinct x.product_id),
         coalesce(sum(p.price * x.quantity), 0)
    into v_rows, v_unique_rows, v_subtotal
  from jsonb_to_recordset(p_items) as x(product_id uuid, quantity integer)
  join public.products p on p.id = x.product_id
  where p.merchant_id = p_merchant_id
    and p.is_available = true
    and x.quantity between 1 and 99;

  if v_rows <> jsonb_array_length(p_items) or v_unique_rows <> v_rows then
    raise exception 'One or more products are unavailable or invalid';
  end if;

  insert into public.orders (
    customer_id, merchant_id, address_id, status, payment_method,
    subtotal, delivery_fee, total, customer_note,
    delivery_area, delivery_street, delivery_landmark, delivery_unit_details,
    delivery_latitude, delivery_longitude, delivery_map_url
  ) values (
    v_customer_id, p_merchant_id, p_address_id, 'pending', 'cash',
    v_subtotal, v_delivery_fee, v_subtotal + v_delivery_fee, p_customer_note,
    v_address.area, v_address.street, v_address.landmark, v_address.unit_details,
    v_address.latitude, v_address.longitude,
    case when v_address.latitude is not null and v_address.longitude is not null
      then 'https://www.google.com/maps?q=' || v_address.latitude::text || ',' || v_address.longitude::text
      else null end
  ) returning id into v_order_id;

  insert into public.order_items (
    order_id, product_id, product_name, unit_price, quantity
  )
  select v_order_id, p.id, p.name, p.price, x.quantity
  from jsonb_to_recordset(p_items) as x(product_id uuid, quantity integer)
  join public.products p on p.id = x.product_id
  where p.merchant_id = p_merchant_id and p.is_available = true;

  insert into public.order_status_events(order_id, changed_by, new_status, note)
  values (v_order_id, v_customer_id, 'pending', 'Order submitted');

  return v_order_id;
end;
$$;

revoke all on function public.create_shifa_order(uuid,uuid,jsonb,text) from public;
grant execute on function public.create_shifa_order(uuid,uuid,jsonb,text) to authenticated;

comment on column public.orders.delivery_map_url is
  'Google Maps link for the immutable delivery destination snapshot visible to the assigned courier.';


-- Courier-facing read model. RLS on orders and customer_addresses remains enforced
-- because this view runs with the caller's privileges.
create or replace view public.courier_delivery_details
with (security_invoker = true)
as
select
  o.id as order_id,
  o.status,
  o.created_at,
  o.delivery_area,
  o.delivery_street,
  o.delivery_landmark,
  o.delivery_unit_details,
  o.delivery_latitude,
  o.delivery_longitude,
  o.delivery_map_url,
  a.address_text,
  o.customer_id,
  o.merchant_id
from public.orders o
join public.customer_addresses a on a.id = o.address_id
where o.courier_id = auth.uid();

grant select on public.courier_delivery_details to authenticated;
