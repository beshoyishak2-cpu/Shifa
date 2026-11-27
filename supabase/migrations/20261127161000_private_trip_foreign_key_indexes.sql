create index if not exists private_trip_settings_updated_by_idx on public.private_trip_settings(updated_by);
create index if not exists private_trips_cancelled_by_idx on public.private_trips(cancelled_by);
