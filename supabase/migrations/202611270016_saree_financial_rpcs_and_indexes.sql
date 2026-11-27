-- Saree security hardening and missing operational RPCs.
create index if not exists partner_applications_applicant_idx on public.partner_applications(applicant_id,created_at desc);
create index if not exists partner_applications_reviewed_by_idx on public.partner_applications(reviewed_by);
create index if not exists payment_receipts_customer_idx on public.payment_receipts(customer_id,created_at desc);
create index if not exists payment_receipts_reviewed_by_idx on public.payment_receipts(reviewed_by);
create index if not exists saree_settings_updated_by_idx on public.saree_app_settings(updated_by);
create index if not exists saree_commission_settings_updated_by_idx on public.saree_commission_settings(updated_by);
create index if not exists wallet_transactions_created_by_idx on public.wallet_transactions(created_by);
create index if not exists courier_settlements_courier_idx on public.courier_settlements(courier_id,created_at desc);
create index if not exists courier_settlements_reviewed_by_idx on public.courier_settlements(reviewed_by);
create index if not exists courier_order_cancellations_order_idx on public.courier_order_cancellations(order_id,created_at desc);
create index if not exists courier_order_cancellations_courier_idx on public.courier_order_cancellations(courier_id,created_at desc);

-- RPC implementations are deliberately callable only by authenticated users and validate the caller inside.
create or replace function private.saree_assert_courier_can_work(p_courier_id uuid)
returns void language plpgsql security definer set search_path=public,private as $$
declare v_cfg public.saree_commission_settings%rowtype; v_due numeric;
begin
 if auth.uid() is null or auth.uid()<>p_courier_id then raise exception 'courier identity mismatch'; end if;
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
grant execute on function private.saree_assert_courier_can_work(uuid) to authenticated;
grant execute on function private.saree_wallet_credit(uuid,numeric,text,text,uuid,text) to authenticated;
grant execute on function private.saree_review_payment(uuid,boolean,text) to authenticated;
grant execute on function private.saree_cancel_claimed_order(uuid,text) to authenticated;
grant execute on function private.saree_confirm_courier_settlement(uuid,text) to authenticated;

-- Keep the existing app RPC name, but enforce settlement lock before the atomic row-locking claim.
create or replace function public.claim_shifa_order(p_order_id uuid)
returns void language plpgsql security invoker set search_path=public,private as $$
begin
 perform private.saree_assert_courier_can_work(auth.uid());
 perform private.claim_shifa_order(p_order_id);
end $$;
grant execute on function public.claim_shifa_order(uuid) to authenticated;

-- Admin approval materializes the approved merchant or courier record from an application.
create or replace function private.saree_review_partner_application(p_application_id uuid,p_approve boolean,p_reason text default null)
returns void language plpgsql security definer set search_path=public,private as $$
declare v public.partner_applications%rowtype; v_merchant_id uuid;
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 select * into v from public.partner_applications where id=p_application_id for update;
 if not found or v.status<>'pending' then raise exception 'application unavailable'; end if;
 if not p_approve and length(trim(coalesce(p_reason,'')))<3 then raise exception 'rejection reason required'; end if;
 if p_approve then
   if v.application_type='merchant' then
     insert into public.merchants(name,description,phone,address,is_active,service_type,area_name,is_open)
     values(v.display_name,coalesce(v.details->>'description',''),v.phone,coalesce(v.address,''),true,coalesce(v.business_type,'restaurant'),v.area_name,true)
     returning id into v_merchant_id;
     insert into public.merchant_members(merchant_id,user_id,member_role) values(v_merchant_id,v.applicant_id,'owner') on conflict do nothing;
     update public.profiles set role='merchant' where id=v.applicant_id;
   else
     insert into public.courier_profiles(user_id,vehicle_type,is_available,is_verified,locked_for_settlement)
     values(v.applicant_id,v.vehicle_type,false,true,false)
     on conflict(user_id) do update set vehicle_type=excluded.vehicle_type,is_verified=true;
     update public.profiles set role='driver' where id=v.applicant_id;
   end if;
   update public.partner_applications set status='approved',reviewed_by=auth.uid(),reviewed_at=now(),rejection_reason=null where id=p_application_id;
 else
   update public.partner_applications set status='rejected',rejection_reason=trim(p_reason),reviewed_by=auth.uid(),reviewed_at=now() where id=p_application_id;
 end if;
