-- Enforce feature switches at database boundaries, not only in the admin screen.
create or replace function private.saree_feature_enabled(p_role text,p_feature text)
returns boolean language sql stable security definer set search_path=''
as $$
 select coalesce((
   select enabled from public.saree_role_feature_permissions
   where app_role=p_role and feature_key=p_feature
 ),true)
$$;
revoke all on function private.saree_feature_enabled(text,text) from public,anon;
grant execute on function private.saree_feature_enabled(text,text) to authenticated;

drop policy if exists "customer creates own order" on public.orders;
create policy "customer creates own order" on public.orders for insert to authenticated
 with check (
   customer_id=(select auth.uid()) and courier_id is null and status='pending'
   and private.saree_feature_enabled('customer','orders')
   and (
     (payment_method::text='cash' and private.saree_feature_enabled('customer','cash_payment'))
     or (payment_method::text in ('wallet','mobile_wallet') and private.saree_feature_enabled('customer','wallet_payment'))
     or (payment_method::text='instapay' and private.saree_feature_enabled('customer','instapay_payment'))
   )
 );

drop policy if exists "partner application own insert" on public.partner_applications;
create policy "partner application own insert" on public.partner_applications
 for insert to authenticated with check(
   applicant_id=(select auth.uid()) and status='pending' and reviewed_by is null
   and private.saree_feature_enabled('customer','partner_signup')
 );

drop policy if exists "customer submits payment receipt" on public.payment_receipts;
create policy "customer submits payment receipt" on public.payment_receipts
 for insert to authenticated with check(
   customer_id=(select auth.uid()) and status='pending' and reviewed_by is null
   and exists(select 1 from public.orders o where o.id=order_id and o.customer_id=(select auth.uid()))
   and (
     (payment_method='mobile_wallet' and private.saree_feature_enabled('customer','wallet_payment'))
     or (payment_method='instapay' and private.saree_feature_enabled('customer','instapay_payment'))
   )
 );

create or replace function private.saree_guard_feature_insert()
returns trigger language plpgsql security definer set search_path=''
as $$
declare v_role text;
begin
 if tg_table_name='product_reviews' then
   v_role:='customer';
   if not private.saree_feature_enabled(v_role,'customer_reviews') then
     raise exception 'feature_disabled:customer_reviews';
   end if;
 elsif tg_table_name='courier_live_locations' then
   v_role:='driver';
   if not private.saree_feature_enabled(v_role,'live_tracking') then
     raise exception 'feature_disabled:live_tracking';
   end if;
 end if;
 return new;
end $$;
revoke all on function private.saree_guard_feature_insert() from public,anon,authenticated;

drop trigger if exists saree_guard_reviews_feature on public.product_reviews;
create trigger saree_guard_reviews_feature before insert on public.product_reviews
 for each row execute function private.saree_guard_feature_insert();
drop trigger if exists saree_guard_live_tracking_feature on public.courier_live_locations;
create trigger saree_guard_live_tracking_feature before insert or update on public.courier_live_locations
 for each row execute function private.saree_guard_feature_insert();
