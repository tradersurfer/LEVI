export const AUTHENTICATED_STREAMING_UNAVAILABLE = "Live agent streaming requires authenticated WebSockets, which aren't supported yet. Disable authentication for local paper trading, or check back for browser-compatible auth support."
export const GENERIC_STREAMING_FAILURE = 'The live WebSocket connection failed.'

export function streamingConnectionError(authEnabled) {
  return authEnabled ? AUTHENTICATED_STREAMING_UNAVAILABLE : GENERIC_STREAMING_FAILURE
}
