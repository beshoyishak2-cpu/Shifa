-- Saree3 operational completion: enforce merchant opening/minimum order,
-- add persistent private rides, verified clinic directory, and pharmacist review.
-- Apply after migrations 001-005.

-- Checkout is authoritative: availability, delivery fee, minimum order and
-- immutable delivery snapshot are calculated from trusted database rows.
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
  v_min_order numeric(10,2);
  v_rows integer;
  v_unique_rows integer;
  v_address public.customer_addresses%rowtype;
begin
  if v_customer_id is null then raise exception 'Authentication required'; end if;
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
    raise exception 'Order must contain at least one item';
  end if;

  select * into v_address
  from public.customer_addresses a
  where a.id = p_address_id and a.customer_id = v_customer_id;
  if not found then raise exception 'Address not found'; end if;

  select m.delivery_fee, m.min_order
    into v_delivery_fee, v_min_order
  from public.merchants m
  where m.id = p_merchant_id and m.is_active = true and m.is_open = true;
  if not found then raise exception 'Merchant is closed or unavailable'; end if;

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
  if v_subtotal < coalesce(v_min_order, 0) then
    raise exception 'Order is below the merchant minimum order amount';
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

  insert into public.order_items (order_id, product_id, product_name, unit_price, quantity)
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

-- Verified doctor/clinic directory. No demo phone numbers are exposed when connected.
create table if not exists public.medical_providers (
  id uuid primary key default gen_random_uuid(),
  full_name text not null,
  specialty text not null,
  address text not null,
  phone text not null,
  working_days text,
  is_active boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.medical_providers enable row level security;
drop policy if exists "active medical providers public" on public.medical_providers;
create policy "active medical providers public"
  on public.medical_providers for select
  using (is_active = true or public.shifa_is_admin());
drop policy if exists "admin manages medical providers" on public.medical_providers;
create policy "admin manages medical providers"
  on public.medical_providers for all to authenticated
  using (public.shifa_is_admin())
  with check (public.shifa_is_admin());
grant select on public.medical_providers to anon, authenticated;
grant insert, update, delete on public.medical_providers to authenticated;

drop trigger if exists medical_providers_set_updated_at on public.medical_providers;
create trigger medical_providers_set_updated_at
before update on public.medical_providers
for each row execute procedure public.shifa_set_updated_at();

-- Private, persisted "ابعتلي / مشوار خاص" requests.
create table if not exists public.private_ride_requests (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles(id) on delete cascade,
  courier_id uuid references public.courier_profiles(user_id),
  pickup_text text not null,
  dropoff_text text not null,
  item_description text not null,
  customer_phone text not null,
  customer_note text,
  price numeric(10,2) not null default 25 check (price >= 0),
  status text not null default 'pending'
    check (status in ('pending','accepted','picked_up','delivered','cancelled')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists private_ride_requests_customer_idx
  on public.private_ride_requests(customer_id, created_at desc);
create index if not exists private_ride_requests_dispatch_idx
  on public.private_ride_requests(status, courier_id, created_at);

alter table public.private_ride_requests enable row level security;
drop policy if exists "ride participants and available couriers read" on public.private_ride_requests;
create policy "ride participants and available couriers read"
  on public.private_ride_requests for select to authenticated
  using (
    customer_id = auth.uid()
    or courier_id = auth.uid()
    or public.shifa_is_admin()
    or (
      status = 'pending' and courier_id is null
      and exists (
        select 1 from public.courier_profiles cp
        where cp.user_id = auth.uid() and cp.is_verified = true and cp.is_available = true
      )
    )
  );
drop policy if exists "customers create own rides" on public.private_ride_requests;
create policy "customers create own rides"
  on public.private_ride_requests for insert to authenticated
  with check (customer_id = auth.uid() and courier_id is null and status = 'pending');
grant select, insert on public.private_ride_requests to authenticated;

drop trigger if exists private_ride_requests_set_updated_at on public.private_ride_requests;
create trigger private_ride_requests_set_updated_at
before update on public.private_ride_requests
for each row execute procedure public.shifa_set_updated_at();

create or replace function public.claim_shifa_ride(p_ride_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare v_ride public.private_ride_requests%rowtype;
begin
  if auth.uid() is null then raise exception 'Authentication required'; end if;
  if not exists (
    select 1 from public.courier_profiles cp
    where cp.user_id = auth.uid() and cp.is_verified = true and cp.is_available = true
  ) then raise exception 'Verified available courier required'; end if;
  select * into v_ride from public.private_ride_requests where id = p_ride_id for update;
  if not found then raise exception 'Ride not found'; end if;
  if v_ride.status <> 'pending' or v_ride.courier_id is not null then
    raise exception 'Ride is no longer available';
  end if;
  update public.private_ride_requests
  set courier_id = auth.uid(), status = 'accepted', updated_at = now()
  where id = p_ride_id;
end;
$$;
revoke all on function public.claim_shifa_ride(uuid) from public;
grant execute on function public.claim_shifa_ride(uuid) to authenticated;

create or replace function public.transition_shifa_ride(
  p_ride_id uuid,
  p_next_status text
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare v_ride public.private_ride_requests%rowtype;
begin
  if auth.uid() is null then raise exception 'Authentication required'; end if;
  if p_next_status not in ('accepted','picked_up','delivered','cancelled') then
    raise exception 'Invalid ride status';
  end if;
  select * into v_ride from public.private_ride_requests where id = p_ride_id for update;
  if not found then raise exception 'Ride not found'; end if;

  if public.shifa_is_admin() then
    null;
  elsif v_ride.customer_id = auth.uid() and v_ride.status = 'pending' and p_next_status = 'cancelled' then
    null;
  elsif v_ride.courier_id = auth.uid() and (
    (v_ride.status = 'accepted' and p_next_status = 'picked_up') or
    (v_ride.status = 'picked_up' and p_next_status = 'delivered')
  ) then
    null;
  else
    raise exception 'Invalid ride transition or insufficient permissions';
  end if;

  update public.private_ride_requests
  set status = p_next_status, updated_at = now()
  where id = p_ride_id;
end;
$$;
revoke all on function public.transition_shifa_ride(uuid,text) from public;
grant execute on function public.transition_shifa_ride(uuid,text) to authenticated;

-- Pharmacist identity must be verified by an administrator before prescription review.
create table if not exists public.pharmacist_profiles (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  pharmacy_merchant_id uuid not null references public.merchants(id) on delete cascade,
  license_number text not null,
  license_verified boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.pharmacist_profiles enable row level security;
drop policy if exists "pharmacist reads own verification" on public.pharmacist_profiles;
create policy "pharmacist reads own verification"
  on public.pharmacist_profiles for select to authenticated
  using (user_id = auth.uid() or public.shifa_is_admin());
drop policy if exists "admin manages pharmacist verification" on public.pharmacist_profiles;
create policy "admin manages pharmacist verification"
  on public.pharmacist_profiles for all to authenticated
  using (public.shifa_is_admin())
  with check (public.shifa_is_admin());
grant select on public.pharmacist_profiles to authenticated;
grant insert, update, delete on public.pharmacist_profiles to authenticated;

drop trigger if exists pharmacist_profiles_set_updated_at on public.pharmacist_profiles;
create trigger pharmacist_profiles_set_updated_at
before update on public.pharmacist_profiles
for each row execute procedure public.shifa_set_updated_at();

create or replace function public.review_shifa_prescription(
  p_prescription_id uuid,
  p_next_status text,
  p_note text default null
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare v_prescription public.pharmacy_prescriptions%rowtype;
begin
  if auth.uid() is null then raise exception 'Authentication required'; end if;
  if p_next_status not in ('under_review','approved','rejected','fulfilled') then
    raise exception 'Invalid prescription status';
  end if;
  select * into v_prescription
  from public.pharmacy_prescriptions
  where id = p_prescription_id
  for update;
  if not found then raise exception 'Prescription not found'; end if;

  if not public.shifa_is_admin() and not exists (
    select 1 from public.pharmacist_profiles pp
    where pp.user_id = auth.uid()
      and pp.pharmacy_merchant_id = v_prescription.pharmacy_merchant_id
      and pp.license_verified = true
      and public.shifa_is_merchant_member(pp.pharmacy_merchant_id)
  ) then
    raise exception 'Verified pharmacist for this pharmacy required';
  end if;

  if (v_prescription.status = 'submitted' and p_next_status in ('under_review','rejected')) or
     (v_prescription.status = 'under_review' and p_next_status in ('approved','rejected')) or
     (v_prescription.status = 'approved' and p_next_status = 'fulfilled') or
     public.shifa_is_admin() then
    update public.pharmacy_prescriptions
    set status = p_next_status,
        pharmacist_note = p_note,
        reviewed_by = auth.uid(),
        reviewed_at = now()
    where id = p_prescription_id;
  else
    raise exception 'Invalid prescription transition';
  end if;
end;
$$;
revoke all on function public.review_shifa_prescription(uuid,text,text) from public;
grant execute on function public.review_shifa_prescription(uuid,text,text) to authenticated;
