drop policy if exists "prescriptions visible to owner pharmacist or admin" on public.pharmacy_prescriptions;
drop policy if exists "prescriptions visible to owner verified pharmacy or admin" on public.pharmacy_prescriptions;
create policy "prescriptions visible to owner verified pharmacy or admin"
on public.pharmacy_prescriptions for select to authenticated
using (
  customer_id=auth.uid()
  or public.shifa_is_admin()
  or exists(
    select 1 from public.merchants m
    where m.id=pharmacy_merchant_id and m.service_type='pharmacy'
      and m.pharmacist_verified=true
      and public.shifa_is_merchant_member(m.id)
  )
);

drop policy if exists "prescription owner pharmacist admin reads" on storage.objects;
drop policy if exists "prescription owner verified pharmacy admin reads" on storage.objects;
create policy "prescription owner verified pharmacy admin reads"
on storage.objects for select to authenticated
using (
  bucket_id='prescriptions'
  and (
    (storage.foldername(name))[1]=auth.uid()::text
    or public.shifa_is_admin()
    or exists(
      select 1 from public.pharmacy_prescriptions pp
      join public.merchants m on m.id=pp.pharmacy_merchant_id
      where pp.storage_path=storage.objects.name
        and m.service_type='pharmacy' and m.pharmacist_verified=true
        and public.shifa_is_merchant_member(m.id)
    )
  )
);

create or replace function public.shifa_guard_prescription_transition()
returns trigger language plpgsql security definer set search_path=public
as $$
begin
  if new.status is distinct from old.status and not public.shifa_is_admin() then
    if not (
      (old.status='submitted' and new.status in ('under_review','rejected'))
      or (old.status='under_review' and new.status in ('approved','rejected'))
      or (old.status='approved' and new.status='fulfilled')
    ) then raise exception 'Invalid prescription review transition'; end if;
    if new.reviewed_by is distinct from auth.uid() then raise exception 'reviewer must be the authenticated pharmacist'; end if;
    if not exists(select 1 from public.merchants m where m.id=new.pharmacy_merchant_id
      and m.service_type='pharmacy' and m.pharmacist_verified=true and public.shifa_is_merchant_member(m.id)) then
      raise exception 'verified pharmacy membership required';
    end if;
  end if;
  return new;
end;
$$;
drop trigger if exists shifa_guard_prescription_transition on public.pharmacy_prescriptions;
create trigger shifa_guard_prescription_transition before update on public.pharmacy_prescriptions
for each row execute function public.shifa_guard_prescription_transition();
revoke execute on function public.shifa_guard_prescription_transition() from public,anon,authenticated;

do $$
begin
  if not exists(select 1 from pg_publication_tables where pubname='supabase_realtime' and schemaname='public' and tablename='errand_requests') then
    alter publication supabase_realtime add table public.errand_requests;
  end if;
end $$;
