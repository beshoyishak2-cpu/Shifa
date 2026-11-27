drop policy if exists "active merchants public, admin all" on public.merchants;
create policy "anonymous reads active merchants" on public.merchants for select to anon using (is_active=true);
create policy "authenticated reads merchants" on public.merchants for select to authenticated
using (is_active or public.shifa_is_admin() or public.shifa_is_merchant_member(id));
drop policy if exists "categories visible" on public.categories;
create policy "anonymous reads active categories" on public.categories for select to anon using (is_active=true);
create policy "authenticated reads categories" on public.categories for select to authenticated using (is_active or public.shifa_is_admin());
drop policy if exists "products visible" on public.products;
create policy "anonymous reads available products" on public.products for select to anon
using (is_available and exists(select 1 from public.merchants m where m.id=merchant_id and m.is_active));
create policy "authenticated reads products" on public.products for select to authenticated
using ((is_available and exists(select 1 from public.merchants m where m.id=merchant_id and m.is_active))
  or public.shifa_is_admin() or public.shifa_is_merchant_member(merchant_id));

create policy "admin manages merchants" on public.merchants
for all to authenticated using (public.shifa_is_admin()) with check (public.shifa_is_admin());
create policy "admin manages merchant memberships" on public.merchant_members
for all to authenticated using (public.shifa_is_admin()) with check (public.shifa_is_admin());
create policy "admin manages courier profiles" on public.courier_profiles
for all to authenticated using (public.shifa_is_admin()) with check (public.shifa_is_admin());

create or replace function public.shifa_protect_courier_verification()
returns trigger language plpgsql security definer set search_path=public
as $$
begin
  if new.is_verified is distinct from old.is_verified and not public.shifa_is_admin() then
    raise exception 'courier verification requires administrator approval';
  end if;
  if new.user_id is distinct from old.user_id and not public.shifa_is_admin() then
    raise exception 'courier identity cannot be changed';
  end if;
  return new;
end;
$$;
drop trigger if exists shifa_protect_courier_verification on public.courier_profiles;
create trigger shifa_protect_courier_verification
before update on public.courier_profiles
for each row execute function public.shifa_protect_courier_verification();
revoke execute on function public.shifa_protect_courier_verification() from public,anon,authenticated;
