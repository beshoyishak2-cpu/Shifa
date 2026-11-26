-- Shifa initial Supabase schema
-- Target: Mallawi, Minya, Egypt. Apply in Supabase SQL Editor after reviewing.
create extension if not exists pgcrypto;

create type public.shifa_order_status as enum
  ('pending','accepted','preparing','ready_for_pickup','picked_up','delivered','cancelled');
create type public.shifa_payment_method as enum ('cash');
create type public.shifa_ticket_status as enum ('open','in_progress','resolved','closed');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default '',
  phone text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.merchants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  phone text,
  address text,
  is_active boolean not null default false,
  delivery_fee numeric(10,2) not null default 0 check (delivery_fee >= 0),
  commission_percent numeric(5,2) not null default 0 check (commission_percent between 0 and 100),
  created_at timestamptz not null default now()
);

create table public.merchant_members (
  merchant_id uuid not null references public.merchants(id) on delete cascade,
  user_id uuid not null references public.profiles(id) on delete cascade,
  member_role text not null default 'staff' check (member_role in ('owner','staff')),
  primary key (merchant_id,user_id)
);

create table public.categories (
  id uuid primary key default gen_random_uuid(),
  name_ar text not null,
  slug text not null unique,
  sort_order int not null default 0,
  is_active boolean not null default true
);

create table public.products (
  id uuid primary key default gen_random_uuid(),
  merchant_id uuid not null references public.merchants(id) on delete cascade,
  category_id uuid references public.categories(id) on delete set null,
  name text not null,
  description text,
  image_url text,
  price numeric(10,2) not null check (price >= 0),
  is_available boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.customer_addresses (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles(id) on delete cascade,
  label text not null default 'المنزل',
  address_text text not null,
  landmark text,
  latitude double precision,
  longitude double precision,
  created_at timestamptz not null default now(),
  check (latitude is null or latitude between -90 and 90),
  check (longitude is null or longitude between -180 and 180)
);

create table public.courier_profiles (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  vehicle_type text,
  is_available boolean not null default false,
  is_verified boolean not null default false
);

create table public.orders (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles(id),
  merchant_id uuid not null references public.merchants(id),
  address_id uuid not null references public.customer_addresses(id),
  courier_id uuid references public.courier_profiles(user_id),
  status public.shifa_order_status not null default 'pending',
  payment_method public.shifa_payment_method not null default 'cash',
  subtotal numeric(10,2) not null check (subtotal >= 0),
  delivery_fee numeric(10,2) not null check (delivery_fee >= 0),
  total numeric(10,2) not null check (total >= 0),
  customer_note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  product_id uuid references public.products(id) on delete set null,
  product_name text not null,
  unit_price numeric(10,2) not null check (unit_price >= 0),
  quantity int not null check (quantity between 1 and 99),
  line_total numeric(10,2) generated always as (unit_price * quantity) stored
);

create table public.order_status_events (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  changed_by uuid references public.profiles(id),
  old_status public.shifa_order_status,
  new_status public.shifa_order_status not null,
  note text,
  created_at timestamptz not null default now()
);

-- Prescription images are private. A licensed pharmacist must review prescriptions;
-- the app must never automatically substitute medicines.
create table public.pharmacy_prescriptions (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles(id) on delete cascade,
  pharmacy_merchant_id uuid references public.merchants(id),
  storage_path text not null,
  status text not null default 'submitted'
    check (status in ('submitted','under_review','approved','rejected','fulfilled')),
  pharmacist_note text,
  reviewed_by uuid references public.profiles(id),
  created_at timestamptz not null default now(),
  reviewed_at timestamptz
);

create table public.support_tickets (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles(id),
  order_id uuid references public.orders(id) on delete set null,
  subject text not null,
  message text not null,
  status public.shifa_ticket_status not null default 'open',
  created_at timestamptz not null default now()
);

create index products_merchant_available_idx on public.products(merchant_id,is_available);
create index orders_customer_created_idx on public.orders(customer_id,created_at desc);
create index orders_merchant_created_idx on public.orders(merchant_id,created_at desc);
create index orders_courier_status_idx on public.orders(courier_id,status);

create or replace function public.shifa_is_admin()
returns boolean language sql stable security definer set search_path = public
as $$
  select coalesce((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin', false);
$$;

create or replace function public.shifa_is_merchant_member(p_merchant_id uuid)
returns boolean language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from public.merchant_members mm
    where mm.merchant_id = p_merchant_id and mm.user_id = auth.uid()
  );
$$;

alter table public.profiles enable row level security;
alter table public.merchants enable row level security;
alter table public.merchant_members enable row level security;
alter table public.categories enable row level security;
alter table public.products enable row level security;
alter table public.customer_addresses enable row level security;
alter table public.courier_profiles enable row level security;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;
alter table public.order_status_events enable row level security;
alter table public.pharmacy_prescriptions enable row level security;
alter table public.support_tickets enable row level security;

create policy "profiles read self or admin" on public.profiles for select to authenticated
  using (id = auth.uid() or public.shifa_is_admin());
create policy "profiles update self or admin" on public.profiles for update to authenticated
  using (id = auth.uid() or public.shifa_is_admin())
  with check (id = auth.uid() or public.shifa_is_admin());

create policy "active merchants public, admin all" on public.merchants for select
  using (is_active or public.shifa_is_admin() or public.shifa_is_merchant_member(id));
create policy "merchant members read memberships" on public.merchant_members for select to authenticated
  using (user_id = auth.uid() or public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id));
create policy "categories visible" on public.categories for select
  using (is_active or public.shifa_is_admin());
create policy "products visible" on public.products for select
  using ((is_available and exists(select 1 from public.merchants m where m.id=merchant_id and m.is_active))
    or public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id));
