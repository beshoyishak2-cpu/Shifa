-- Clinical safety boundary: admin moderation is not a substitute for pharmacist approval.
alter table public.saree_product_alternatives
 add column if not exists admin_reviewed boolean not null default false,
 add column if not exists admin_review_note text,
 add column if not exists admin_reviewed_by uuid references public.profiles(id),
 add column if not exists admin_reviewed_at timestamptz;

create or replace function public.saree_admin_review_alternative(
 p_alternative_id uuid,p_approve boolean,p_note text default null
) returns void language plpgsql security invoker set search_path=''
as $$
begin
 if not private.shifa_is_admin() then raise exception 'administrator required'; end if;
 update public.saree_product_alternatives
 set admin_reviewed=true,admin_review_note=p_note,admin_reviewed_by=auth.uid(),admin_reviewed_at=now(),
     pharmacist_reviewed=false,is_active=false,review_note=coalesce(p_note,'بانتظار مراجعة صيدلي معتمد')
 where id=p_alternative_id;
 if not found then raise exception 'alternative unavailable'; end if;
end $$;
revoke all on function public.saree_admin_review_alternative(uuid,boolean,text) from public,anon;
grant execute on function public.saree_admin_review_alternative(uuid,boolean,text) to authenticated;

create or replace function public.saree_pharmacist_review_alternative(
 p_alternative_id uuid,p_approve boolean,p_note text default null
) returns void language plpgsql security invoker set search_path=''
as $$
declare v_merchant uuid;
begin
 select merchant_id into v_merchant from public.saree_product_alternatives where id=p_alternative_id;
 if v_merchant is null then raise exception 'alternative unavailable'; end if;
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
