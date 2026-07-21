# LEVI Phase 2B — Broker Paper Adapter

Phase 2B adds a paper-only broker boundary. `BrokerAdapter` defines account, position, limit-order, fill, cancellation, and health operations. Immutable models live in `levi/brokers/`; routing and polling live in `levi/execution/`.

## Safety boundary

`TastytradeClient` accepts certificate/sandbox URLs only and rejects production URLs. Only `OrderType.LIMIT` and option call/put sides pass the execution gateway. There is no live-trading switch, market-order path, autonomous consensus connection, market-data feed, or credential persistence. Credentials and tokens remain in memory and come from deployment configuration.

## Components

- `TastytradeAuth`: session creation, expiry checks, and refresh.
- `TastytradeClient`: bounded HTTP operations for balances, positions, current/open orders, order history, fills, and cancellation.
- `OrderSubmitter` and `ExecutionGateway`: validation and process-local idempotency.
- `FillReconciler`: broker-fill weighted price and integrity checks.
- `PositionTracker`: realized, unrealized, and combined daily P&L.
- `ContinuousReconciler`: one-second configurable polling with once-only fill callbacks.
- `SimulatorBroker`: deterministic offline paper adapter.

## Configuration

Use `TASTYTRADE_API_URL=https://api.cert.tastyworks.com`, paper account ID, username, and password. Never configure a production endpoint. `TASTYTRADE_POLL_INTERVAL` defaults to 1 second. Idempotency is process-local; durable persistence is deferred.

## Testing

Run `pytest tests/test_broker_adapter_base.py tests/test_tastytrade_auth.py tests/test_tastytrade_client.py tests/test_tastytrade_orders.py tests/test_tastytrade_positions.py tests/test_fill_reconciliation.py tests/test_execution_gateway.py tests/test_execution_reconciler.py tests/test_broker_simulator.py -q`, then `pytest tests -q`.

## Exclusions

No live trading, market orders, automatic execution, market-data adapter, dashboard, authentication UI, model changes, or Phase 3 work is included.
