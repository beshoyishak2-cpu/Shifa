-- Keep the merchant status RPC callable by signed-in clients without exposing a
-- SECURITY DEFINER function in the public API schema.
create or replace function private.set_merchant_open_status(
  p_merchant_id uuid,
  p_is_open boolean
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $function$
begin
  if auth.uid() is null then
    raise exception 'Authentication required' using errcode = '42501';
  end if;

  if not private.shifa_is_admin()
     and not private.shifa_is_merchant_member(p_merchant_id) then
    raise exception 'Not authorized to manage this merchant' using errcode = '42501';
  end if;

  update public.merchants
  set is_open = p_is_open
  where id = p_merchant_id;

  if not found then
    raise exception 'Merchant not found' using errcode = 'P0002';
  end if;

  return p_is_open;
end;
$function$;

revoke all on function private.set_merchant_open_status(uuid, boolean) from public, anon;
grant execute on function private.set_merchant_open_status(uuid, boolean) to authenticated;

create or replace function public.set_merchant_open_status(
  p_merchant_id uuid,
  p_is_open boolean
)
returns boolean
language sql
security invoker
set search_path = public, private
as $function$
  select private.set_merchant_open_status(p_merchant_id, p_is_open);
$function$;

revoke all on function public.set_merchant_open_status(uuid, boolean) from public, anon;
grant execute on function public.set_merchant_open_status(uuid, boolean) to authenticated;
