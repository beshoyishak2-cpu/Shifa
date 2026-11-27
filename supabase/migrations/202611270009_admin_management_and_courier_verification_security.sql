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
create trigger shifa_protect_courier_verification
before update on public.courier_profiles
for each row execute function public.shifa_protect_courier_verification();
revoke execute on function public.shifa_protect_courier_verification() from public,anon,authenticated;
