-- Shifa: complete core customer, support, merchant-hours and courier-live workflows.
-- Additive only: no existing rows or tables are removed.
alter table public.support_tickets
  add column if not exists admin_reply text,
  add column if not exists replied_at timestamptz,
  add column if not exists updated_at timestamptz not null default now();

create table if not exists public.customer_favorites (
  customer_id uuid not null references public.profiles(id) on delete cascade,
  product_id uuid not null references public.products(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (customer_id, product_id)
);
alter table public.customer_favorites enable row level security;
create policy "customers manage own favorites" on public.customer_favorites for all to authenticated
  using (customer_id = (select auth.uid())) with check (customer_id = (select auth.uid()));
grant select, insert, delete on public.customer_favorites to authenticated;

create table if not exists public.product_reviews (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles(id) on delete cascade,
  merchant_id uuid not null references public.merchants(id) on delete cascade,
  product_id uuid not null references public.products(id) on delete cascade,
  order_id uuid not null references public.orders(id) on delete cascade,
  rating smallint not null check (rating between 1 and 5),
  comment text not null default '' check (length(comment) <= 1200),
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  reviewed_by uuid references public.profiles(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  unique (order_id, product_id)
);
create index if not exists product_reviews_product_status_idx on public.product_reviews(product_id, status, created_at desc);
create index if not exists product_reviews_customer_idx on public.product_reviews(customer_id, created_at desc);
alter table public.product_reviews enable row level security;
create policy "public reads approved product reviews" on public.product_reviews for select to anon, authenticated using (status = 'approved');
create policy "customers read own product reviews" on public.product_reviews for select to authenticated
  using (customer_id = (select auth.uid()) or (select private.shifa_is_admin()));
grant select on public.product_reviews to anon, authenticated;

create or replace function public.submit_product_review(p_order_id uuid,p_product_id uuid,p_rating smallint,p_comment text default '')
returns uuid language plpgsql security definer set search_path = ''
as $$
declare v_merchant_id uuid; v_review_id uuid;
begin
  if auth.uid() is null then raise exception 'authentication required' using errcode='28000'; end if;
  if p_rating < 1 or p_rating > 5 then raise exception 'rating must be from 1 to 5' using errcode='22023'; end if;
  if length(coalesce(p_comment,'')) > 1200 then raise exception 'review is too long' using errcode='22023'; end if;
  select o.merchant_id into v_merchant_id from public.orders o
  where o.id=p_order_id and o.customer_id=auth.uid() and o.status='delivered'::public.shifa_order_status;
  if v_merchant_id is null then raise exception 'only the customer of a delivered order can review it' using errcode='42501'; end if;
  if not exists(select 1 from public.order_items oi join public.products p on p.id=oi.product_id
    where oi.order_id=p_order_id and oi.product_id=p_product_id and p.merchant_id=v_merchant_id) then
    raise exception 'product is not part of this order' using errcode='22023';
  end if;
  insert into public.product_reviews(customer_id,merchant_id,product_id,order_id,rating,comment)
  values(auth.uid(),v_merchant_id,p_product_id,p_order_id,p_rating,coalesce(trim(p_comment),'')) returning id into v_review_id;
  return v_review_id;
end;
$$;
revoke all on function public.submit_product_review(uuid,uuid,smallint,text) from public, anon;
grant execute on function public.submit_product_review(uuid,uuid,smallint,text) to authenticated;

create or replace function public.admin_review_product_review(p_review_id uuid,p_approve boolean)
returns void language plpgsql security definer set search_path = ''
as $$
begin
  if not coalesce(private.shifa_is_admin(),false) then raise exception 'admin access required' using errcode='42501'; end if;
  update public.product_reviews set status=case when p_approve then 'approved' else 'rejected' end,
    reviewed_by=auth.uid(),reviewed_at=now() where id=p_review_id;
  if not found then raise exception 'review not found' using errcode='P0002'; end if;
end;
$$;
revoke all on function public.admin_review_product_review(uuid,boolean) from public, anon;
grant execute on function public.admin_review_product_review(uuid,boolean) to authenticated;

create table if not exists public.merchant_business_hours (
  id uuid primary key default gen_random_uuid(),
  merchant_id uuid not null references public.merchants(id) on delete cascade,
  day_of_week smallint not null check (day_of_week between 0 and 6),
  opens_at time,
  closes_at time,
  is_closed boolean not null default false,
  updated_at timestamptz not null default now(),
  unique (merchant_id,day_of_week),
  check (is_closed or (opens_at is not null and closes_at is not null and opens_at <> closes_at))
);
create index if not exists merchant_business_hours_merchant_idx on public.merchant_business_hours(merchant_id,day_of_week);
alter table public.merchant_business_hours enable row level security;
create policy "public reads active merchant hours" on public.merchant_business_hours for select to anon, authenticated
  using (exists(select 1 from public.merchants m where m.id=merchant_id and m.is_active));
create policy "merchant members manage own business hours" on public.merchant_business_hours for all to authenticated
  using ((select private.shifa_is_admin()) or (select private.shifa_is_merchant_member(merchant_id)))
  with check ((select private.shifa_is_admin()) or (select private.shifa_is_merchant_member(merchant_id)));
grant select on public.merchant_business_hours to anon, authenticated;
grant insert, update, delete on public.merchant_business_hours to authenticated;

create table if not exists public.courier_live_locations (
  courier_id uuid primary key references public.courier_profiles(user_id) on delete cascade,
  latitude double precision not null check (latitude between -90 and 90),
  longitude double precision not null check (longitude between -180 and 180),
  heading double precision check (heading is null or heading between 0 and 360),
  speed_mps double precision check (speed_mps is null or speed_mps >= 0),
  accuracy_m double precision check (accuracy_m is null or accuracy_m >= 0),
  updated_at timestamptz not null default now()
);
create index if not exists courier_live_locations_updated_idx on public.courier_live_locations(updated_at desc);
alter table public.courier_live_locations enable row level security;
create policy "couriers and assigned order participants read live location" on public.courier_live_locations for select to authenticated
  using (
    courier_id=(select auth.uid()) or (select private.shifa_is_admin())
    or exists(select 1 from public.orders o where o.courier_id=courier_live_locations.courier_id
      and o.status in ('accepted','preparing','ready_for_pickup','picked_up')
      and (o.customer_id=(select auth.uid()) or exists(select 1 from public.merchant_members mm
        where mm.merchant_id=o.merchant_id and mm.user_id=(select auth.uid()))))
  );
grant select on public.courier_live_locations to authenticated;

create or replace function public.set_courier_live_location(
  p_latitude double precision,p_longitude double precision,p_heading double precision default null,
  p_speed_mps double precision default null,p_accuracy_m double precision default null
) returns timestamptz language plpgsql security definer set search_path = ''
as $$
declare v_updated_at timestamptz := now();
begin
  if auth.uid() is null then raise exception 'authentication required' using errcode='28000'; end if;
  if p_latitude is null or p_latitude not between -90 and 90 or p_longitude is null or p_longitude not between -180 and 180 then
    raise exception 'invalid coordinates' using errcode='22023';
  end if;
  if not exists(select 1 from public.courier_profiles cp where cp.user_id=auth.uid() and cp.is_verified and cp.is_available and not cp.locked_for_settlement) then
    raise exception 'verified available courier required' using errcode='42501';
  end if;
  insert into public.courier_live_locations(courier_id,latitude,longitude,heading,speed_mps,accuracy_m,updated_at)
  values(auth.uid(),p_latitude,p_longitude,p_heading,p_speed_mps,p_accuracy_m,v_updated_at)
  on conflict(courier_id) do update set latitude=excluded.latitude,longitude=excluded.longitude,heading=excluded.heading,
    speed_mps=excluded.speed_mps,accuracy_m=excluded.accuracy_m,updated_at=excluded.updated_at;
  return v_updated_at;
end;
$$;
revoke all on function public.set_courier_live_location(double precision,double precision,double precision,double precision,double precision) from public, anon;
grant execute on function public.set_courier_live_location(double precision,double precision,double precision,double precision,double precision) to authenticated;

create table if not exists public.user_notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  title text not null check (length(title) between 1 and 160),
  body text not null default '' check (length(body) <= 1200),
  kind text not null default 'general',
  related_id uuid,
  read_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists user_notifications_user_created_idx on public.user_notifications(user_id,created_at desc);
alter table public.user_notifications enable row level security;
create policy "users read own notifications" on public.user_notifications for select to authenticated using (user_id=(select auth.uid()));
create policy "users mark own notifications read" on public.user_notifications for update to authenticated
  using (user_id=(select auth.uid())) with check (user_id=(select auth.uid()));
grant select on public.user_notifications to authenticated;
grant update(read_at) on public.user_notifications to authenticated;

create table if not exists public.push_device_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  device_token text not null unique,
  platform text not null check (platform in ('android','ios','web')),
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create index if not exists push_device_tokens_user_idx on public.push_device_tokens(user_id);
alter table public.push_device_tokens enable row level security;
create policy "users manage own push tokens" on public.push_device_tokens for all to authenticated
  using (user_id=(select auth.uid())) with check (user_id=(select auth.uid()));
grant select, insert, update, delete on public.push_device_tokens to authenticated;

create or replace function public.admin_reply_support_ticket(
  p_ticket_id uuid,p_reply text,p_status public.shifa_ticket_status default 'in_progress'
) returns void language plpgsql security definer set search_path = ''
as $$
declare v_customer_id uuid; v_subject text;
begin
  if not coalesce(private.shifa_is_admin(),false) then raise exception 'admin access required' using errcode='42501'; end if;
  if length(trim(coalesce(p_reply,'')))<2 or length(p_reply)>4000 then raise exception 'reply must contain 2 to 4000 characters' using errcode='22023'; end if;
  if p_status not in ('open','in_progress','resolved','closed') then raise exception 'invalid ticket status' using errcode='22023'; end if;
  update public.support_tickets set admin_reply=trim(p_reply),replied_at=now(),updated_at=now(),status=p_status
    where id=p_ticket_id returning customer_id,subject into v_customer_id,v_subject;
  if not found then raise exception 'ticket not found' using errcode='P0002'; end if;
  insert into public.user_notifications(user_id,title,body,kind,related_id)
    values(v_customer_id,'رد جديد من دعم سريع','تم الرد على شكواك: '||v_subject,'support_reply',p_ticket_id);
end;
$$;
revoke all on function public.admin_reply_support_ticket(uuid,text,public.shifa_ticket_status) from public, anon;
grant execute on function public.admin_reply_support_ticket(uuid,text,public.shifa_ticket_status) to authenticated;

create or replace function private.shifa_notify_product_review_status()
returns trigger language plpgsql security definer set search_path = ''
as $$
begin
  if new.status is distinct from old.status and new.status in ('approved','rejected') then
    insert into public.user_notifications(user_id,title,body,kind,related_id)
    values(new.customer_id,case when new.status='approved' then 'تم اعتماد تقييمك' else 'تقييمك يحتاج إلى مراجعة' end,
      case when new.status='approved' then 'تم نشر تقييمك للمنتج.' else 'لم يتم نشر تقييمك. يمكنك التواصل مع الدعم.' end,'review_status',new.id);
  end if;
  return new;
end;
$$;
drop trigger if exists shifa_product_review_status_notify on public.product_reviews;
create trigger shifa_product_review_status_notify after update of status on public.product_reviews
for each row execute function private.shifa_notify_product_review_status();

create or replace function private.shifa_support_ticket_updated_at()
returns trigger language plpgsql security definer set search_path = ''
as $$ begin new.updated_at:=now(); return new; end; $$;
drop trigger if exists shifa_support_ticket_updated_at on public.support_tickets;
create trigger shifa_support_ticket_updated_at before update on public.support_tickets
for each row execute function private.shifa_support_ticket_updated_at();

do $$
begin
  if exists(select 1 from pg_publication where pubname='supabase_realtime') then
    begin alter publication supabase_realtime add table public.user_notifications; exception when duplicate_object then null; end;
    begin alter publication supabase_realtime add table public.courier_live_locations; exception when duplicate_object then null; end;
  end if;
end;
$$;
