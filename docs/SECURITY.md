# LEVI Security Notes

## Dashboard Authentication

Dashboard endpoints (`/api/dashboard/*`) accept `user_id` as a query parameter.

- When `LEVI_AUTH_ENABLED=false` (default): dashboard access is unauthenticated and trusts the client-supplied `user_id`. This is appropriate for local, single-user paper trading on a machine you control. Do not expose this port on a shared network or the public internet in this mode.
- When `LEVI_AUTH_ENABLED=true`: dashboard routes require a valid bearer session matching the requested `user_id`. Requests without a valid session are rejected, and an authenticated user cannot request another user's dashboard.

Authentication enforcement is conditional so the existing local paper-trading default remains unchanged. Enabling authentication also requires a correctly configured authentication service.