end $$;
revoke all on function private.saree_review_partner_application(uuid,boolean,text) from public,anon,authenticated;
create or replace function public.saree_admin_review_partner_application(p_application_id uuid,p_approve boolean,p_reason text default null)
returns void language plpgsql security invoker set search_path=public,private as $$
begin perform private.saree_review_partner_application(p_application_id,p_approve,p_reason); end $$;
grant execute on function private.saree_review_partner_application(uuid,boolean,text) to authenticated;
grant execute on function public.saree_admin_review_partner_application(uuid,boolean,text) to authenticated;

-- Driver submits a settlement receipt for the current due amount; client cannot choose the amount.
drop policy if exists "driver creates settlement request" on public.courier_settlements;
revoke insert on public.courier_settlements from anon,authenticated;
create or replace function private.saree_submit_driver_settlement(p_receipt_path text)
returns uuid language plpgsql security definer set search_path=public,private as $$
declare v_due numeric(12,2); v_id uuid;
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 if length(trim(coalesce(p_receipt_path,'')))<4 then raise exception 'settlement receipt required'; end if;
 select amount_due into v_due from public.courier_settlement_accounts where courier_id=auth.uid() for update;
 if coalesce(v_due,0)<=0 then raise exception 'no outstanding settlement'; end if;
 insert into public.courier_settlements(courier_id,amount,receipt_path) values(auth.uid(),v_due,p_receipt_path) returning id into v_id;
 return v_id;
end $$;
revoke all on function private.saree_submit_driver_settlement(text) from public,anon,authenticated;
create or replace function public.saree_driver_submit_settlement(p_receipt_path text)
returns uuid language plpgsql security invoker set search_path=public,private as $$
declare v uuid;
begin v:=private.saree_submit_driver_settlement(p_receipt_path); return v; end $$;
grant execute on function private.saree_submit_driver_settlement(text) to authenticated;
grant execute on function public.saree_driver_submit_settlement(text) to authenticated;

-- Apply wallet credit/debit only through transactional ledger RPCs.
create or replace function private.saree_apply_wallet_to_order(p_order_id uuid,p_amount numeric)
returns numeric language plpgsql security definer set search_path=public,private as $$
declare v_order public.orders%rowtype; v_balance numeric(12,2); v_new_balance numeric(12,2);
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 if p_amount is null or p_amount<=0 then raise exception 'invalid wallet amount'; end if;
 select * into v_order from public.orders where id=p_order_id for update;
 if not found or v_order.customer_id<>auth.uid() or v_order.status<>'pending' then raise exception 'order unavailable'; end if;
 if p_amount>v_order.total-v_order.wallet_amount then raise exception 'wallet amount exceeds order balance'; end if;
 select balance into v_balance from public.wallet_accounts where customer_id=auth.uid() for update;
 if coalesce(v_balance,0)<p_amount then raise exception 'insufficient wallet balance'; end if;
 update public.wallet_accounts set balance=balance-p_amount,updated_at=now() where customer_id=auth.uid() returning balance into v_new_balance;
 insert into public.wallet_transactions(customer_id,direction,amount,transaction_type,reference_id,note,created_by)
 values(auth.uid(),'debit',p_amount,'order_payment',p_order_id,'Wallet used for order',auth.uid());
 update public.orders set wallet_amount=wallet_amount+p_amount,payment_status=case when wallet_amount+p_amount>=total then 'paid' else 'partially_paid' end,updated_at=now() where id=p_order_id;
 return v_new_balance;
end $$;
revoke all on function private.saree_apply_wallet_to_order(uuid,numeric) from public,anon,authenticated;
create or replace function public.saree_apply_wallet_to_order(p_order_id uuid,p_amount numeric)
returns numeric language plpgsql security invoker set search_path=public,private as $$
begin return private.saree_apply_wallet_to_order(p_order_id,p_amount); end $$;
grant execute on function private.saree_apply_wallet_to_order(uuid,numeric) to authenticated;
grant execute on function public.saree_apply_wallet_to_order(uuid,numeric) to authenticated;

