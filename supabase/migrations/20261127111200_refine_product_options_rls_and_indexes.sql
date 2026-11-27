drop policy "merchant manages product option groups" on public.product_option_groups;
drop policy "merchant manages product option values" on public.product_option_values;

create policy "public and owners read product option groups"
on public.product_option_groups for select to anon, authenticated
using (
  (is_active and exists (
    select 1 from public.products p join public.merchants m on m.id=p.merchant_id
    where p.id=product_option_groups.product_id and p.is_available and m.is_active
  ))
  or shifa_is_admin()
  or exists (select 1 from public.products p where p.id=product_option_groups.product_id and shifa_is_merchant_member(p.merchant_id))
);
create policy "merchant inserts product option groups"
on public.product_option_groups for insert to authenticated
with check (shifa_is_admin() or exists (select 1 from public.products p where p.id=product_option_groups.product_id and shifa_is_merchant_member(p.merchant_id)));
create policy "merchant updates product option groups"
on public.product_option_groups for update to authenticated
using (shifa_is_admin() or exists (select 1 from public.products p where p.id=product_option_groups.product_id and shifa_is_merchant_member(p.merchant_id)))
with check (shifa_is_admin() or exists (select 1 from public.products p where p.id=product_option_groups.product_id and shifa_is_merchant_member(p.merchant_id)));
create policy "merchant deletes product option groups"
on public.product_option_groups for delete to authenticated
using (shifa_is_admin() or exists (select 1 from public.products p where p.id=product_option_groups.product_id and shifa_is_merchant_member(p.merchant_id)));

create policy "public and owners read product option values"
on public.product_option_values for select to anon, authenticated
using (
  (is_available and exists (
    select 1 from public.product_option_groups g
    join public.products p on p.id=g.product_id
    join public.merchants m on m.id=p.merchant_id
    where g.id=product_option_values.group_id and g.is_active and p.is_available and m.is_active
  ))
  or shifa_is_admin()
  or exists (
    select 1 from public.product_option_groups g
    join public.products p on p.id=g.product_id
    where g.id=product_option_values.group_id and shifa_is_merchant_member(p.merchant_id)
  )
);
create policy "merchant inserts product option values"
on public.product_option_values for insert to authenticated
with check (shifa_is_admin() or exists (
  select 1 from public.product_option_groups g join public.products p on p.id=g.product_id
  where g.id=product_option_values.group_id and shifa_is_merchant_member(p.merchant_id)
));
create policy "merchant updates product option values"
on public.product_option_values for update to authenticated
using (shifa_is_admin() or exists (
  select 1 from public.product_option_groups g join public.products p on p.id=g.product_id
  where g.id=product_option_values.group_id and shifa_is_merchant_member(p.merchant_id)
))
with check (shifa_is_admin() or exists (
  select 1 from public.product_option_groups g join public.products p on p.id=g.product_id
  where g.id=product_option_values.group_id and shifa_is_merchant_member(p.merchant_id)
));
create policy "merchant deletes product option values"
on public.product_option_values for delete to authenticated
using (shifa_is_admin() or exists (
  select 1 from public.product_option_groups g join public.products p on p.id=g.product_id
  where g.id=product_option_values.group_id and shifa_is_merchant_member(p.merchant_id)
));

create index order_item_options_option_group_idx on public.order_item_options(option_group_id) where option_group_id is not null;
create index order_item_options_option_value_idx on public.order_item_options(option_value_id) where option_value_id is not null;
