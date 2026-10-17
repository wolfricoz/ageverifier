# Database connection pooling

How ageverifier moved its production SQLAlchemy engine from `NullPool` to a `QueuePool`, and how to do the same in banwatch.

Reference: ageverifier branch `claude/queuepool-production`, commits `587872a`, `b7a6164`, `b723142`.

## Why

`NullPool` opens a new Postgres connection for every session and closes it afterwards. That costs about 38 ms per session on the test database. Most DB calls run synchronously on the asyncio event loop, so every one of those connects blocked the whole bot: gateway heartbeats, commands and API requests. In ageverifier, pooling cut the test suite from 6.5 minutes to about 20 seconds; the same cost was paid on every call in production.

`NullPool` was originally picked to avoid stale connections: ones the server or a firewall closed while they sat idle. The settings below cover that without paying for a new connection every time.

## The engine

`databases/current.py` in ageverifier (in banwatch this is `database/current.py`):

```python
# Opening a connection per session cost ~38ms, and most DB calls run on the event loop, so that time blocked the bot.
# pool_timeout is short so an exhausted pool fails fast instead of freezing the loop; pre_ping and recycle replace
# connections the server or a firewall closed while they sat idle.
pool_options = {"pool_size" : 32, "max_overflow" : 8, "pool_timeout" : 5, "pool_pre_ping" : True, "pool_recycle" : 1800}
engine = create_engine(db_string, echo=False, isolation_level="READ COMMITTED", **pool_options)


def _reset_pool_after_fork() :
	"""A forked worker (gunicorn --preload) must not reuse the parent's pooled sockets; close=False leaves them to the parent."""
	engine.dispose(close=False)


if hasattr(os, "register_at_fork") :  # POSIX only; Windows has no fork
	os.register_at_fork(after_in_child=_reset_pool_after_fork)
```

Remove the `from sqlalchemy.pool import NullPool` import if nothing else uses it.

| Option | Value | What it does |
|---|---|---|
| `pool_size` | `32` | Connections kept open for reuse. They are opened on demand, not at startup. |
| `max_overflow` | `8` | Extra connections allowed during a spike; closed again when returned. At most 40 per process. |
| `pool_timeout` | `5` | Seconds to wait for a free connection before raising. Keep it short: a long wait on the event loop freezes the bot. |
| `pool_pre_ping` | `True` | Runs a cheap check when a connection is checked out and replaces it if it is dead. This is what makes pooling safe against stale connections. |
| `pool_recycle` | `1800` | Replaces any connection older than 30 minutes, ahead of server or firewall idle timeouts. Also covers MySQL's `wait_timeout` in tests. |

**Fork safety.** Under gunicorn with `--preload` / `preload_app`, the app (and the engine) is imported in the master process before the workers fork. Workers would then share the master's sockets, which corrupts connections. The `register_at_fork` hook gives each child a fresh pool and leaves the parent's sockets alone (`close=False`). It is harmless without preload, so it doesn't matter how the bot is started. `os.register_at_fork` doesn't exist on Windows, hence the `hasattr` guard.

**Anything else that recreates the engine** (ageverifier's `Database.restart()`) must pass the same `**pool_options`, or it silently goes back to the default pool settings.

**Alembic stays on `NullPool`.** `alembic/env.py` runs once and exits, so pooling gains nothing there.

## Check for sessions that hold connections

With a pool, a session that is never closed keeps its connection checked out until garbage collection, and enough of those exhaust the pool. Look for:

- `createsession()` / `sessionmanager()` / `Session()` used outside a `with` block. Fine only if every path closes it; ageverifier's `commit()` closes the session in `finally`.
- **A second session opened inside a first one.** Ageverifier's `ServerTransactions.add` did `session = self.createsession()` inside `with self.createsession() as session:`. Nothing leaked, since both were closed, but each new guild held two connections, and the outer one sat idle in a transaction. The fix was to reuse the outer session.
- Sessions stored on singletons or other long-lived objects. A `sessionmaker` on a singleton is fine; a session on one is not.

Search with:

```bash
grep -rn "createsession()\|sessionmanager()\|Session()" --include=*.py . | grep -v "with "
```

## Tests

Postgres refuses to drop a database that still has open connections, and a pool keeps them open. Dispose the pool before the test runner drops the test database:

```python
finally :
	# Tests use a connection pool; Postgres refuses to drop a database that still has open connections.
	engine.dispose()
	drop_database(engine.url)
```

Banwatch tests run on MySQL. It doesn't refuse the drop the same way, but `engine.dispose()` there is still correct and harmless.

## Postgres server settings (64 GB server)

Both bots' pools count against `max_connections`. If they share one Postgres server, ageverifier (40) plus banwatch (40) is already 80 of the default 100. Raise it before deploying:

| Setting | Value | Needs |
|---|---|---|
| `max_connections` | `200` | restart |
| `shared_buffers` | `16GB` (25% of RAM; any amount above the database size is wasted) | restart |
| `huge_pages` | `try` (Linux, set `vm.nr_hugepages`) | restart |
| `effective_cache_size` | `40GB` (`48GB` if Postgres has the server to itself) | reload |
| `work_mem` | `32MB` | reload |
| `maintenance_work_mem` | `1GB` | reload |
| `random_page_cost` | `1.1` (SSD/NVMe only) | reload |
| `effective_io_concurrency` | `200` (SSD/NVMe only) | reload |
| `checkpoint_completion_target` | `0.9` | reload |
| `max_wal_size` | `4GB` | reload |
| `idle_in_transaction_session_timeout` | `5min` | reload |

Reload with `SELECT pg_reload_conf();`. Check the current limit with `SHOW max_connections;` and the database size with `SELECT pg_size_pretty(pg_database_size('<db name>'));`.

Pool size is about memory and headroom, not speed. Postgres runs well with about 2-4 active queries per CPU core; more connections than that just queue inside Postgres instead of in the pool. A Discord bot rarely runs more than about 35 queries at once: one event loop plus the default `asyncio.to_thread` pool of `min(32, cores + 4)` threads.

## Rollout

1. Test on the test guild first: a normal verification flow and a config reload.
2. Raise `max_connections` if both bots share the Postgres server, then restart the bot.
3. For a day, watch Sentry for:
   - `QueuePool limit of size ... overflow ... reached, connection timed out`: the pool is exhausted, likely a session that isn't being closed.
   - `server closed the connection unexpectedly` / `OperationalError`: disconnects that pre-ping and recycle should be catching.
   - `too many clients already`: Postgres `max_connections` reached.
4. To roll back, revert the engine change and restart; nothing else depends on it.
