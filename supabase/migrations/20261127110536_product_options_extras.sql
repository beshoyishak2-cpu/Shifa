create table public.product_option_groups (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  name text not null check (length(btrim(name)) between 1 and 100),
  selection_type text not null default 'single' check (selection_type in ('single','multiple')),
  min_select integer not null default 0 check (min_select >= 0),
  max_select integer not null default 1 check (max_select between 1 and 30),
  is_required boolean not null default false,
  sort_order integer not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint product_option_groups_selection_bounds check (min_select <= max_select and (not is_required or min_select >= 1) and (selection_type <> 'single' or max_select = 1))
);
create index product_option_groups_product_idx on public.product_option_groups(product_id, sort_order) where is_active;

create table public.product_option_values (
  id uuid primary key default gen_random_uuid(),
  group_id uuid not null references public.product_option_groups(id) on delete cascade,
  name text not null check (length(btrim(name)) between 1 and 100),
  price_delta numeric(10,2) not null default 0 check (price_delta >= 0),
  is_available boolean not null default true,
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index product_option_values_group_idx on public.product_option_values(group_id, sort_order) where is_available;

create table public.order_item_options (
  id uuid primary key default gen_random_uuid(),
  order_item_id uuid not null references public.order_items(id) on delete cascade,
  option_group_id uuid references public.product_option_groups(id) on delete set null,
  option_value_id uuid references public.product_option_values(id) on delete set null,
  group_name_snapshot text not null,
  option_name_snapshot text not null,
  price_delta numeric(10,2) not null default 0 check (price_delta >= 0),
  quantity integer not null default 1 check (quantity between 1 and 99),
  created_at timestamptz not null default now()
);
create index order_item_options_item_idx on public.order_item_options(order_item_id);

alter table public.product_option_groups enable row level security;
alter table public.product_option_values enable row level security;
alter table public.order_item_options enable row level security;

create policy "public reads active product option groups"
on public.product_option_groups for select to anon, authenticated
using (
  is_active and exists (
    select 1 from public.products p
    join public.merchants m on m.id = p.merchant_id
    where p.id = product_option_groups.product_id and p.is_available and m.is_active
  )
);
create policy "merchant manages product option groups"
on public.product_option_groups for all to authenticated
using (
  shifa_is_admin() or exists (
    select 1 from public.products p
    where p.id = product_option_groups.product_id and shifa_is_merchant_member(p.merchant_id)
  )
)
with check (
  shifa_is_admin() or exists (
    select 1 from public.products p
    where p.id = product_option_groups.product_id and shifa_is_merchant_member(p.merchant_id)
  )
);

create policy "public reads available product option values"
on public.product_option_values for select to anon, authenticated
using (
  is_available and exists (
    select 1 from public.product_option_groups g
    join public.products p on p.id = g.product_id
    join public.merchants m on m.id = p.merchant_id
    where g.id = product_option_values.group_id and g.is_active and p.is_available and m.is_active
  )
);
create policy "merchant manages product option values"
on public.product_option_values for all to authenticated
using (
  shifa_is_admin() or exists (
    select 1 from public.product_option_groups g
    join public.products p on p.id = g.product_id
    where g.id = product_option_values.group_id and shifa_is_merchant_member(p.merchant_id)
  )
)
with check (
  shifa_is_admin() or exists (
    select 1 from public.product_option_groups g
    join public.products p on p.id = g.product_id
    where g.id = product_option_values.group_id and shifa_is_merchant_member(p.merchant_id)
  )
);

create policy "order option snapshots visible to order participants"
on public.order_item_options for select to authenticated
using (
  exists (
    select 1 from public.order_items oi
    join public.orders o on o.id = oi.order_id
    where oi.id = order_item_options.order_item_id
      and (
        o.customer_id = (select auth.uid())
        or o.courier_id = (select auth.uid())
        or shifa_is_admin()
        or shifa_is_merchant_member(o.merchant_id)
      )
  )
);

comment on table public.product_option_groups is 'Selectable option groups for a product, such as size or extras.';
comment on table public.product_option_values is 'Selectable values and their additional prices within a product option group.';
comment on table public.order_item_options is 'Immutable-at-order-time option snapshots attached to an order item.';
