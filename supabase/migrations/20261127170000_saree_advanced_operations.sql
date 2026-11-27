-- Saree advanced operations: pharmacy inventory expiry, delivery zones,
-- role feature permissions, pharmacist-reviewed alternatives, refunds and audit trail.
-- No medication interaction is automated: all clinical substitutions require pharmacist review.

create table if not exists public.product_inventory_batches (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  merchant_id uuid not null references public.merchants(id) on delete cascade,
  batch_code text not null,
  quantity integer not null default 0 check (quantity >= 0),
  expiry_date date,
  received_at timestamptz not null default now(),
  created_by uuid references public.profiles(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (length(trim(batch_code)) between 1 and 80)
);
create index if not exists inventory_batches_product_expiry_idx
  on public.product_inventory_batches(product_id, expiry_date);
create index if not exists inventory_batches_merchant_expiry_idx
  on public.product_inventory_batches(merchant_id, expiry_date);

create table if not exists public.saree_delivery_zones (
  id uuid primary key default gen_random_uuid(),
  merchant_id uuid not null references public.merchants(id) on delete cascade,
  area_name text not null,
  delivery_fee numeric(10,2) not null default 0 check(delivery_fee >= 0),
  minimum_order numeric(10,2) not null default 0 check(minimum_order >= 0),
  estimated_minutes integer not null default 45 check(estimated_minutes between 5 and 240),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(merchant_id, area_name)
);
create index if not exists saree_delivery_zones_area_idx
  on public.saree_delivery_zones(area_name, is_active);

create table if not exists public.saree_role_feature_permissions (
  id uuid primary key default gen_random_uuid(),
  app_role text not null check(app_role in ('customer','driver','merchant')),
  feature_key text not null,
  enabled boolean not null default true,
  updated_by uuid references public.profiles(id),
  updated_at timestamptz not null default now(),
  unique(app_role, feature_key),
  check(length(trim(feature_key)) between 2 and 100)
);

create table if not exists public.saree_product_alternatives (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  alternative_product_id uuid not null references public.products(id) on delete cascade,
  merchant_id uuid not null references public.merchants(id) on delete cascade,
  pharmacist_reviewed boolean not null default false,
  is_active boolean not null default false,
  review_note text,
  reviewed_by uuid references public.profiles(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  unique(product_id, alternative_product_id),
  check(product_id <> alternative_product_id)
);

create table if not exists public.saree_refund_requests (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  customer_id uuid not null references public.profiles(id),
  amount numeric(10,2) not null check(amount > 0),
  reason text not null check(length(trim(reason)) between 3 and 1000),
  status text not null default 'pending' check(status in ('pending','approved','rejected','paid')),
  admin_note text,
  reviewed_by uuid references public.profiles(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists saree_refunds_status_idx on public.saree_refund_requests(status,created_at desc);

create table if not exists public.saree_audit_events (
  id bigint generated always as identity primary key,
  actor_id uuid references public.profiles(id),
  table_name text not null,
  record_id text,
  action text not null,
  old_data jsonb,
  new_data jsonb,
  created_at timestamptz not null default now()
);
create index if not exists saree_audit_events_created_idx on public.saree_audit_events(created_at desc);
create index if not exists saree_audit_events_record_idx on public.saree_audit_events(table_name,record_id,created_at desc);

alter table public.product_inventory_batches enable row level security;
alter table public.saree_delivery_zones enable row level security;
alter table public.saree_role_feature_permissions enable row level security;
alter table public.saree_product_alternatives enable row level security;
alter table public.saree_refund_requests enable row level security;
alter table public.saree_audit_events enable row level security;

revoke all on public.product_inventory_batches, public.saree_delivery_zones,
 public.saree_role_feature_permissions, public.saree_product_alternatives,
 public.saree_refund_requests, public.saree_audit_events from anon, authenticated;

grant select,insert,update,delete on public.product_inventory_batches to authenticated;
grant select,insert,update,delete on public.saree_delivery_zones to authenticated;
grant select,insert,update,delete on public.saree_role_feature_permissions to authenticated;
grant select,insert,update,delete on public.saree_product_alternatives to authenticated;
grant select,insert,update on public.saree_refund_requests to authenticated;
grant select on public.saree_audit_events to authenticated;
grant usage,select on sequence public.saree_audit_events_id_seq to authenticated;

create policy inventory_read_admin_or_merchant on public.product_inventory_batches
 for select to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));
create policy inventory_insert_admin_or_merchant on public.product_inventory_batches
 for insert to authenticated with check((private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id)) and created_by=auth.uid());
create policy inventory_update_admin_or_merchant on public.product_inventory_batches
 for update to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id))
 with check(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));
create policy inventory_delete_admin_or_merchant on public.product_inventory_batches
 for delete to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));

create policy delivery_zones_anon_read_active on public.saree_delivery_zones
 for select to anon using(is_active);
