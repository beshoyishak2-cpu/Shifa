-- Explicit Data API grants for newly created tables and ownership validation for uploaded evidence.
grant select,insert on public.partner_applications to authenticated;
grant select,insert on public.payment_receipts to authenticated;
grant select on public.saree_commission_settings to authenticated;
grant select on public.saree_app_settings to authenticated,anon;
grant select on public.wallet_accounts,public.wallet_transactions,public.courier_settlement_accounts,public.courier_commissions,public.courier_settlements,public.courier_order_cancellations to authenticated;

drop policy if exists "partner application own insert" on public.partner_applications;
create policy "partner application own insert" on public.partner_applications for insert to authenticated
with check (
 applicant_id=(select auth.uid()) and status='pending' and reviewed_by is null
 and not exists(select 1 from unnest(document_paths) p where p !~ ('^'||(select auth.uid())::text||'/'))
);
drop policy if exists "customer submits payment receipt" on public.payment_receipts;
create policy "customer submits payment receipt" on public.payment_receipts for insert to authenticated
with check (
 customer_id=(select auth.uid()) and status='pending' and reviewed_by is null
 and storage_path like (select auth.uid())::text||'/%'
 and exists(select 1 from public.orders o where o.id=order_id and o.customer_id=(select auth.uid()))
);

create or replace function private.saree_submit_driver_settlement(p_receipt_path text)
returns uuid language plpgsql security definer set search_path=public,private as $$
declare v_due numeric(12,2); v_id uuid;
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 if length(trim(coalesce(p_receipt_path,'')))<4 or p_receipt_path not like auth.uid()::text||'/%' then raise exception 'settlement receipt must belong to this driver'; end if;
 select amount_due into v_due from public.courier_settlement_accounts where courier_id=auth.uid() for update;
 if coalesce(v_due,0)<=0 then raise exception 'no outstanding settlement'; end if;
 insert into public.courier_settlements(courier_id,amount,receipt_path) values(auth.uid(),v_due,p_receipt_path) returning id into v_id;
 return v_id;
end $$;
grant execute on function private.saree_submit_driver_settlement(text) to authenticated;
