-- Security and performance refinement: exposed RPCs are invoker wrappers around private definer functions.
create index if not exists customer_favorites_product_idx on public.customer_favorites(product_id);
create index if not exists product_reviews_merchant_idx on public.product_reviews(merchant_id);
create index if not exists product_reviews_reviewed_by_idx on public.product_reviews(reviewed_by);
create index if not exists support_tickets_status_created_idx on public.support_tickets(status,created_at desc);

drop policy if exists "public reads approved product reviews" on public.product_reviews;
drop policy if exists "customers read own product reviews" on public.product_reviews;
create policy "anonymous reads approved product reviews" on public.product_reviews for select to anon using(status='approved');
create policy "authenticated reads permitted product reviews" on public.product_reviews for select to authenticated
using(status='approved' or customer_id=(select auth.uid()) or (select private.shifa_is_admin()));

drop policy if exists "public reads active merchant hours" on public.merchant_business_hours;
drop policy if exists "merchant members manage own business hours" on public.merchant_business_hours;
create policy "anonymous reads active merchant hours" on public.merchant_business_hours for select to anon
using(exists(select 1 from public.merchants m where m.id=merchant_id and m.is_active));
create policy "authenticated reads merchant hours" on public.merchant_business_hours for select to authenticated
using(exists(select 1 from public.merchants m where m.id=merchant_id and m.is_active)
  or (select private.shifa_is_admin()) or (select private.shifa_is_merchant_member(merchant_id)));
create policy "merchant members insert own business hours" on public.merchant_business_hours for insert to authenticated
with check((select private.shifa_is_admin()) or (select private.shifa_is_merchant_member(merchant_id)));
create policy "merchant members update own business hours" on public.merchant_business_hours for update to authenticated
using((select private.shifa_is_admin()) or (select private.shifa_is_merchant_member(merchant_id)))
with check((select private.shifa_is_admin()) or (select private.shifa_is_merchant_member(merchant_id)));
create policy "merchant members delete own business hours" on public.merchant_business_hours for delete to authenticated
using((select private.shifa_is_admin()) or (select private.shifa_is_merchant_member(merchant_id)));

create or replace function private.submit_product_review(p_order_id uuid,p_product_id uuid,p_rating smallint,p_comment text default '')
returns uuid language plpgsql security definer set search_path=''
as $$
declare v_merchant_id uuid; v_review_id uuid;
begin
 if auth.uid() is null then raise exception 'authentication required' using errcode='28000'; end if;
 if p_rating is null or p_rating<1 or p_rating>5 then raise exception 'rating must be from 1 to 5' using errcode='22023'; end if;
 if length(coalesce(p_comment,''))>1200 then raise exception 'review is too long' using errcode='22023'; end if;
 select o.merchant_id into v_merchant_id from public.orders o where o.id=p_order_id and o.customer_id=auth.uid() and o.status='delivered'::public.shifa_order_status;
 if v_merchant_id is null then raise exception 'only the customer of a delivered order can review it' using errcode='42501'; end if;
 if not exists(select 1 from public.order_items oi join public.products p on p.id=oi.product_id where oi.order_id=p_order_id and oi.product_id=p_product_id and p.merchant_id=v_merchant_id) then
  raise exception 'product is not part of this order' using errcode='22023';
 end if;
 insert into public.product_reviews(customer_id,merchant_id,product_id,order_id,rating,comment)
 values(auth.uid(),v_merchant_id,p_product_id,p_order_id,p_rating,coalesce(trim(p_comment),'')) returning id into v_review_id;
 return v_review_id;
end; $$;
revoke all on function private.submit_product_review(uuid,uuid,smallint,text) from public,anon;
grant execute on function private.submit_product_review(uuid,uuid,smallint,text) to authenticated;
create or replace function public.submit_product_review(p_order_id uuid,p_product_id uuid,p_rating smallint,p_comment text default '')
returns uuid language sql security invoker set search_path=public,private
as $$ select private.submit_product_review(p_order_id,p_product_id,p_rating,p_comment); $$;
revoke all on function public.submit_product_review(uuid,uuid,smallint,text) from public,anon;
grant execute on function public.submit_product_review(uuid,uuid,smallint,text) to authenticated;

create or replace function private.admin_review_product_review(p_review_id uuid,p_approve boolean)
returns void language plpgsql security definer set search_path=''
as $$ begin
 if not coalesce(private.shifa_is_admin(),false) then raise exception 'admin access required' using errcode='42501'; end if;
 update public.product_reviews set status=case when p_approve then 'approved' else 'rejected' end,reviewed_by=auth.uid(),reviewed_at=now() where id=p_review_id;
 if not found then raise exception 'review not found' using errcode='P0002'; end if;
