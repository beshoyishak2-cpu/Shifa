-- Permit a customer to resubmit a rejected transfer proof for the same pending order.
create or replace function private.saree_submit_order_payment(p_order_id uuid,p_method text,p_receipt_path text)
returns uuid language plpgsql security definer set search_path=public,private as $$
declare v_order public.orders%rowtype; v_cfg public.saree_app_settings%rowtype; v_amount numeric(10,2); v_id uuid; v_existing public.payment_receipts%rowtype;
begin
 if auth.uid() is null then raise exception 'authentication required'; end if;
 select * into v_order from public.orders where id=p_order_id for update;
 if not found or v_order.customer_id<>auth.uid() or v_order.status<>'pending' then raise exception 'order unavailable'; end if;
 if p_method not in ('mobile_wallet','instapay') then raise exception 'unsupported external payment method'; end if;
 select * into v_cfg from public.saree_app_settings where id=true;
 if p_method='mobile_wallet' and not v_cfg.mobile_wallet_enabled then raise exception 'mobile wallet payment disabled'; end if;
 if p_method='instapay' and not v_cfg.instapay_enabled then raise exception 'InstaPay payment disabled'; end if;
 if length(trim(coalesce(p_receipt_path,'')))<4 then raise exception 'payment receipt required'; end if;
 v_amount:=greatest(0,v_order.total-v_order.wallet_amount);
 if v_amount<=0 then raise exception 'order already paid by wallet'; end if;
 select * into v_existing from public.payment_receipts where order_id=p_order_id for update;
 if found and v_existing.status<>'rejected' then raise exception 'payment receipt already submitted'; end if;
 update public.orders set payment_method=p_method::public.shifa_payment_method,external_payment_amount=v_amount,payment_status='awaiting_review',updated_at=now() where id=p_order_id;
 if v_existing.id is not null then
   update public.payment_receipts set customer_id=auth.uid(),payment_method=p_method,amount=v_amount,storage_path=p_receipt_path,status='pending',review_note=null,reviewed_by=null,reviewed_at=null,created_at=now() where id=v_existing.id returning id into v_id;
 else
   insert into public.payment_receipts(order_id,customer_id,payment_method,amount,storage_path)
   values(p_order_id,auth.uid(),p_method,v_amount,p_receipt_path) returning id into v_id;
 end if;
 return v_id;
end $$;
grant execute on function private.saree_submit_order_payment(uuid,text,text) to authenticated;

-- Keep the customer-facing RPC permissions explicit after replacement.
grant execute on function public.saree_submit_order_payment(uuid,text,text) to authenticated;
