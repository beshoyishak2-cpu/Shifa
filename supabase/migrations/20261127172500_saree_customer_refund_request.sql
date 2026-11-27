create or replace function public.saree_submit_refund_request(
 p_order_id uuid,p_amount numeric,p_reason text
) returns uuid language plpgsql security definer set search_path=''
as $$
declare v_order public.orders%rowtype; v_id uuid;
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 if p_amount is null or p_amount<=0 then raise exception 'invalid refund amount'; end if;
 if length(trim(coalesce(p_reason,'')))<3 or length(trim(p_reason))>1000 then raise exception 'refund reason is required'; end if;
 select * into v_order from public.orders where id=p_order_id and customer_id=auth.uid() for update;
 if not found or v_order.status<>'delivered' then raise exception 'only delivered orders can be submitted for refund'; end if;
 if p_amount>v_order.total then raise exception 'refund amount exceeds order total'; end if;
 if exists(select 1 from public.saree_refund_requests r where r.order_id=p_order_id and r.status in ('pending','approved','paid')) then
   raise exception 'an active refund request already exists for this order';
 end if;
 insert into public.saree_refund_requests(order_id,customer_id,amount,reason)
 values(p_order_id,auth.uid(),p_amount,trim(p_reason)) returning id into v_id;
 return v_id;
end $$;
revoke all on function public.saree_submit_refund_request(uuid,numeric,text) from public,anon;
grant execute on function public.saree_submit_refund_request(uuid,numeric,text) to authenticated;
