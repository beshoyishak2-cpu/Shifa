-- Harden client writes and provide trusted checkout.
-- Clients cannot submit their own totals or edit courier verification / order ownership.
revoke insert on public.orders from authenticated;
revoke insert on public.order_items from authenticated;
revoke update on public.orders from authenticated;
revoke update on public.courier_profiles from authenticated;

grant update (status, updated_at) on public.orders to authenticated;
grant update (is_available) on public.courier_profiles to authenticated;

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
begin
  if v_customer_id is null then
    raise exception 'Authentication required';
  end if;
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
    raise exception 'Order must contain at least one item';
  end if;
  if not exists (
    select 1 from public.customer_addresses a
    where a.id = p_address_id and a.customer_id = v_customer_id
  ) then
    raise exception 'Address not found';
  end if;

  select m.delivery_fee into v_delivery_fee
  from public.merchants m where m.id = p_merchant_id and m.is_active = true;
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
    subtotal, delivery_fee, total, customer_note
  ) values (
    v_customer_id, p_merchant_id, p_address_id, 'pending', 'cash',
    v_subtotal, v_delivery_fee, v_subtotal + v_delivery_fee, p_customer_note
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

-- Order status changes are restricted by RLS to admins, the merchant team, or assigned courier.
-- Only the status columns are writable by authenticated clients; totals and ownership stay protected.
