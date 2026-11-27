do $$
declare v_def text;
begin
  v_def:=pg_get_functiondef('public.create_shifa_order(uuid,uuid,jsonb,text)'::regprocedure);
  execute replace(v_def,'FUNCTION public.create_shifa_order','FUNCTION private.create_shifa_order');
  v_def:=pg_get_functiondef('public.claim_shifa_order(uuid)'::regprocedure);
  execute replace(v_def,'FUNCTION public.claim_shifa_order','FUNCTION private.claim_shifa_order');
  v_def:=pg_get_functiondef('public.transition_shifa_order(uuid,public.shifa_order_status)'::regprocedure);
  execute replace(v_def,'FUNCTION public.transition_shifa_order','FUNCTION private.transition_shifa_order');
  v_def:=pg_get_functiondef('public.create_shifa_errand(text,text,text,text,text)'::regprocedure);
  execute replace(v_def,'FUNCTION public.create_shifa_errand','FUNCTION private.create_shifa_errand');
  v_def:=pg_get_functiondef('public.claim_shifa_errand(uuid)'::regprocedure);
  execute replace(v_def,'FUNCTION public.claim_shifa_errand','FUNCTION private.claim_shifa_errand');
  v_def:=pg_get_functiondef('public.transition_shifa_errand(uuid,public.shifa_order_status)'::regprocedure);
  execute replace(v_def,'FUNCTION public.transition_shifa_errand','FUNCTION private.transition_shifa_errand');
end $$;

revoke all on function private.create_shifa_order(uuid,uuid,jsonb,text) from public,anon;
revoke all on function private.claim_shifa_order(uuid) from public,anon;
revoke all on function private.transition_shifa_order(uuid,public.shifa_order_status) from public,anon;
revoke all on function private.create_shifa_errand(text,text,text,text,text) from public,anon;
revoke all on function private.claim_shifa_errand(uuid) from public,anon;
revoke all on function private.transition_shifa_errand(uuid,public.shifa_order_status) from public,anon;
grant execute on function private.create_shifa_order(uuid,uuid,jsonb,text) to authenticated;
grant execute on function private.claim_shifa_order(uuid) to authenticated;
grant execute on function private.transition_shifa_order(uuid,public.shifa_order_status) to authenticated;
grant execute on function private.create_shifa_errand(text,text,text,text,text) to authenticated;
grant execute on function private.claim_shifa_errand(uuid) to authenticated;
grant execute on function private.transition_shifa_errand(uuid,public.shifa_order_status) to authenticated;

create or replace function public.create_shifa_order(p_merchant_id uuid,p_address_id uuid,p_items jsonb,p_customer_note text default null)
returns uuid language sql security invoker set search_path=public,private
as $$ select private.create_shifa_order(p_merchant_id,p_address_id,p_items,p_customer_note); $$;
create or replace function public.claim_shifa_order(p_order_id uuid)
returns void language sql security invoker set search_path=public,private
as $$ select private.claim_shifa_order(p_order_id); $$;
create or replace function public.transition_shifa_order(p_order_id uuid,p_next_status public.shifa_order_status)
returns void language sql security invoker set search_path=public,private
as $$ select private.transition_shifa_order(p_order_id,p_next_status); $$;
create or replace function public.create_shifa_errand(p_pickup_address text,p_dropoff_address text,p_item_description text,p_customer_phone text,p_customer_note text default null)
returns uuid language sql security invoker set search_path=public,private
as $$ select private.create_shifa_errand(p_pickup_address,p_dropoff_address,p_item_description,p_customer_phone,p_customer_note); $$;
create or replace function public.claim_shifa_errand(p_errand_id uuid)
returns void language sql security invoker set search_path=public,private
as $$ select private.claim_shifa_errand(p_errand_id); $$;
create or replace function public.transition_shifa_errand(p_errand_id uuid,p_next_status public.shifa_order_status)
returns void language sql security invoker set search_path=public,private
as $$ select private.transition_shifa_errand(p_errand_id,p_next_status); $$;

revoke execute on function public.create_shifa_order(uuid,uuid,jsonb,text) from public,anon;
revoke execute on function public.claim_shifa_order(uuid) from public,anon;
revoke execute on function public.transition_shifa_order(uuid,public.shifa_order_status) from public,anon;
revoke execute on function public.create_shifa_errand(text,text,text,text,text) from public,anon;
revoke execute on function public.claim_shifa_errand(uuid) from public,anon;
revoke execute on function public.transition_shifa_errand(uuid,public.shifa_order_status) from public,anon;
grant execute on function public.create_shifa_order(uuid,uuid,jsonb,text) to authenticated;
grant execute on function public.claim_shifa_order(uuid) to authenticated;
grant execute on function public.transition_shifa_order(uuid,public.shifa_order_status) to authenticated;
grant execute on function public.create_shifa_errand(text,text,text,text,text) to authenticated;
grant execute on function public.claim_shifa_errand(uuid) to authenticated;
grant execute on function public.transition_shifa_errand(uuid,public.shifa_order_status) to authenticated;
