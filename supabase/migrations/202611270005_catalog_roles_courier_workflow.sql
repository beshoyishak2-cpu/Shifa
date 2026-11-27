-- Operational compatibility and secure courier handoff for the current React MVP.
-- Apply after migrations 001-004. This schema follows the deployed Shifa tables
-- (merchants/products/customer_addresses/orders), not the separate starter schema.sql.

alter table public.profiles
  add column if not exists role text not null default 'customer';
do $$ begin
  alter table public.profiles add constraint profiles_role_allowed
    check (role in ('customer','merchant','driver','admin'));
exception when duplicate_object then null; end $$;

create or replace function public.shifa_protect_profile_role()
returns trigger language plpgsql
security definer
set search_path = public
as $$
begin
  if new.role is distinct from old.role and not public.shifa_is_admin() then
    raise exception 'role changes require administrator approval';
  end if;
  new.updated_at = now();
  return new;
end;
$$;
drop trigger if exists shifa_protect_profile_role_trigger on public.profiles;
create trigger shifa_protect_profile_role_trigger
before update on public.profiles
for each row execute procedure public.shifa_protect_profile_role();

alter table public.merchants
  add column if not exists service_type text not null default 'restaurant',
  add column if not exists area_name text not null default 'ملوي',
  add column if not exists is_open boolean not null default false,
  add column if not exists min_order numeric(10,2) not null default 0,
  add column if not exists eta text not null default '20–30 دقيقة';
do $$ begin
  alter table public.merchants add constraint merchants_service_type_allowed
    check (service_type in ('restaurant','cafe','grocery','vegetables','pharmacy'));
exception when duplicate_object then null; end $$;
update public.merchants set is_open = is_active where is_open = false and is_active = true;

alter table public.products
  add column if not exists unit text not null default 'قطعة',
  add column if not exists emoji text not null default '📦';

alter table public.orders
  add column if not exists customer_name text not null default '',
  add column if not exists customer_phone text not null default '';

-- A verified, available courier may see orders prepared and waiting for pickup.
drop policy if exists "verified couriers see ready unassigned orders" on public.orders;
create policy "verified couriers see ready unassigned orders"
on public.orders for select to authenticated
using (
  status = 'ready_for_pickup'
  and courier_id is null
  and exists (
    select 1 from public.courier_profiles cp
    where cp.user_id = auth.uid()
      and cp.is_verified = true
      and cp.is_available = true
  )
);

create or replace function public.claim_shifa_order(p_order_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_order public.orders%rowtype;
begin
  if auth.uid() is null then raise exception 'authentication required'; end if;
  if not exists (
    select 1 from public.courier_profiles cp
    where cp.user_id = auth.uid()
      and cp.is_verified = true
      and cp.is_available = true
  ) then raise exception 'verified available courier required'; end if;

  select * into v_order
  from public.orders
  where id = p_order_id
  for update;

  if not found then raise exception 'order not found'; end if;
  if v_order.status <> 'ready_for_pickup' or v_order.courier_id is not null then
    raise exception 'order is no longer available';
  end if;

  update public.orders
  set courier_id = auth.uid(), updated_at = now()
  where id = p_order_id;

  insert into public.order_status_events(order_id, changed_by, old_status, new_status, note)
  values (p_order_id, auth.uid(), v_order.status, v_order.status, 'Courier accepted delivery');
end;
$$;
revoke all on function public.claim_shifa_order(uuid) from public;
grant execute on function public.claim_shifa_order(uuid) to authenticated;

create or replace function public.transition_shifa_order(
  p_order_id uuid,
  p_next_status public.shifa_order_status
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_order public.orders%rowtype;
  v_is_admin boolean;
  v_is_merchant boolean;
begin
  if auth.uid() is null then raise exception 'authentication required'; end if;
  select * into v_order from public.orders where id = p_order_id for update;
  if not found then raise exception 'order not found'; end if;

  v_is_admin := public.shifa_is_admin();
  v_is_merchant := public.shifa_is_merchant_member(v_order.merchant_id);

  if v_is_admin then
    update public.orders set status = p_next_status, updated_at = now() where id = p_order_id;
  elsif v_is_merchant and (
    (v_order.status = 'pending' and p_next_status in ('accepted','cancelled')) or
    (v_order.status = 'accepted' and p_next_status in ('preparing','cancelled')) or
    (v_order.status = 'preparing' and p_next_status = 'ready_for_pickup')
  ) then
    update public.orders set status = p_next_status, updated_at = now() where id = p_order_id;
  elsif v_order.courier_id = auth.uid() and (
    (v_order.status = 'ready_for_pickup' and p_next_status = 'picked_up') or
    (v_order.status = 'picked_up' and p_next_status = 'delivered')
  ) then
    update public.orders set status = p_next_status, updated_at = now() where id = p_order_id;
  else
    raise exception 'invalid status transition or insufficient permissions';
  end if;

  insert into public.order_status_events(order_id, changed_by, old_status, new_status)
  values (p_order_id, auth.uid(), v_order.status, p_next_status);
end;
$$;
revoke all on function public.transition_shifa_order(uuid,public.shifa_order_status) from public;
grant execute on function public.transition_shifa_order(uuid,public.shifa_order_status) to authenticated;

comment on column public.profiles.role is
  'Customer by default. Merchant, driver, and admin roles require approval; self-service role escalation is blocked.';


-- Fill the customer contact snapshot for the trusted checkout RPC.
create or replace function public.shifa_fill_order_customer_snapshot()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_name text;
  v_phone text;
begin
  select full_name, phone into v_name, v_phone
  from public.profiles where id = new.customer_id;
  if coalesce(new.customer_name, '') = '' then
    new.customer_name := coalesce(v_name, '');
  end if;
  if coalesce(new.customer_phone, '') = '' then
    new.customer_phone := coalesce(v_phone, '');
  end if;
  return new;
end;
$$;
drop trigger if exists shifa_fill_order_customer_snapshot_trigger on public.orders;
create trigger shifa_fill_order_customer_snapshot_trigger
before insert on public.orders
for each row execute procedure public.shifa_fill_order_customer_snapshot();