end; $$;
revoke all on function private.admin_review_product_review(uuid,boolean) from public,anon;
grant execute on function private.admin_review_product_review(uuid,boolean) to authenticated;
create or replace function public.admin_review_product_review(p_review_id uuid,p_approve boolean)
returns void language sql security invoker set search_path=public,private
as $$ select private.admin_review_product_review(p_review_id,p_approve); $$;
revoke all on function public.admin_review_product_review(uuid,boolean) from public,anon;
grant execute on function public.admin_review_product_review(uuid,boolean) to authenticated;

create or replace function private.set_courier_live_location(
 p_latitude double precision,p_longitude double precision,p_heading double precision default null,
 p_speed_mps double precision default null,p_accuracy_m double precision default null
) returns timestamptz language plpgsql security definer set search_path=''
as $$ declare v_updated_at timestamptz:=now(); begin
 if auth.uid() is null then raise exception 'authentication required' using errcode='28000'; end if;
 if p_latitude is null or p_latitude not between -90 and 90 or p_longitude is null or p_longitude not between -180 and 180 then raise exception 'invalid coordinates' using errcode='22023'; end if;
 if not exists(select 1 from public.courier_profiles cp where cp.user_id=auth.uid() and cp.is_verified and cp.is_available and not cp.locked_for_settlement) then raise exception 'verified available courier required' using errcode='42501'; end if;
 insert into public.courier_live_locations(courier_id,latitude,longitude,heading,speed_mps,accuracy_m,updated_at)
 values(auth.uid(),p_latitude,p_longitude,p_heading,p_speed_mps,p_accuracy_m,v_updated_at)
 on conflict(courier_id) do update set latitude=excluded.latitude,longitude=excluded.longitude,heading=excluded.heading,speed_mps=excluded.speed_mps,accuracy_m=excluded.accuracy_m,updated_at=excluded.updated_at;
 return v_updated_at;
end; $$;
revoke all on function private.set_courier_live_location(double precision,double precision,double precision,double precision,double precision) from public,anon;
grant execute on function private.set_courier_live_location(double precision,double precision,double precision,double precision,double precision) to authenticated;
create or replace function public.set_courier_live_location(
 p_latitude double precision,p_longitude double precision,p_heading double precision default null,
 p_speed_mps double precision default null,p_accuracy_m double precision default null
) returns timestamptz language sql security invoker set search_path=public,private
as $$ select private.set_courier_live_location(p_latitude,p_longitude,p_heading,p_speed_mps,p_accuracy_m); $$;
revoke all on function public.set_courier_live_location(double precision,double precision,double precision,double precision,double precision) from public,anon;
grant execute on function public.set_courier_live_location(double precision,double precision,double precision,double precision,double precision) to authenticated;

create or replace function private.admin_reply_support_ticket(p_ticket_id uuid,p_reply text,p_status public.shifa_ticket_status default 'in_progress')
returns void language plpgsql security definer set search_path=''
as $$ declare v_customer_id uuid; v_subject text; begin
 if not coalesce(private.shifa_is_admin(),false) then raise exception 'admin access required' using errcode='42501'; end if;
 if length(trim(coalesce(p_reply,'')))<2 or length(p_reply)>4000 then raise exception 'reply must contain 2 to 4000 characters' using errcode='22023'; end if;
 if p_status not in ('open','in_progress','resolved','closed') then raise exception 'invalid ticket status' using errcode='22023'; end if;
 update public.support_tickets set admin_reply=trim(p_reply),replied_at=now(),updated_at=now(),status=p_status where id=p_ticket_id returning customer_id,subject into v_customer_id,v_subject;
 if not found then raise exception 'ticket not found' using errcode='P0002'; end if;
 insert into public.user_notifications(user_id,title,body,kind,related_id) values(v_customer_id,'رد جديد من دعم سريع','تم الرد على شكواك: '||v_subject,'support_reply',p_ticket_id);
end; $$;
revoke all on function private.admin_reply_support_ticket(uuid,text,public.shifa_ticket_status) from public,anon;
grant execute on function private.admin_reply_support_ticket(uuid,text,public.shifa_ticket_status) to authenticated;
create or replace function public.admin_reply_support_ticket(p_ticket_id uuid,p_reply text,p_status public.shifa_ticket_status default 'in_progress')
returns void language sql security invoker set search_path=public,private
as $$ select private.admin_reply_support_ticket(p_ticket_id,p_reply,p_status); $$;
revoke all on function public.admin_reply_support_ticket(uuid,text,public.shifa_ticket_status) from public,anon;
grant execute on function public.admin_reply_support_ticket(uuid,text,public.shifa_ticket_status) to authenticated;