-- Attach external payment proof after checkout; feature flags and transfer settings are enforced server-side.
create or replace function private.saree_submit_order_payment(p_order_id uuid,p_method text,p_receipt_path text)
returns uuid language plpgsql security definer set search_path=public,private as $$
declare v_order public.orders%rowtype; v_cfg public.saree_app_settings%rowtype; v_amount numeric(10,2); v_id uuid;
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 select * into v_order from public.orders where id=p_order_id for update;
 if not found or v_order.customer_id<>auth.uid() or v_order.status<>'pending' then raise exception 'order unavailable'; end if;
 if p_method not in ('mobile_wallet','instapay') then raise exception 'unsupported external payment method'; end if;
 select * into v_cfg from public.saree_app_settings where id=true;
 if p_method='mobile_wallet' and not v_cfg.mobile_wallet_enabled then raise exception 'mobile wallet payment disabled'; end if;
 if p_method='instapay' and not v_cfg.instapay_enabled then raise exception 'InstaPay payment disabled'; end if;
 if length(trim(coalesce(p_receipt_path,'')))<4 then raise exception 'payment receipt required'; end if;
 if exists(select 1 from public.payment_receipts where order_id=p_order_id and status='pending') then raise exception 'payment receipt already submitted'; end if;
 v_amount:=greatest(0,v_order.total-v_order.wallet_amount);
 if v_amount<=0 then raise exception 'order already paid by wallet'; end if;
 update public.orders set payment_method=p_method::public.shifa_payment_method,external_payment_amount=v_amount,payment_status='awaiting_review',updated_at=now() where id=p_order_id;
 insert into public.payment_receipts(order_id,customer_id,payment_method,amount,storage_path)
 values(p_order_id,auth.uid(),p_method,v_amount,p_receipt_path) returning id into v_id;
 return v_id;
end $$;
revoke all on function private.saree_submit_order_payment(uuid,text,text) from public,anon,authenticated;
create or replace function public.saree_submit_order_payment(p_order_id uuid,p_method text,p_receipt_path text)
returns uuid language plpgsql security invoker set search_path=public,private as $$
declare v uuid;
begin v:=private.saree_submit_order_payment(p_order_id,p_method,p_receipt_path); return v; end $$;
grant execute on function private.saree_submit_order_payment(uuid,text,text) to authenticated;
grant execute on function public.saree_submit_order_payment(uuid,text,text) to authenticated;

-- Settings mutation remains administrator-only; clients can read feature flags and transfer number.
create or replace function private.saree_admin_update_payment_settings(p_wallet_enabled boolean,p_instapay_enabled boolean,p_transfer_phone text)
returns void language plpgsql security definer set search_path=public,private as $$
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 if length(trim(coalesce(p_transfer_phone,'')))<8 then raise exception 'valid transfer phone required'; end if;
 update public.saree_app_settings set mobile_wallet_enabled=p_wallet_enabled,instapay_enabled=p_instapay_enabled,transfer_phone=trim(p_transfer_phone),updated_by=auth.uid(),updated_at=now() where id=true;
end $$;
revoke all on function private.saree_admin_update_payment_settings(boolean,boolean,text) from public,anon,authenticated;
create or replace function public.saree_admin_update_payment_settings(p_wallet_enabled boolean,p_instapay_enabled boolean,p_transfer_phone text)
returns void language plpgsql security invoker set search_path=public,private as $$
begin perform private.saree_admin_update_payment_settings(p_wallet_enabled,p_instapay_enabled,p_transfer_phone); end $$;
grant execute on function private.saree_admin_update_payment_settings(boolean,boolean,text) to authenticated;

create or replace function private.saree_admin_update_commission_settings(p_mode text,p_value numeric,p_due_time time,p_max_debt numeric,p_auto_lock boolean,p_transfer_phone text)
returns void language plpgsql security definer set search_path=public,private as $$
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 if p_mode not in ('percent','fixed') or p_value<0 or (p_mode='percent' and p_value>100) or p_max_debt<0 or length(trim(coalesce(p_transfer_phone,'')))<8 then raise exception 'invalid commission settings'; end if;
 update public.saree_commission_settings set commission_mode=p_mode,commission_value=p_value,daily_due_time=p_due_time,max_debt=p_max_debt,auto_lock_enabled=p_auto_lock,transfer_phone=trim(p_transfer_phone),updated_by=auth.uid(),updated_at=now() where id=true;
end $$;
revoke all on function private.saree_admin_update_commission_settings(text,numeric,time,numeric,boolean,text) from public,anon,authenticated;
create or replace function public.saree_admin_update_commission_settings(p_mode text,p_value numeric,p_due_time time,p_max_debt numeric,p_auto_lock boolean,p_transfer_phone text)
returns void language plpgsql security invoker set search_path=public,private as $$
begin perform private.saree_admin_update_commission_settings(p_mode,p_value,p_due_time,p_max_debt,p_auto_lock,p_transfer_phone); end $$;
grant execute on function private.saree_admin_update_commission_settings(text,numeric,time,numeric,boolean,text) to authenticated;
grant execute on function public.saree_admin_update_commission_settings(text,numeric,time,numeric,boolean,text) to authenticated;
