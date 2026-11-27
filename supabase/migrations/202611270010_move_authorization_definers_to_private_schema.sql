create schema if not exists private;
revoke all on schema private from public,anon;
grant usage on schema private to authenticated;

create or replace function private.shifa_is_admin()
returns boolean language sql stable security definer set search_path=public
as $$
  select auth.uid() is not null and (
    coalesce((auth.jwt() -> 'app_metadata' ->> 'role')='admin',false)
    or exists(select 1 from public.profiles p where p.id=auth.uid() and p.role='admin')
  );
$$;
create or replace function private.shifa_is_merchant_member(p_merchant_id uuid)
returns boolean language sql stable security definer set search_path=public
as $$
  select auth.uid() is not null and exists(
    select 1 from public.merchant_members mm where mm.merchant_id=p_merchant_id and mm.user_id=auth.uid()
  );
$$;
revoke all on function private.shifa_is_admin() from public,anon;
revoke all on function private.shifa_is_merchant_member(uuid) from public,anon;
grant execute on function private.shifa_is_admin() to authenticated;
grant execute on function private.shifa_is_merchant_member(uuid) to authenticated;

create or replace function public.shifa_is_admin()
returns boolean language sql stable security invoker set search_path=public,private
as $$ select private.shifa_is_admin(); $$;
create or replace function public.shifa_is_merchant_member(p_merchant_id uuid)
returns boolean language sql stable security invoker set search_path=public,private
as $$ select private.shifa_is_merchant_member(p_merchant_id); $$;
revoke execute on function public.shifa_is_admin() from public,anon;
revoke execute on function public.shifa_is_merchant_member(uuid) from public,anon;
grant execute on function public.shifa_is_admin() to authenticated;
grant execute on function public.shifa_is_merchant_member(uuid) to authenticated;
