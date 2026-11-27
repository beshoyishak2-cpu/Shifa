-- Resolve administrator privileges from either trusted app_metadata or the protected profile role.
-- profiles.role is guarded by shifa_protect_profile_role; users cannot promote themselves.
create or replace function public.shifa_is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select
    coalesce((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin', false)
    or exists (
      select 1 from public.profiles p
      where p.id = auth.uid() and p.role = 'admin'
    );
$$;
