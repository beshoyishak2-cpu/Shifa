from pathlib import Path

# Role switching is intentionally disabled: authenticated roles must come from
# separate Supabase users and the profiles/RLS authorization layer.
print('Visual role impersonation disabled; use separate authenticated test accounts.')
