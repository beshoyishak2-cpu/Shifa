-- Scheduled automatic settlement locks and financial idempotency safeguards.
create extension if not exists pg_cron;

create unique index if not exists one_pending_settlement_per_courier
on public.courier_settlements(courier_id) where status='pending';

create or replace function private.saree_auto_lock_overdue_couriers()
returns integer language plpgsql security definer set search_path=public,private as $$
declare v_cfg public.saree_commission_settings%rowtype; v_count integer;
begin
 select * into v_cfg from public.saree_commission_settings where id=true;
 if not coalesce(v_cfg.auto_lock_enabled,false) then return 0; end if;
 update public.courier_profiles cp
 set locked_for_settlement=true,settlement_locked_at=coalesce(cp.settlement_locked_at,now())
 where cp.locked_for_settlement=false
 and exists(select 1 from public.courier_settlement_accounts a where a.courier_id=cp.user_id and a.amount_due>0)
 and (
   (v_cfg.max_debt>0 and exists(select 1 from public.courier_settlement_accounts a where a.courier_id=cp.user_id and a.amount_due>=v_cfg.max_debt))
   or timezone('Africa/Cairo',now())::time >= v_cfg.daily_due_time
 );
 get diagnostics v_count=row_count;
 return v_count;
end $$;
revoke all on function private.saree_auto_lock_overdue_couriers() from public,anon,authenticated;

do $$
begin
 if exists(select 1 from pg_extension where extname='pg_cron') then
   perform cron.unschedule(jobid) from cron.job where jobname='saree-auto-lock-overdue-couriers';
   perform cron.schedule('saree-auto-lock-overdue-couriers','* * * * *','select private.saree_auto_lock_overdue_couriers();');
 end if;
end $$;

-- When the wallet covers the complete order, record the tender type explicitly.
create or replace function private.saree_apply_wallet_to_order(p_order_id uuid,p_amount numeric)
returns numeric language plpgsql security definer set search_path=public,private as $$
declare v_order public.orders%rowtype; v_balance numeric(12,2); v_new_balance numeric(12,2); v_new_wallet numeric(10,2);
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
 v_new_wallet:=v_order.wallet_amount+p_amount;
 update public.orders set wallet_amount=v_new_wallet,
 payment_status=case when v_new_wallet>=total then 'paid' else 'partially_paid' end,
 payment_method=case when v_new_wallet>=total then 'wallet'::public.shifa_payment_method else payment_method end,
 updated_at=now() where id=p_order_id;
 return v_new_balance;
end $$;
grant execute on function private.saree_apply_wallet_to_order(uuid,numeric) to authenticated;
