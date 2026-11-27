CREATE OR REPLACE FUNCTION private.create_shifa_order(p_merchant_id uuid, p_address_id uuid, p_items jsonb, p_customer_note text DEFAULT NULL::text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_customer_id uuid := auth.uid();
  v_order_id uuid;
  v_subtotal numeric(10,2) := 0;
  v_delivery_fee numeric(10,2);
  v_rows integer;
  v_unique_rows integer;
  v_address public.customer_addresses%rowtype;
  v_item jsonb;
  v_group jsonb;
  v_group_row record;
  v_value_row record;
  v_selected_count integer;
  v_valid_count integer;
  v_extra_total numeric(10,2);
  v_item_id uuid;
  v_options jsonb;
  v_value_ids jsonb;
begin
  if v_customer_id is null then raise exception 'Authentication required'; end if;
  if p_items is null or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
    raise exception 'Order must contain at least one item';
  end if;

  select * into v_address from public.customer_addresses a
  where a.id = p_address_id and a.customer_id = v_customer_id;
  if not found then raise exception 'Address not found'; end if;

  select m.delivery_fee into v_delivery_fee from public.merchants m
  where m.id = p_merchant_id and m.is_active = true;
  if not found then raise exception 'Merchant is unavailable'; end if;

  select count(*), count(distinct x.product_id)
  into v_rows, v_unique_rows
  from jsonb_to_recordset(p_items) as x(product_id uuid, quantity integer);
  if v_rows <> jsonb_array_length(p_items) or v_unique_rows <> v_rows then
    raise exception 'Order contains duplicate or invalid products';
  end if;

  for v_item in select value from jsonb_array_elements(p_items)
  loop
    if jsonb_typeof(v_item->'options') is not null and jsonb_typeof(v_item->'options') <> 'array' then
      raise exception 'Invalid product options payload';
    end if;
    v_options := coalesce(v_item->'options', '[]'::jsonb);

    if exists (
      select 1 from jsonb_array_elements(v_options) e
      group by e->>'group_id' having count(*) > 1
    ) then raise exception 'An option group was submitted more than once'; end if;

    if exists (
      select 1 from jsonb_array_elements(v_options) e
      where coalesce(e->>'group_id','') !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        or jsonb_typeof(e->'value_ids') is distinct from 'array'
        or not exists (
          select 1 from public.product_option_groups g
          where g.id = (e->>'group_id')::uuid
            and g.product_id = (v_item->>'product_id')::uuid
            and g.is_active
        )
    ) then raise exception 'One or more selected option groups are invalid'; end if;

    for v_group_row in
      select g.* from public.product_option_groups g
      where g.product_id = (v_item->>'product_id')::uuid and g.is_active
    loop
      v_group := null;
      select e into v_group from jsonb_array_elements(v_options) e
      where e->>'group_id' = v_group_row.id::text limit 1;

      if v_group is null then
        v_selected_count := 0;
        v_value_ids := '[]'::jsonb;
      else
        v_value_ids := v_group->'value_ids';
        if jsonb_typeof(v_value_ids) is distinct from 'array' then
          raise exception 'Invalid selected values for option group %', v_group_row.name;
        end if;
        v_selected_count := jsonb_array_length(v_value_ids);
      end if;

      if v_selected_count < v_group_row.min_select or v_selected_count > v_group_row.max_select then
        raise exception 'Please select the required options for %', v_group_row.name;
      end if;

      select count(*), count(distinct x.value_id)
      into v_valid_count, v_selected_count
      from jsonb_array_elements_text(v_value_ids) as x(value_id)
      join public.product_option_values ov
        on ov.id = x.value_id::uuid and ov.group_id = v_group_row.id and ov.is_available;

      if v_valid_count <> jsonb_array_length(v_value_ids) or v_selected_count <> v_valid_count then
        raise exception 'One or more selected options are unavailable';
      end if;
    end loop;

    select p.price + coalesce(sum(ov.price_delta),0)
    into v_extra_total
    from public.products p
    left join lateral (
      select x.value_id::uuid as option_value_id
      from jsonb_array_elements(v_options) e
      cross join lateral jsonb_array_elements_text(e->'value_ids') as x(value_id)
    ) selected on true
    left join public.product_option_values ov
      on ov.id = selected.option_value_id and ov.is_available
    where p.id = (v_item->>'product_id')::uuid
      and p.merchant_id = p_merchant_id and p.is_available
    group by p.price;

    if v_extra_total is null then raise exception 'One or more products are unavailable or invalid'; end if;
    if coalesce((v_item->>'quantity')::integer,0) not between 1 and 99 then
      raise exception 'Invalid product quantity';
    end if;
    v_subtotal := v_subtotal + v_extra_total * (v_item->>'quantity')::integer;
  end loop;

  insert into public.orders (
    customer_id, merchant_id, address_id, status, payment_method,
    subtotal, delivery_fee, total, customer_note,
    delivery_area, delivery_street, delivery_landmark, delivery_unit_details,
    delivery_latitude, delivery_longitude, delivery_map_url
  ) values (
    v_customer_id, p_merchant_id, p_address_id, 'pending', 'cash',
    v_subtotal, v_delivery_fee, v_subtotal + v_delivery_fee, p_customer_note,
    v_address.area, v_address.street, v_address.landmark, v_address.unit_details,
    v_address.latitude, v_address.longitude,
    case when v_address.latitude is not null and v_address.longitude is not null
      then 'https://www.google.com/maps?q=' || v_address.latitude::text || ',' || v_address.longitude::text
      else null end
  ) returning id into v_order_id;

  for v_item in select value from jsonb_array_elements(p_items)
  loop
    v_options := coalesce(v_item->'options', '[]'::jsonb);
    select p.price + coalesce(sum(ov.price_delta),0)
    into v_extra_total
    from public.products p
    left join lateral (
      select x.value_id::uuid as option_value_id
      from jsonb_array_elements(v_options) e
      cross join lateral jsonb_array_elements_text(e->'value_ids') as x(value_id)
    ) selected on true
    left join public.product_option_values ov
      on ov.id = selected.option_value_id and ov.is_available
    where p.id = (v_item->>'product_id')::uuid
      and p.merchant_id = p_merchant_id and p.is_available
    group by p.price;

    insert into public.order_items (order_id, product_id, product_name, unit_price, quantity)
    select v_order_id, p.id, p.name, v_extra_total, (v_item->>'quantity')::integer
    from public.products p
    where p.id = (v_item->>'product_id')::uuid
    returning id into v_item_id;

    for v_group in select value from jsonb_array_elements(v_options)
    loop
      select g.* into v_group_row
      from public.product_option_groups g
      where g.id = (v_group->>'group_id')::uuid
        and g.product_id = (v_item->>'product_id')::uuid;

      for v_value_row in
        select ov.* from jsonb_array_elements_text(v_group->'value_ids') as x(value_id)
        join public.product_option_values ov on ov.id = x.value_id::uuid
        where ov.group_id = v_group_row.id and ov.is_available
      loop
        insert into public.order_item_options (
          order_item_id, option_group_id, option_value_id,
          group_name_snapshot, option_name_snapshot, price_delta, quantity
        ) values (
          v_item_id, v_group_row.id, v_value_row.id,
          v_group_row.name, v_value_row.name, v_value_row.price_delta, 1
        );
      end loop;
    end loop;
  end loop;

  insert into public.order_status_events(order_id, changed_by, new_status, note)
  values (v_order_id, v_customer_id, 'pending', 'Order submitted');
  return v_order_id;
end;
$function$

