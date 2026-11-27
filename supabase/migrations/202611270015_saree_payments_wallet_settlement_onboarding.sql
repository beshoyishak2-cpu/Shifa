-- Saree operational core: partner onboarding, payment proof, wallet ledger and courier settlement.
-- Idempotent DDL; all balance/dispatch mutations happen inside database transactions.

alter type public.shifa_payment_method add value if not exists 'mobile_wallet';
alter type public.shifa_payment_method add value if not exists 'instapay';
alter type public.shifa_payment_method add value if not exists 'wallet';

alter table public.orders
  add column if not exists payment_status text not null default 'unpaid'
    check (payment_status in ('unpaid','awaiting_review','paid','rejected','partially_paid')),
  add column if not exists wallet_amount numeric(10,2) not null default 0 check (wallet_amount >= 0),
  add column if not exists external_payment_amount numeric(10,2) not null default 0 check (external_payment_amount >= 0),
  add column if not exists payment_reference text;

alter table public.courier_profiles
  add column if not exists locked_for_settlement boolean not null default false,
  add column if not exists settlement_locked_at timestamptz;

create table if not exists public.saree_app_settings (
  id boolean primary key default true check (id),
  mobile_wallet_enabled boolean not null default true,
  instapay_enabled boolean not null default true,
  transfer_phone text not null default '01221236118',
  updated_at timestamptz not null default now(),
  updated_by uuid references public.profiles(id)
);
insert into public.saree_app_settings(id) values(true) on conflict(id) do nothing;