create policy "merchant manages products" on public.products for all to authenticated
  using (public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id))
  with check (public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id));

create policy "customers manage own addresses" on public.customer_addresses for all to authenticated
  using (customer_id = auth.uid() or public.shifa_is_admin())
  with check (customer_id = auth.uid() or public.shifa_is_admin());

create policy "courier reads own profile or admin" on public.courier_profiles for select to authenticated
  using (user_id = auth.uid() or public.shifa_is_admin());
create policy "courier updates own availability" on public.courier_profiles for update to authenticated
  using (user_id = auth.uid() or public.shifa_is_admin())
  with check (user_id = auth.uid() or public.shifa_is_admin());

create policy "orders visible to participants" on public.orders for select to authenticated
  using (customer_id = auth.uid() or courier_id = auth.uid()
    or public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id));
create policy "customer creates own order" on public.orders for insert to authenticated
  with check (customer_id = auth.uid() and courier_id is null and status = 'pending');
create policy "merchant or courier updates order" on public.orders for update to authenticated
  using (public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id) or courier_id = auth.uid())
  with check (public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id) or courier_id = auth.uid());

create policy "order items visible to order participants" on public.order_items for select to authenticated
  using (exists(select 1 from public.orders o where o.id=order_id and
    (o.customer_id=auth.uid() or o.courier_id=auth.uid() or public.shifa_is_admin()
      or public.shifa_is_merchant_member(o.merchant_id))));
create policy "customer adds items to own pending order" on public.order_items for insert to authenticated
  with check (exists(select 1 from public.orders o where o.id=order_id
    and o.customer_id=auth.uid() and o.status='pending'));

create policy "order events visible to participants" on public.order_status_events for select to authenticated
  using (exists(select 1 from public.orders o where o.id=order_id and
    (o.customer_id=auth.uid() or o.courier_id=auth.uid() or public.shifa_is_admin()
      or public.shifa_is_merchant_member(o.merchant_id))));
create policy "prescriptions visible to owner pharmacist or admin" on public.pharmacy_prescriptions
  for select to authenticated using (customer_id=auth.uid() or public.shifa_is_admin()
    or (pharmacy_merchant_id is not null and public.shifa_is_merchant_member(pharmacy_merchant_id)));
create policy "customer submits own prescription" on public.pharmacy_prescriptions
  for insert to authenticated with check (customer_id=auth.uid() and status='submitted');
create policy "tickets visible to owner or admin" on public.support_tickets for select to authenticated
  using (customer_id=auth.uid() or public.shifa_is_admin());
create policy "customer creates own ticket" on public.support_tickets for insert to authenticated
  with check (customer_id=auth.uid());

-- NOTE: Configure a PRIVATE Storage bucket named 'prescriptions' and policies separately.
-- Never expose the Supabase service_role key in the mobile application.
-- Before production, route checkout through a trusted server/RPC to recalculate all prices
-- and fees from database records; do not trust client-submitted totals.
