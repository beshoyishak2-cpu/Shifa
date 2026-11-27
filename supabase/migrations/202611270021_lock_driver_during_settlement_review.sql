-- Freeze the courier while a settlement receipt is awaiting admin confirmation.
create or replace function private.saree_submit_driver_settlement(p_receipt_path text)
returns uuid language plpgsql security definer set search_path=public,private as $$
declare v_due numeric(12,2); v_id uuid;
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 if length(trim(coalesce(p_receipt_path,'')))<4 or p_receipt_path not like auth.uid()::text||'/%' then raise exception 'settlement receipt must belong to this driver'; end if;
 select amount_due into v_due from public.courier_settlement_accounts where courier_id=auth.uid() for update;
 if coalesce(v_due,0)<=0 then raise exception 'no outstanding settlement'; end if;
 insert into public.courier_settlements(courier_id,amount,receipt_path) values(auth.uid(),v_due,p_receipt_path) returning id into v_id;
 update public.courier_profiles set locked_for_settlement=true,is_available=false,settlement_locked_at=coalesce(settlement_locked_at,now()) where user_id=auth.uid();
 return v_id;
end $$;
grant execute on function private.saree_submit_driver_settlement(text) to authenticated;