create table if not exists public.partner_applications (
  id uuid primary key default gen_random_uuid(),
  applicant_id uuid not null references public.profiles(id) on delete cascade,
  application_type text not null check(application_type in ('merchant','driver')),
  business_type text check(business_type in ('restaurant','pharmacy','cafe','grocery','vegetables')),
  display_name text not null check(length(trim(display_name)) between 2 and 160),
  phone text not null,
  area_name text not null default 'ملوي',
  address text,
  latitude double precision,
  longitude double precision,
  vehicle_type text,
  details jsonb not null default '{}'::jsonb,
  document_paths text[] not null default '{}',
  status text not null default 'pending' check(status in ('pending','approved','rejected')),
  rejection_reason text,
  reviewed_by uuid references public.profiles(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists partner_applications_pending_idx on public.partner_applications(status,created_at desc);

create table if not exists public.payment_receipts (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null unique references public.orders(id) on delete cascade,
  customer_id uuid not null references public.profiles(id),
  payment_method text not null check(payment_method in ('mobile_wallet','instapay')),
  amount numeric(10,2) not null check(amount > 0),
  storage_path text not null,
  status text not null default 'pending' check(status in ('pending','confirmed','rejected')),
  review_note text,
  reviewed_by uuid references public.profiles(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists payment_receipts_pending_idx on public.payment_receipts(status,created_at desc);

create table if not exists public.wallet_accounts (
  customer_id uuid primary key references public.profiles(id) on delete cascade,
  balance numeric(12,2) not null default 0 check(balance >= 0),
  updated_at timestamptz not null default now()
);
create table if not exists public.wallet_transactions (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles(id),
  direction text not null check(direction in ('credit','debit')),
  amount numeric(12,2) not null check(amount > 0),
  transaction_type text not null check(transaction_type in ('admin_credit','refund','promotion','order_payment','settlement_refund')),
  reference_id uuid,
  idempotency_key text unique,
  note text,
  created_by uuid references public.profiles(id),
  created_at timestamptz not null default now()
);
create index if not exists wallet_transactions_customer_idx on public.wallet_transactions(customer_id,created_at desc);

create table if not exists public.saree_commission_settings (
  id boolean primary key default true check(id),
  commission_mode text not null default 'percent' check(commission_mode in ('percent','fixed')),
  commission_value numeric(10,2) not null default 0 check(commission_value >= 0),
  daily_due_time time not null default '22:00',
  max_debt numeric(12,2) not null default 500 check(max_debt >= 0),
  auto_lock_enabled boolean not null default true,
  transfer_phone text not null default '01221236118',
  updated_at timestamptz not null default now(),
  updated_by uuid references public.profiles(id)
);
insert into public.saree_commission_settings(id) values(true) on conflict(id) do nothing;

create table if not exists public.courier_settlement_accounts (
  courier_id uuid primary key references public.courier_profiles(user_id) on delete cascade,
  amount_due numeric(12,2) not null default 0 check(amount_due >= 0),
  last_settled_at timestamptz,
  updated_at timestamptz not null default now()
);
create table if not exists public.courier_commissions (
  id uuid primary key default gen_random_uuid(),
  courier_id uuid not null references public.courier_profiles(user_id),
  order_id uuid not null unique references public.orders(id),
  order_total numeric(10,2) not null,
  commission_amount numeric(10,2) not null check(commission_amount >= 0),
  created_at timestamptz not null default now()
);
create index if not exists courier_commissions_driver_idx on public.courier_commissions(courier_id,created_at desc);

create table if not exists public.courier_settlements (
  id uuid primary key default gen_random_uuid(),
  courier_id uuid not null references public.courier_profiles(user_id),
  amount numeric(12,2) not null check(amount > 0),
  receipt_path text,
  status text not null default 'pending' check(status in ('pending','confirmed','rejected')),
  note text,
  reviewed_by uuid references public.profiles(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists courier_settlements_pending_idx on public.courier_settlements(status,created_at desc);

create table if not exists public.courier_order_cancellations (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id),
  courier_id uuid not null references public.courier_profiles(user_id),
  reason text not null check(length(trim(reason)) between 2 and 300),
  created_at timestamptz not null default now()
);

-- RLS: sensitive documents and receipts are private; admin review is explicit.
alter table public.saree_app_settings enable row level security;
alter table public.partner_applications enable row level security;
alter table public.payment_receipts enable row level security;
alter table public.wallet_accounts enable row level security;
alter table public.wallet_transactions enable row level security;
alter table public.saree_commission_settings enable row level security;
alter table public.courier_settlement_accounts enable row level security;
alter table public.courier_commissions enable row level security;
alter table public.courier_settlements enable row level security;
alter table public.courier_order_cancellations enable row level security;

drop policy if exists "saree settings public read" on public.saree_app_settings;
create policy "saree settings public read" on public.saree_app_settings for select to anon,authenticated using(true);
create policy "saree settings admin update" on public.saree_app_settings for update to authenticated using(private.shifa_is_admin()) with check(private.shifa_is_admin());
create policy "partner application own or admin read" on public.partner_applications for select to authenticated using(applicant_id=(select auth.uid()) or private.shifa_is_admin());
create policy "partner application own insert" on public.partner_applications for insert to authenticated with check(applicant_id=(select auth.uid()) and status='pending' and reviewed_by is null);
create policy "partner application admin update" on public.partner_applications for update to authenticated using(private.shifa_is_admin()) with check(private.shifa_is_admin());
create policy "payment receipt participants read" on public.payment_receipts for select to authenticated using(customer_id=(select auth.uid()) or private.shifa_is_admin() or exists(select 1 from public.orders o where o.id=order_id and (o.courier_id=(select auth.uid()) or private.shifa_is_merchant_member(o.merchant_id))));
create policy "customer submits payment receipt" on public.payment_receipts for insert to authenticated with check(customer_id=(select auth.uid()) and status='pending' and reviewed_by is null and exists(select 1 from public.orders o where o.id=order_id and o.customer_id=(select auth.uid())));
create policy "admin reviews payment receipts" on public.payment_receipts for update to authenticated using(private.shifa_is_admin()) with check(private.shifa_is_admin());
create policy "wallet account own read" on public.wallet_accounts for select to authenticated using(customer_id=(select auth.uid()) or private.shifa_is_admin());
create policy "wallet transactions own read" on public.wallet_transactions for select to authenticated using(customer_id=(select auth.uid()) or private.shifa_is_admin());
create policy "commission settings admin all" on public.saree_commission_settings for all to authenticated using(private.shifa_is_admin()) with check(private.shifa_is_admin());
create policy "settlement accounts driver or admin read" on public.courier_settlement_accounts for select to authenticated using(courier_id=(select auth.uid()) or private.shifa_is_admin());
create policy "commissions driver or admin read" on public.courier_commissions for select to authenticated using(courier_id=(select auth.uid()) or private.shifa_is_admin());
create policy "settlements driver or admin read" on public.courier_settlements for select to authenticated using(courier_id=(select auth.uid()) or private.shifa_is_admin());
create policy "driver creates settlement request" on public.courier_settlements for insert to authenticated with check(courier_id=(select auth.uid()) and status='pending' and reviewed_by is null);
create policy "admin updates settlements" on public.courier_settlements for update to authenticated using(private.shifa_is_admin()) with check(private.shifa_is_admin());
create policy "driver cancellation history read" on public.courier_order_cancellations for select to authenticated using(courier_id=(select auth.uid()) or private.shifa_is_admin());

-- Clients cannot directly alter financial balances or commission ledgers.
revoke insert,update,delete on public.wallet_accounts,public.wallet_transactions,public.courier_settlement_accounts,public.courier_commissions from anon,authenticated;
revoke insert,update,delete on public.courier_order_cancellations from anon,authenticated;
revoke insert,update,delete on public.saree_commission_settings from anon,authenticated;
grant select on public.wallet_accounts,public.wallet_transactions,public.courier_settlement_accounts,public.courier_commissions,public.courier_settlements,public.courier_order_cancellations,public.saree_app_settings,public.partner_applications,public.payment_receipts to authenticated;
grant select on public.saree_app_settings to anon;

-- Private RPC: admin-only wallet credit with idempotency and a ledger row.
create or replace function private.saree_wallet_credit(p_customer_id uuid,p_amount numeric,p_type text,p_note text,p_reference_id uuid default null,p_idempotency_key text default null)
returns numeric language plpgsql security definer set search_path=public,private as $$
declare v_balance numeric(12,2);
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 if p_amount is null or p_amount<=0 or p_type not in ('admin_credit','refund','promotion','settlement_refund') then raise exception 'invalid wallet credit'; end if;
 if p_idempotency_key is not null and exists(select 1 from public.wallet_transactions where idempotency_key=p_idempotency_key) then
   select balance into v_balance from public.wallet_accounts where customer_id=p_customer_id;
   return coalesce(v_balance,0);
 end if;
 insert into public.wallet_accounts(customer_id,balance) values(p_customer_id,0) on conflict(customer_id) do nothing;
 update public.wallet_accounts set balance=balance+p_amount,updated_at=now() where customer_id=p_customer_id returning balance into v_balance;
 insert into public.wallet_transactions(customer_id,direction,amount,transaction_type,reference_id,idempotency_key,note,created_by)
 values(p_customer_id,'credit',p_amount,p_type,p_reference_id,p_idempotency_key,p_note,auth.uid());
 return v_balance;
end $$;
revoke all on function private.saree_wallet_credit(uuid,numeric,text,text,uuid,text) from public,anon,authenticated;
create or replace function public.saree_admin_credit_wallet(p_customer_id uuid,p_amount numeric,p_type text,p_note text,p_reference_id uuid default null,p_idempotency_key text default null)
returns numeric language sql security invoker set search_path=public as $$
 select private.saree_wallet_credit(p_customer_id,p_amount,p_type,p_note,p_reference_id,p_idempotency_key)
$$;
grant execute on function public.saree_admin_credit_wallet(uuid,numeric,text,text,uuid,text) to authenticated;

-- Admin confirms/rejects external payment; only confirmation changes the order to paid.
create or replace function private.saree_review_payment(p_receipt_id uuid,p_approve boolean,p_note text default null)
returns void language plpgsql security definer set search_path=public,private as $$
declare v public.payment_receipts%rowtype;
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 select * into v from public.payment_receipts where id=p_receipt_id for update;
 if not found or v.status<>'pending' then raise exception 'receipt unavailable'; end if;
 update public.payment_receipts set status=case when p_approve then 'confirmed' else 'rejected' end,review_note=p_note,reviewed_by=auth.uid(),reviewed_at=now() where id=p_receipt_id;
 update public.orders set payment_status=case when p_approve then 'paid' else 'rejected' end,updated_at=now() where id=v.order_id;
end $$;
revoke all on function private.saree_review_payment(uuid,boolean,text) from public,anon,authenticated;
create or replace function public.saree_admin_review_payment(p_receipt_id uuid,p_approve boolean,p_note text default null)
returns void language sql security invoker set search_path=public as $$
 select private.saree_review_payment(p_receipt_id,p_approve,p_note)
$$;
grant execute on function public.saree_admin_review_payment(uuid,boolean,text) to authenticated;

-- Atomic courier cancellation before pickup, returning the job to the shared queue.
create or replace function private.saree_cancel_claimed_order(p_order_id uuid,p_reason text)
returns void language plpgsql security definer set search_path=public,private as $$
declare v public.orders%rowtype;
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 if length(trim(coalesce(p_reason,'')))<2 then raise exception 'cancellation reason required'; end if;
 select * into v from public.orders where id=p_order_id for update;
 if not found or v.courier_id<>auth.uid() or v.status<>'ready_for_pickup' then raise exception 'order cannot be released after pickup'; end if;
 insert into public.courier_order_cancellations(order_id,courier_id,reason) values(p_order_id,auth.uid(),trim(p_reason));
 update public.orders set courier_id=null,updated_at=now() where id=p_order_id;
 insert into public.order_status_events(order_id,changed_by,old_status,new_status,note) values(p_order_id,auth.uid(),v.status,v.status,'Courier released order: '||trim(p_reason));
end $$;
revoke all on function private.saree_cancel_claimed_order(uuid,text) from public,anon,authenticated;
create or replace function public.saree_driver_release_order(p_order_id uuid,p_reason text)
returns void language sql security invoker set search_path=public as $$
 select private.saree_cancel_claimed_order(p_order_id,p_reason)
$$;
grant execute on function public.saree_driver_release_order(uuid,text) to authenticated;

-- Record commission exactly once when an order is delivered.
create or replace function private.saree_record_delivery_commission()
returns trigger language plpgsql security definer set search_path=public,private as $$
declare v_cfg public.saree_commission_settings%rowtype; v_amount numeric(12,2);
begin
 if new.status='delivered' and old.status is distinct from new.status and new.courier_id is not null then
   select * into v_cfg from public.saree_commission_settings where id=true;
   v_amount:=case when v_cfg.commission_mode='fixed' then v_cfg.commission_value else round(new.total*v_cfg.commission_value/100,2) end;
   insert into public.courier_settlement_accounts(courier_id,amount_due) values(new.courier_id,0) on conflict(courier_id) do nothing;
   insert into public.courier_commissions(courier_id,order_id,order_total,commission_amount) values(new.courier_id,new.id,new.total,v_amount) on conflict(order_id) do nothing;
   if found then
     update public.courier_settlement_accounts set amount_due=amount_due+v_amount,updated_at=now() where courier_id=new.courier_id;
     if v_cfg.auto_lock_enabled and v_cfg.max_debt>0 and (select amount_due from public.courier_settlement_accounts where courier_id=new.courier_id)>=v_cfg.max_debt then
       update public.courier_profiles set locked_for_settlement=true,settlement_locked_at=now() where user_id=new.courier_id;
     end if;
   end if;
 end if;
 return new;
end $$;
drop trigger if exists saree_delivery_commission_trigger on public.orders;
create trigger saree_delivery_commission_trigger after update of status on public.orders for each row execute function private.saree_record_delivery_commission();

-- Admin confirms settlement: ledger is retained, due is cleared, courier is unlocked.
create or replace function private.saree_confirm_courier_settlement(p_settlement_id uuid,p_note text default null)
returns void language plpgsql security definer set search_path=public,private as $$
declare v public.courier_settlements%rowtype;
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 select * into v from public.courier_settlements where id=p_settlement_id for update;
 if not found or v.status<>'pending' then raise exception 'settlement request unavailable'; end if;
 update public.courier_settlements set status='confirmed',note=coalesce(p_note,note),reviewed_by=auth.uid(),reviewed_at=now() where id=p_settlement_id;
 update public.courier_settlement_accounts set amount_due=greatest(0,amount_due-v.amount),last_settled_at=now(),updated_at=now() where courier_id=v.courier_id;
 update public.courier_profiles set locked_for_settlement=false,settlement_locked_at=null where user_id=v.courier_id;
end $$;
revoke all on function private.saree_confirm_courier_settlement(uuid,text) from public,anon,authenticated;
create or replace function public.saree_admin_confirm_settlement(p_settlement_id uuid,p_note text default null)
returns void language sql security invoker set search_path=public as $$
 select private.saree_confirm_courier_settlement(p_settlement_id,p_note)
$$;
grant execute on function public.saree_admin_confirm_settlement(uuid,text) to authenticated;

-- Claim guard: the existing row-locking RPC remains first-come-first-served.
create or replace function private.saree_assert_courier_can_work(p_courier_id uuid)
returns void language plpgsql security definer set search_path=public,private as $$
declare v_cfg public.saree_commission_settings%rowtype; v_due numeric;
begin
 select * into v_cfg from public.saree_commission_settings where id=true;
 select coalesce(amount_due,0) into v_due from public.courier_settlement_accounts where courier_id=p_courier_id;
 if v_cfg.auto_lock_enabled and exists(select 1 from public.courier_profiles where user_id=p_courier_id and locked_for_settlement) then raise exception 'locked_for_settlement'; end if;
 if v_cfg.auto_lock_enabled and v_cfg.max_debt>0 and coalesce(v_due,0)>=v_cfg.max_debt then
   update public.courier_profiles set locked_for_settlement=true,settlement_locked_at=coalesce(settlement_locked_at,now()) where user_id=p_courier_id;
   raise exception 'locked_for_settlement';
 end if;
 if v_cfg.auto_lock_enabled and localtime>=v_cfg.daily_due_time and coalesce(v_due,0)>0 then
   update public.courier_profiles set locked_for_settlement=true,settlement_locked_at=coalesce(settlement_locked_at,now()) where user_id=p_courier_id;
   raise exception 'locked_for_settlement';
 end if;
end $$;
revoke all on function private.saree_assert_courier_can_work(uuid) from public,anon,authenticated;

-- Wrap the atomic claim operation with settlement eligibility; its existing implementation still locks the order row.
create or replace function public.saree_claim_order(p_order_id uuid)
returns void language plpgsql security invoker set search_path=public,private as $$
begin
 perform private.saree_assert_courier_can_work(auth.uid());
 perform private.claim_shifa_order(p_order_id);
end $$;
revoke all on function public.saree_claim_order(uuid) from public,anon;
grant execute on function public.saree_claim_order(uuid) to authenticated;

-- Storage buckets: private by default; folder 1 must be the uploader's auth uid.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values
 ('partner-documents','partner-documents',false,10485760,array['image/jpeg','image/png','application/pdf']),
 ('payment-receipts','payment-receipts',false,5242880,array['image/jpeg','image/png','image/webp'])
on conflict(id) do update set public=false,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;

drop policy if exists "saree partner docs owner upload" on storage.objects;
create policy "saree partner docs owner upload" on storage.objects for insert to authenticated
with check(bucket_id='partner-documents' and (storage.foldername(name))[1]=(select auth.uid())::text);
drop policy if exists "saree partner docs owner or admin read" on storage.objects;
create policy "saree partner docs owner or admin read" on storage.objects for select to authenticated
using(bucket_id='partner-documents' and ((storage.foldername(name))[1]=(select auth.uid())::text or private.shifa_is_admin()));
drop policy if exists "saree payment receipt owner upload" on storage.objects;
create policy "saree payment receipt owner upload" on storage.objects for insert to authenticated
with check(bucket_id='payment-receipts' and (storage.foldername(name))[1]=(select auth.uid())::text);
drop policy if exists "saree payment receipt owner or admin read" on storage.objects;
create policy "saree payment receipt owner or admin read" on storage.objects for select to authenticated
using(bucket_id='payment-receipts' and ((storage.foldername(name))[1]=(select auth.uid())::text or private.shifa_is_admin()));

-- Realtime publication for operational screens; safe when tables are already members.
do $$ declare t text; begin
 foreach t in array array['orders','order_status_events','payment_receipts','partner_applications','wallet_accounts','wallet_transactions','courier_settlement_accounts','courier_settlements','courier_commissions','courier_order_cancellations','saree_app_settings','saree_commission_settings'] loop
  if not exists(select 1 from pg_publication_tables where pubname='supabase_realtime' and schemaname='public' and tablename=t) then
   execute format('alter publication supabase_realtime add table public.%I',t);
  end if;
 end loop;
end $$;
