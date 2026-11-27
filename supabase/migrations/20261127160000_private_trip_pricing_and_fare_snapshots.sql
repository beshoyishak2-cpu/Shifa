-- Private-trip pricing and immutable fare snapshots.
create table if not exists public.private_trip_settings (
 id boolean primary key default true check(id),
 price_per_km numeric(10,2) not null default 0 check(price_per_km>=0),
 minimum_fare numeric(10,2) not null default 0 check(minimum_fare>=0),
 meter_start_fee numeric(10,2) not null default 0 check(meter_start_fee>=0),
 commission_percent numeric(5,2) not null default 0 check(commission_percent between 0 and 100),
 updated_at timestamptz not null default now(), updated_by uuid references public.profiles(id)
);
insert into public.private_trip_settings(id) values(true) on conflict(id) do nothing;
alter table public.private_trip_settings enable row level security;
create policy "admins read private trip settings" on public.private_trip_settings for select to authenticated using((select private.shifa_is_admin()));
create policy "admins update private trip settings" on public.private_trip_settings for update to authenticated using((select private.shifa_is_admin())) with check((select private.shifa_is_admin()));
grant select,update on public.private_trip_settings to authenticated;

create table if not exists public.private_trips (
 id uuid primary key default gen_random_uuid(),
 customer_id uuid not null references public.profiles(id), courier_id uuid references public.courier_profiles(user_id),
 pickup_latitude double precision not null check(pickup_latitude between -90 and 90),
 pickup_longitude double precision not null check(pickup_longitude between -180 and 180), pickup_address text not null,
 destination_latitude double precision not null check(destination_latitude between -90 and 90),
 destination_longitude double precision not null check(destination_longitude between -180 and 180), destination_address text not null,
 route_distance_km numeric(10,3) not null check(route_distance_km>0),
 estimated_duration_minutes integer not null check(estimated_duration_minutes>=0), route_geometry jsonb not null default '[]'::jsonb,
 price_per_km_snapshot numeric(10,2) not null check(price_per_km_snapshot>=0),
 minimum_fare_snapshot numeric(10,2) not null check(minimum_fare_snapshot>=0),
 meter_start_fee_snapshot numeric(10,2) not null check(meter_start_fee_snapshot>=0),
 commission_percent_snapshot numeric(5,2) not null check(commission_percent_snapshot between 0 and 100),
 fare_amount numeric(10,2) not null check(fare_amount>=0),
 app_commission_amount numeric(10,2) not null check(app_commission_amount>=0),
 courier_earnings numeric(10,2) not null check(courier_earnings>=0),
 payment_method text not null default 'cash' check(payment_method='cash'),
 customer_note text not null default '',
 status text not null default 'searching' check(status in ('searching','accepted','in_progress','delivered','cancelled')),
 cancelled_by uuid references public.profiles(id), cancellation_reason text,
 confirmed_at timestamptz not null default now(), accepted_at timestamptz, started_at timestamptz, delivered_at timestamptz, cancelled_at timestamptz,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create index if not exists private_trips_customer_created_idx on public.private_trips(customer_id,created_at desc);
create index if not exists private_trips_courier_status_idx on public.private_trips(courier_id,status,created_at desc);
create index if not exists private_trips_searching_idx on public.private_trips(status,created_at) where status='searching';
alter table public.private_trips enable row level security;
create policy "private trip participants read trip" on public.private_trips for select to authenticated using(
 customer_id=(select auth.uid()) or courier_id=(select auth.uid()) or (select private.shifa_is_admin())
 or (status='searching' and exists(select 1 from public.courier_profiles cp where cp.user_id=(select auth.uid()) and cp.is_verified and cp.is_available and not cp.locked_for_settlement))
);
grant select on public.private_trips to authenticated;
revoke insert,update,delete on public.private_trips from anon,authenticated;

drop policy if exists "couriers and assigned order participants read live location" on public.courier_live_locations;
create policy "couriers and assigned order or trip participants read live location" on public.courier_live_locations for select to authenticated using(
 courier_id=(select auth.uid()) or (select private.shifa_is_admin())
 or exists(select 1 from public.orders o where o.courier_id=courier_live_locations.courier_id and o.status in ('accepted','preparing','ready_for_pickup','picked_up')
  and (o.customer_id=(select auth.uid()) or exists(select 1 from public.merchant_members mm where mm.merchant_id=o.merchant_id and mm.user_id=(select auth.uid()))))
 or exists(select 1 from public.private_trips t where t.courier_id=courier_live_locations.courier_id and t.status in ('accepted','in_progress') and t.customer_id=(select auth.uid()))
);
do $$ begin
 if not exists(select 1 from pg_publication_tables where pubname='supabase_realtime' and schemaname='public' and tablename='private_trips') then
  alter publication supabase_realtime add table public.private_trips;
 end if;
end $$;