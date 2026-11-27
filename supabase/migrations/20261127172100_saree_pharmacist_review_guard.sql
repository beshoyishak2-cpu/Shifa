create or replace function public.saree_pharmacist_review_alternative(
 p_alternative_id uuid,p_approve boolean,p_note text default null
) returns void language plpgsql security invoker set search_path=''
as $$
declare v_merchant uuid;
begin
 select merchant_id into v_merchant from public.saree_product_alternatives
 where id=p_alternative_id and admin_reviewed=true;
 if v_merchant is null then raise exception 'alternative not referred for pharmacist review'; end if;
 if not exists(select 1 from public.merchants m where m.id=v_merchant and m.service_type='pharmacy'
    and m.pharmacist_verified=true and private.shifa_is_merchant_member(m.id)) then
   raise exception 'verified pharmacist membership required';
 end if;
 update public.saree_product_alternatives
 set pharmacist_reviewed=true,is_active=p_approve,review_note=p_note,
     reviewed_by=auth.uid(),reviewed_at=now()
 where id=p_alternative_id;
end $$;
revoke all on function public.saree_pharmacist_review_alternative(uuid,boolean,text) from public,anon;
grant execute on function public.saree_pharmacist_review_alternative(uuid,boolean,text) to authenticated;
