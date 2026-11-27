create or replace function public.shifa_protect_profile_role()
returns trigger language plpgsql security definer set search_path=public
as $$
begin
  if new.role is distinct from old.role
     and not public.shifa_is_admin()
     and current_setting('shifa.bootstrap_admin',true) is distinct from 'on' then
    raise exception 'role changes require administrator approval';
  end if;
  new.updated_at=now();
  return new;
end;
$$;

create or replace function public.shifa_bootstrap_first_admin(p_user_id uuid)
returns void language plpgsql security definer set search_path=public
as $$
begin
  if exists(select 1 from public.profiles where role='admin') then
    raise exception 'an administrator is already configured';
  end if;
  if not exists(select 1 from public.profiles where id=p_user_id) then
    raise exception 'profile not found; the user must sign up first';
  end if;
  perform set_config('shifa.bootstrap_admin','on',true);
  update public.profiles set role='admin' where id=p_user_id;
end;
$$;
revoke all on function public.shifa_bootstrap_first_admin(uuid) from public,anon,authenticated;
grant execute on function public.shifa_bootstrap_first_admin(uuid) to service_role;
