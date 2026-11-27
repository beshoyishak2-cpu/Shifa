-- Locking must remove the courier from the available queue; settlement confirmation restores availability.
create or replace function private.saree_assert_courier_can_work(p_courier_id uuid)
returns void language plpgsql security definer set search_path=public,private as $$
declare v_cfg public.saree_commission_settings%rowtype; v_due numeric;
begin
 if auth.uid() is null or auth.uid()<>p_courier_id then raise exception 'courier identity mismatch'; end if;
 select * into v_cfg from public.saree_commission_settings where id=true;
 select coalesce(amount_due,0) into v_due from public.courier_settlement_accounts where courier_id=p_courier_id;
 if v_cfg.auto_lock_enabled and exists(select 1 from public.courier_profiles where user_id=p_courier_id and locked_for_settlement) then
   update public.courier_profiles set is_available=false where user_id=p_courier_id;
   raise exception 'locked_for_settlement';
 end if;
 if v_cfg.auto_lock_enabled and v_cfg.max_debt>0 and coalesce(v_due,0)>=v_cfg.max_debt then
   update public.courier_profiles set locked_for_settlement=true,is_available=false,settlement_locked_at=coalesce(settlement_locked_at,now()) where user_id=p_courier_id;
   raise exception 'locked_for_settlement';
 end if;
 if v_cfg.auto_lock_enabled and timezone('Africa/Cairo',now())::time>=v_cfg.daily_due_time and coalesce(v_due,0)>0 then
   update public.courier_profiles set locked_for_settlement=true,is_available=false,settlement_locked_at=coalesce(settlement_locked_at,now()) where user_id=p_courier_id;
   raise exception 'locked_for_settlement';
 end if;
end $$;
grant execute on function private.saree_assert_courier_can_work(uuid) to authenticated;

create or replace function private.saree_auto_lock_overdue_couriers()
returns integer language plpgsql security definer set search_path=public,private as $$
declare v_cfg public.saree_commission_settings%rowtype; v_count integer;
begin
 select * into v_cfg from public.saree_commission_settings where id=true;
 if not coalesce(v_cfg.auto_lock_enabled,false) then return 0; end if;
 update public.courier_profiles cp
 set locked_for_settlement=true,is_available=false,settlement_locked_at=coalesce(cp.settlement_locked_at,now())
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

create or replace function private.saree_confirm_courier_settlement(p_settlement_id uuid,p_note text default null)
returns void language plpgsql security definer set search_path=public,private as $$
declare v public.courier_settlements%rowtype;
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 select * into v from public.courier_settlements where id=p_settlement_id for update;
 if not found or v.status<>'pending' then raise exception 'settlement request unavailable'; end if;
 update public.courier_settlements set status='confirmed',note=coalesce(p_note,note),reviewed_by=auth.uid(),reviewed_at=now() where id=p_settlement_id;
 update public.courier_settlement_accounts set amount_due=greatest(0,amount_due-v.amount),last_settled_at=now(),updated_at=now() where courier_id=v.courier_id;
 update public.courier_profiles set locked_for_settlement=false,settlement_locked_at=null,is_available=is_verified where user_id=v.courier_id;
end $$;
grant execute on function private.saree_confirm_courier_settlement(uuid,text) to authenticated;
