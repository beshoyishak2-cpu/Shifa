-- Consolidate overlapping policies while preserving least-privilege behavior.
drop policy if exists "admin manages courier profiles" on public.courier_profiles;
create policy "admin inserts courier profiles" on public.courier_profiles for insert to authenticated with check (public.shifa_is_admin());
create policy "admin deletes courier profiles" on public.courier_profiles for delete to authenticated using (public.shifa_is_admin());

drop policy if exists "customers manage own addresses" on public.customer_addresses;
drop policy if exists "assigned courier reads delivery address" on public.customer_addresses;
create policy "customer addresses readable by participants" on public.customer_addresses for select to authenticated
using (customer_id=(select auth.uid()) or public.shifa_is_admin()
  or exists(select 1 from public.orders o where o.address_id=customer_addresses.id and o.courier_id=(select auth.uid())));
create policy "customers insert own addresses" on public.customer_addresses for insert to authenticated
with check (customer_id=(select auth.uid()) or public.shifa_is_admin());
create policy "customers update own addresses" on public.customer_addresses for update to authenticated
using (customer_id=(select auth.uid()) or public.shifa_is_admin())
with check (customer_id=(select auth.uid()) or public.shifa_is_admin());
create policy "customers delete own addresses" on public.customer_addresses for delete to authenticated
using (customer_id=(select auth.uid()) or public.shifa_is_admin());

drop policy if exists "admin manages medical providers" on public.medical_providers;
create policy "admin inserts medical providers" on public.medical_providers for insert to authenticated with check (public.shifa_is_admin());
create policy "admin updates medical providers" on public.medical_providers for update to authenticated using (public.shifa_is_admin()) with check (public.shifa_is_admin());
create policy "admin deletes medical providers" on public.medical_providers for delete to authenticated using (public.shifa_is_admin());

drop policy if exists "admin manages merchant memberships" on public.merchant_members;
create policy "admin inserts merchant memberships" on public.merchant_members for insert to authenticated with check (public.shifa_is_admin());
create policy "admin updates merchant memberships" on public.merchant_members for update to authenticated using (public.shifa_is_admin()) with check (public.shifa_is_admin());
create policy "admin deletes merchant memberships" on public.merchant_members for delete to authenticated using (public.shifa_is_admin());

drop policy if exists "admin manages merchants" on public.merchants;
create policy "admin inserts merchants" on public.merchants for insert to authenticated with check (public.shifa_is_admin());
create policy "admin updates merchants" on public.merchants for update to authenticated using (public.shifa_is_admin()) with check (public.shifa_is_admin());
create policy "admin deletes merchants" on public.merchants for delete to authenticated using (public.shifa_is_admin());

drop policy if exists "orders visible to participants" on public.orders;
drop policy if exists "verified couriers see ready unassigned orders" on public.orders;
create policy "orders visible to participants or verified couriers" on public.orders for select to authenticated
using (
  customer_id=(select auth.uid()) or courier_id=(select auth.uid()) or public.shifa_is_admin()
  or public.shifa_is_merchant_member(merchant_id)
  or (status='ready_for_pickup' and courier_id is null and exists(
    select 1 from public.courier_profiles cp where cp.user_id=(select auth.uid()) and cp.is_verified and cp.is_available
  ))
);

drop policy if exists "merchant manages products" on public.products;
create policy "merchant inserts products" on public.products for insert to authenticated
with check (public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id));
create policy "merchant updates products" on public.products for update to authenticated
using (public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id))
with check (public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id));
create policy "merchant deletes products" on public.products for delete to authenticated
using (public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id));

do $$
declare r record; q text; w text; stmt text;
begin
  for r in select schemaname,tablename,policyname,qual,with_check from pg_policies
    where schemaname='public' and (coalesce(qual,'') like '%auth.uid()%' or coalesce(qual,'') like '%auth.jwt()%'
      or coalesce(with_check,'') like '%auth.uid()%' or coalesce(with_check,'') like '%auth.jwt()%')
  loop
    q:=replace(replace(r.qual,'auth.uid()','(select auth.uid())'),'auth.jwt()','(select auth.jwt())');
    w:=replace(replace(r.with_check,'auth.uid()','(select auth.uid())'),'auth.jwt()','(select auth.jwt())');
    stmt:=format('alter policy %I on %I.%I',r.policyname,r.schemaname,r.tablename);
    if q is not null then stmt:=stmt||format(' using (%s)',q); end if;
    if w is not null then stmt:=stmt||format(' with check (%s)',w); end if;
    execute stmt;
  end loop;
end $$;
