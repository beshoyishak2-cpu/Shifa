alter table public.merchants
  add column if not exists pharmacist_verified boolean not null default false;

create table if not exists public.errand_requests (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles(id) on delete cascade,
  courier_id uuid references public.courier_profiles(user_id),
  status public.shifa_order_status not null default 'pending',
  pickup_address text not null,
  dropoff_address text not null,
  item_description text not null,
  customer_name text not null default '',
  customer_phone text not null default '',
  customer_note text,
  delivery_fee numeric(10,2) not null default 25 check (delivery_fee >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (length(trim(pickup_address)) between 3 and 300),
  check (length(trim(dropoff_address)) between 3 and 300),
  check (length(trim(item_description)) between 2 and 300)
);
create index if not exists errand_requests_customer_created_idx on public.errand_requests(customer_id,created_at desc);
create index if not exists errand_requests_courier_status_idx on public.errand_requests(courier_id,status,created_at desc);
alter table public.errand_requests enable row level security;

create policy "errands visible to participants" on public.errand_requests
for select to authenticated using (
  customer_id = auth.uid() or courier_id = auth.uid() or public.shifa_is_admin()
  or (courier_id is null and status='pending' and exists(
    select 1 from public.courier_profiles cp where cp.user_id=auth.uid() and cp.is_verified and cp.is_available
  ))
);
create policy "customers create own errands" on public.errand_requests
for insert to authenticated with check (customer_id=auth.uid() and courier_id is null and status='pending');

create or replace function public.create_shifa_errand(
  p_pickup_address text,p_dropoff_address text,p_item_description text,
  p_customer_phone text,p_customer_note text default null
) returns uuid language plpgsql security definer set search_path=public
as $$
declare v_uid uuid:=auth.uid(); v_id uuid; v_name text; v_phone text;
begin
  if v_uid is null then raise exception 'authentication required'; end if;
  if length(trim(coalesce(p_pickup_address,''))) not between 3 and 300
    or length(trim(coalesce(p_dropoff_address,''))) not between 3 and 300
    or length(trim(coalesce(p_item_description,''))) not between 2 and 300 then
    raise exception 'pickup, dropoff and item details are required';
  end if;
  select full_name,phone into v_name,v_phone from public.profiles where id=v_uid;
  insert into public.errand_requests(customer_id,pickup_address,dropoff_address,item_description,customer_name,customer_phone,customer_note,delivery_fee)
  values(v_uid,trim(p_pickup_address),trim(p_dropoff_address),trim(p_item_description),coalesce(v_name,''),
    coalesce(nullif(trim(p_customer_phone),''),v_phone,''),nullif(trim(p_customer_note),''),25)
  returning id into v_id;
  return v_id;
end;
$$;

create or replace function public.claim_shifa_errand(p_errand_id uuid)
returns void language plpgsql security definer set search_path=public
as $$
declare v_row public.errand_requests%rowtype;
begin
  if auth.uid() is null then raise exception 'authentication required'; end if;
  if not exists(select 1 from public.courier_profiles cp where cp.user_id=auth.uid() and cp.is_verified and cp.is_available) then
    raise exception 'verified available courier required';
  end if;
  select * into v_row from public.errand_requests where id=p_errand_id for update;
  if not found then raise exception 'errand not found'; end if;
  if v_row.status<>'pending' or v_row.courier_id is not null then raise exception 'errand is no longer available'; end if;
  update public.errand_requests set courier_id=auth.uid(),status='ready_for_pickup',updated_at=now() where id=p_errand_id;
end;
$$;

create or replace function public.transition_shifa_errand(p_errand_id uuid,p_next_status public.shifa_order_status)
returns void language plpgsql security definer set search_path=public
as $$
declare v_row public.errand_requests%rowtype;
begin
  if auth.uid() is null then raise exception 'authentication required'; end if;
  select * into v_row from public.errand_requests where id=p_errand_id for update;
  if not found then raise exception 'errand not found'; end if;
  if not public.shifa_is_admin() and v_row.courier_id<>auth.uid() then raise exception 'only assigned courier or admin may update errand'; end if;
  if not public.shifa_is_admin() and not ((v_row.status='ready_for_pickup' and p_next_status='picked_up') or (v_row.status='picked_up' and p_next_status='delivered')) then
    raise exception 'invalid errand status transition';
  end if;
  if public.shifa_is_admin() and p_next_status not in ('pending','ready_for_pickup','picked_up','delivered','cancelled') then raise exception 'invalid admin status'; end if;
  update public.errand_requests set status=p_next_status,updated_at=now() where id=p_errand_id;
end;
$$;
revoke execute on function public.create_shifa_errand(text,text,text,text,text) from public,anon;
grant execute on function public.create_shifa_errand(text,text,text,text,text) to authenticated;
revoke execute on function public.claim_shifa_errand(uuid) from public,anon;
grant execute on function public.claim_shifa_errand(uuid) to authenticated;
revoke execute on function public.transition_shifa_errand(uuid,public.shifa_order_status) from public,anon;
grant execute on function public.transition_shifa_errand(uuid,public.shifa_order_status) to authenticated;

create policy "verified pharmacy team reviews prescriptions" on public.pharmacy_prescriptions
for update to authenticated
using (pharmacy_merchant_id is not null and exists(
  select 1 from public.merchants m where m.id=pharmacy_merchant_id and m.service_type='pharmacy' and m.pharmacist_verified
) and public.shifa_is_merchant_member(pharmacy_merchant_id))
with check (pharmacy_merchant_id is not null and reviewed_by=auth.uid()
  and status in ('under_review','approved','rejected','fulfilled')
  and exists(select 1 from public.merchants m where m.id=pharmacy_merchant_id and m.service_type='pharmacy' and m.pharmacist_verified)
  and public.shifa_is_merchant_member(pharmacy_merchant_id));