create policy delivery_zones_authenticated_read on public.saree_delivery_zones
 for select to authenticated using(is_active or private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));
create policy delivery_zones_manage_admin_or_merchant on public.saree_delivery_zones
 for all to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id))
 with check(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));

create policy role_permissions_admin_only on public.saree_role_feature_permissions
 for all to authenticated using(private.shifa_is_admin()) with check(private.shifa_is_admin());

create policy alternatives_read_active on public.saree_product_alternatives
 for select to authenticated using(is_active or private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));
create policy alternatives_manage_admin_or_merchant on public.saree_product_alternatives
 for all to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id))
 with check(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));

create policy refunds_customer_or_admin_read on public.saree_refund_requests
 for select to authenticated using(customer_id=auth.uid() or private.shifa_is_admin());
create policy refunds_customer_create on public.saree_refund_requests
 for insert to authenticated with check(customer_id=auth.uid() and status='pending' and reviewed_by is null);
create policy refunds_admin_update on public.saree_refund_requests
 for update to authenticated using(private.shifa_is_admin()) with check(private.shifa_is_admin());

create policy audit_admin_read on public.saree_audit_events
 for select to authenticated using(private.shifa_is_admin());

create or replace function private.saree_write_audit_event()
returns trigger language plpgsql security definer set search_path=''
as $$
declare v_old jsonb; v_new jsonb; v_id text;
begin
 if tg_op='INSERT' then v_new:=to_jsonb(new); v_id:=coalesce(v_new->>'id',v_new->>'user_id'); 
 elsif tg_op='UPDATE' then v_old:=to_jsonb(old); v_new:=to_jsonb(new); v_id:=coalesce(v_new->>'id',v_new->>'user_id');
 else v_old:=to_jsonb(old); v_id:=coalesce(v_old->>'id',v_old->>'user_id'); end if;
 insert into public.saree_audit_events(actor_id,table_name,record_id,action,old_data,new_data)
 values(auth.uid(),tg_table_name,v_id,tg_op,v_old,v_new);
 if tg_op='DELETE' then return old; else return new; end if;
end $$;
revoke all on function private.saree_write_audit_event() from public,anon,authenticated;

drop trigger if exists saree_audit_products on public.products;
create trigger saree_audit_products after insert or update or delete on public.products
 for each row execute function private.saree_write_audit_event();
drop trigger if exists saree_audit_merchants on public.merchants;
create trigger saree_audit_merchants after insert or update or delete on public.merchants
 for each row execute function private.saree_write_audit_event();
drop trigger if exists saree_audit_orders on public.orders;
create trigger saree_audit_orders after insert or update or delete on public.orders
 for each row execute function private.saree_write_audit_event();

create or replace function public.saree_admin_review_refund(
 p_refund_id uuid,p_approve boolean,p_note text default null
) returns void language plpgsql security invoker set search_path=''
as $$
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 update public.saree_refund_requests
 set status=case when p_approve then 'approved' else 'rejected' end,
     admin_note=p_note,reviewed_by=auth.uid(),reviewed_at=now()
 where id=p_refund_id and status='pending';
 if not found then raise exception 'refund request unavailable'; end if;
end $$;
revoke all on function public.saree_admin_review_refund(uuid,boolean,text) from public,anon;
grant execute on function public.saree_admin_review_refund(uuid,boolean,text) to authenticated;

create or replace function public.saree_admin_set_role_feature(
 p_role text,p_feature text,p_enabled boolean
) returns void language plpgsql security invoker set search_path=''
as $$
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 if p_role not in ('customer','driver','merchant') then raise exception 'invalid role'; end if;
 if length(trim(coalesce(p_feature,'')))<2 then raise exception 'invalid feature'; end if;
 insert into public.saree_role_feature_permissions(app_role,feature_key,enabled,updated_by)
 values(p_role,p_feature,p_enabled,auth.uid())
 on conflict(app_role,feature_key) do update
 set enabled=excluded.enabled,updated_by=auth.uid(),updated_at=now();
end $$;
revoke all on function public.saree_admin_set_role_feature(text,text,boolean) from public,anon;
grant execute on function public.saree_admin_set_role_feature(text,text,boolean) to authenticated;

create or replace function public.saree_admin_review_alternative(
 p_alternative_id uuid,p_approve boolean,p_note text default null
) returns void language plpgsql security invoker set search_path=''
as $$
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 update public.saree_product_alternatives
 set pharmacist_reviewed=p_approve,is_active=p_approve,review_note=p_note,
     reviewed_by=auth.uid(),reviewed_at=now()
 where id=p_alternative_id;
 if not found then raise exception 'alternative unavailable'; end if;
end $$;
revoke all on function public.saree_admin_review_alternative(uuid,boolean,text) from public,anon;
grant execute on function public.saree_admin_review_alternative(uuid,boolean,text) to authenticated;

-- Admin/merchant stock view: batches expiring within 90 days are highlighted in the admin UI.
