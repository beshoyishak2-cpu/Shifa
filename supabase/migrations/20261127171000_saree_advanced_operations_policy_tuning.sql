-- Performance and policy cleanup for advanced Saree operations.
drop policy if exists delivery_zones_manage_admin_or_merchant on public.saree_delivery_zones;
create policy delivery_zones_insert_admin_or_merchant on public.saree_delivery_zones
 for insert to authenticated with check(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));
create policy delivery_zones_update_admin_or_merchant on public.saree_delivery_zones
 for update to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id))
 with check(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));
create policy delivery_zones_delete_admin_or_merchant on public.saree_delivery_zones
 for delete to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));

drop policy if exists alternatives_manage_admin_or_merchant on public.saree_product_alternatives;
create policy alternatives_insert_admin_or_merchant on public.saree_product_alternatives
 for insert to authenticated with check(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));
create policy alternatives_update_admin_or_merchant on public.saree_product_alternatives
 for update to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id))
 with check(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));
create policy alternatives_delete_admin_or_merchant on public.saree_product_alternatives
 for delete to authenticated using(private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id));

drop policy if exists inventory_insert_admin_or_merchant on public.product_inventory_batches;
create policy inventory_insert_admin_or_merchant on public.product_inventory_batches
 for insert to authenticated with check(
   (private.shifa_is_admin() or private.shifa_is_merchant_member(merchant_id))
   and created_by=(select auth.uid())
 );

drop policy if exists refunds_customer_or_admin_read on public.saree_refund_requests;
create policy refunds_customer_or_admin_read on public.saree_refund_requests
 for select to authenticated using(customer_id=(select auth.uid()) or private.shifa_is_admin());
drop policy if exists refunds_customer_create on public.saree_refund_requests;
create policy refunds_customer_create on public.saree_refund_requests
 for insert to authenticated with check(customer_id=(select auth.uid()) and status='pending' and reviewed_by is null);

create index if not exists product_inventory_batches_created_by_idx on public.product_inventory_batches(created_by);
create index if not exists saree_audit_events_actor_idx on public.saree_audit_events(actor_id);
create index if not exists saree_product_alternatives_alt_product_idx on public.saree_product_alternatives(alternative_product_id);
create index if not exists saree_product_alternatives_merchant_idx on public.saree_product_alternatives(merchant_id);
create index if not exists saree_product_alternatives_reviewed_by_idx on public.saree_product_alternatives(reviewed_by);
create index if not exists saree_refund_requests_customer_idx on public.saree_refund_requests(customer_id);
create index if not exists saree_refund_requests_order_idx on public.saree_refund_requests(order_id);
create index if not exists saree_refund_requests_reviewed_by_idx on public.saree_refund_requests(reviewed_by);
create index if not exists saree_role_feature_permissions_updated_by_idx on public.saree_role_feature_permissions(updated_by);
