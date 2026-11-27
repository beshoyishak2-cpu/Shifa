import { createClient } from "npm:@supabase/supabase-js@2";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { ...cors, "Content-Type": "application/json" },
});
const round2 = (n: number) => Math.round((n + Number.EPSILON) * 100) / 100;

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405);

  const url = Deno.env.get("SUPABASE_URL")!;
  const anon = Deno.env.get("SUPABASE_ANON_KEY")!;
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const authHeader = req.headers.get("Authorization");
  if (!authHeader) return json({ error: "authentication_required" }, 401);

  const userClient = createClient(url, anon, { global: { headers: { Authorization: authHeader } } });
  const admin = createClient(url, serviceKey, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: userData, error: authError } = await userClient.auth.getUser();
  const user = userData.user;
  if (authError || !user) return json({ error: "invalid_session" }, 401);

  try {
    const body = await req.json();
    const action = String(body.action || "");
    if (action === "create") {
      const points = [body.pickup, body.destination];
      for (const p of points) {
        if (!p || !Number.isFinite(p.lat) || !Number.isFinite(p.lng) ||
            p.lat < -90 || p.lat > 90 || p.lng < -180 || p.lng > 180 ||
            typeof p.address !== "string" || !p.address.trim()) {
          return json({ error: "invalid_trip_points" }, 400);
        }
      }
      const routeUrl = `https://router.project-osrm.org/route/v1/driving/${points[0].lng},${points[0].lat};${points[1].lng},${points[1].lat}?overview=full&geometries=geojson&steps=false`;
      const routeResponse = await fetch(routeUrl, { headers: { "User-Agent": "Saree3/1.0 private-trip" } });
      if (!routeResponse.ok) return json({ error: "route_provider_unavailable" }, 503);
      const routeData = await routeResponse.json();
      const route = routeData.routes?.[0];
      if (routeData.code !== "Ok" || !route || !Number.isFinite(route.distance) || route.distance <= 0) {
        return json({ error: "no_driving_route_found" }, 422);
      }
      const { data: settings, error: settingsError } = await admin.from("private_trip_settings")
        .select("price_per_km,minimum_fare,meter_start_fee,commission_percent").eq("id", true).single();
      if (settingsError || !settings) return json({ error: "trip_pricing_not_configured" }, 503);
      if (Number(settings.price_per_km) <= 0) return json({ error: "trip_pricing_not_configured" }, 409);
      const km = route.distance / 1000;
      const fare = round2(Math.max(Number(settings.minimum_fare), km * Number(settings.price_per_km) + Number(settings.meter_start_fee)));
      const commission = round2(fare * Number(settings.commission_percent) / 100);
      const { data: trip, error } = await admin.from("private_trips").insert({
        customer_id: user.id,
        pickup_latitude: points[0].lat, pickup_longitude: points[0].lng, pickup_address: points[0].address.trim(),
        destination_latitude: points[1].lat, destination_longitude: points[1].lng, destination_address: points[1].address.trim(),
        route_distance_km: round2(km), estimated_duration_minutes: Math.ceil(route.duration / 60),
        route_geometry: route.geometry,
        price_per_km_snapshot: settings.price_per_km, minimum_fare_snapshot: settings.minimum_fare,
        meter_start_fee_snapshot: settings.meter_start_fee, commission_percent_snapshot: settings.commission_percent,
        fare_amount: fare, app_commission_amount: commission, courier_earnings: round2(fare - commission),
        customer_note: String(body.customer_note || "").slice(0, 500), payment_method: "cash", status: "searching",
      }).select("*").single();
      if (error) return json({ error: "trip_create_failed", detail: error.message }, 400);
      return json({ trip });
    }

    const tripId = String(body.trip_id || "");
    if (!tripId) return json({ error: "trip_id_required" }, 400);
    const { data: trip, error: tripError } = await admin.from("private_trips").select("*").eq("id", tripId).maybeSingle();
    if (tripError || !trip) return json({ error: "trip_not_found" }, 404);

    if (action === "accept") {
      const { data: courier } = await admin.from("courier_profiles").select("is_verified,is_available,locked_for_settlement").eq("user_id", user.id).maybeSingle();
      if (!courier?.is_verified || !courier.is_available || courier.locked_for_settlement) return json({ error: "verified_available_courier_required" }, 403);
      const { data: updated, error } = await admin.from("private_trips").update({
        courier_id: user.id, status: "accepted", accepted_at: new Date().toISOString(), updated_at: new Date().toISOString(),
      }).eq("id", tripId).eq("status", "searching").is("courier_id", null).select("*").maybeSingle();
      if (error || !updated) return json({ error: "trip_no_longer_available" }, 409);
      return json({ trip: updated });
    }

    if (action === "start" || action === "complete") {
      if (trip.courier_id !== user.id) return json({ error: "assigned_courier_only" }, 403);
      const from = action === "start" ? "accepted" : "in_progress";
      const to = action === "start" ? "in_progress" : "delivered";
      const stamp = action === "start" ? { started_at: new Date().toISOString() } : { delivered_at: new Date().toISOString() };
      const { data: updated, error } = await admin.from("private_trips").update({ status: to, ...stamp, updated_at: new Date().toISOString() })
        .eq("id", tripId).eq("status", from).select("*").maybeSingle();
      if (error || !updated) return json({ error: "invalid_trip_transition" }, 409);
      return json({ trip: updated });
    }

    if (action === "cancel") {
      const isCustomer = trip.customer_id === user.id;
      const isCourier = trip.courier_id === user.id;
      const { data: profile } = await admin.from("profiles").select("role").eq("id", user.id).maybeSingle();
      if (!isCustomer && !isCourier && profile?.role !== "admin") return json({ error: "not_trip_participant" }, 403);
      if (["delivered", "cancelled"].includes(trip.status)) return json({ error: "trip_already_closed" }, 409);
      if (trip.status === "in_progress" && !isCourier && profile?.role !== "admin") return json({ error: "cannot_cancel_started_trip" }, 409);
      const { data: updated, error } = await admin.from("private_trips").update({
        status: "cancelled", cancelled_by: user.id, cancellation_reason: String(body.reason || "").slice(0, 300),
        cancelled_at: new Date().toISOString(), updated_at: new Date().toISOString(),
      }).eq("id", tripId).not("status", "in", '("delivered","cancelled")').select("*").maybeSingle();
      if (error || !updated) return json({ error: "trip_already_closed" }, 409);
      return json({ trip: updated });
    }

    if (action === "location") {
      if (trip.courier_id !== user.id || !["accepted", "in_progress"].includes(trip.status)) return json({ error: "active_assigned_trip_required" }, 403);
      const { lat, lng, heading, speed, accuracy } = body;
      if (![lat, lng].every(Number.isFinite) || lat < -90 || lat > 90 || lng < -180 || lng > 180) return json({ error: "invalid_coordinates" }, 400);
      const { error } = await admin.from("courier_live_locations").upsert({
        courier_id: user.id, latitude: lat, longitude: lng,
        heading: Number.isFinite(heading) ? heading : null, speed_mps: Number.isFinite(speed) ? speed : null,
        accuracy_m: Number.isFinite(accuracy) ? accuracy : null, updated_at: new Date().toISOString(),
      });
      if (error) return json({ error: "location_update_failed" }, 400);
      return json({ ok: true });
    }
    return json({ error: "unknown_action" }, 400);
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : "unexpected_error" }, 500);
  }
});