-- Keep the privileged write helper outside the exposed API schema.
create or replace function private.set_merchant_image_url(p_merchant_id uuid, p_image_url text)
returns text language plpgsql security definer set search_path = ''
as $$
declare saved_url text;
begin
 if auth.uid() is null or (not public.shifa_is_merchant_member(p_merchant_id) and not public.shifa_is_admin()) then
  raise exception 'not authorized to update this merchant image';
 end if;
 if p_image_url is not null and length(p_image_url)>2048 then raise exception 'image URL is too long'; end if;
 update public.merchants set image_url=p_image_url where id=p_merchant_id returning image_url into saved_url;
 if not found then raise exception 'merchant not found'; end if;
 return saved_url;
end;
$$;
revoke all on function private.set_merchant_image_url(uuid,text) from public;
revoke all on function private.set_merchant_image_url(uuid,text) from anon;
grant usage on schema private to authenticated;
grant execute on function private.set_merchant_image_url(uuid,text) to authenticated;

create or replace function public.set_merchant_image_url(p_merchant_id uuid, p_image_url text)
returns text language sql security invoker set search_path = ''
as $$ select private.set_merchant_image_url(p_merchant_id,p_image_url); $$;
revoke all on function public.set_merchant_image_url(uuid,text) from public;
revoke all on function public.set_merchant_image_url(uuid,text) from anon;
grant execute on function public.set_merchant_image_url(uuid,text) to authenticated;
