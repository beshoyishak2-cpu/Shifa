revoke all on table public.product_option_groups, public.product_option_values from anon, authenticated;
grant select on table public.product_option_groups, public.product_option_values to anon;
grant select, insert, update, delete on table public.product_option_groups, public.product_option_values to authenticated;

revoke all on table public.order_item_options from anon, authenticated;
grant select on table public.order_item_options to authenticated;
