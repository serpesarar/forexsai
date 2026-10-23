"""Reconnect/cancellation regressions; no Redis, market data, or DB writes."""
import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError
from services import mt5_redis_client as feed


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    monkeypatch.setattr(feed, '_listener_running', False)
    monkeypatch.setattr(feed, '_listener_task', None)
    monkeypatch.setattr(feed, '_listener_client', None)
    monkeypatch.setattr(feed, '_listener_pubsub', None)
    monkeypatch.setattr(feed, '_diag', dict(feed._diag, ticks_received=0, ticks_ingested=0,
        bars_received=0, reconnect_count=0, last_tick_time=None, last_bar_time=None,
        connected=False, stream_reader_active=False))
    monkeypatch.setattr(feed, 'get_redis_url', lambda: 'redis://user:never-disclose@invalid:6379')
    monkeypatch.setattr(feed, '_source_mode_enabled', lambda: True)


def test_old_reader_and_pool_are_closed_before_reconnect(monkeypatch):
    async def run():
        clients = []
        got_tick = asyncio.Event()
        original_sleep = asyncio.sleep

        class Client:
            def __init__(self):
                self.index = len(clients)
                self.started = asyncio.Event()
                self.stopped = False
                self.closed = False
                self.sent = False
                clients.append(self)
            async def ping(self): return True
            def pubsub(self): return self
            async def subscribe(self, channel): pass
            async def xread(self, *args, **kwargs):
                self.started.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    # Make joining observable: cleanup itself has an await.
                    await original_sleep(0.005)
                    self.stopped = True
            async def get_message(self, **kwargs):
                await self.started.wait()
                if self.index == 0:
                    raise ConnectionError('disconnect')
                if not self.sent:
                    self.sent = True
                    return {'channel': feed.settings.mt5_redis_tick_channel,
                            'data': json.dumps({'symbol': 'NDX.INDX', 'price': 100})}
                await asyncio.Event().wait()
            async def aclose(self, **kwargs): self.closed = True

        def factory(*args, **kwargs):
            assert kwargs['max_connections'] == 4
            if clients:
                assert clients[-1].stopped and clients[-1].closed
            return Client()

        async def ingest(payload): got_tick.set()
        async def quick_sleep(delay): await original_sleep(min(delay, 0.01))
        monkeypatch.setattr(feed.redis, 'from_url', factory)
        monkeypatch.setattr(feed, '_handle_tick', ingest)
        monkeypatch.setattr(feed.asyncio, 'sleep', quick_sleep)
        task = asyncio.create_task(feed.start_mt5_redis_listener())
        await asyncio.wait_for(got_tick.wait(), 1)
        await feed.stop_mt5_redis_listener()
        assert task.done()
        assert len(clients) == 2
        assert all(c.closed and c.stopped for c in clients)
        assert not feed._listener_running
        assert not feed._diag['connected']
        assert not [t for t in asyncio.all_tasks() if t.get_name() == 'mt5-bar-reader']
    asyncio.run(run())


def test_stream_connection_failure_propagates_instead_of_spinning(monkeypatch):
    async def run():
        monkeypatch.setattr(feed, '_listener_running', True)
        client = AsyncMock()
        client.xread.side_effect = ConnectionError('pool full')
        with pytest.raises(ConnectionError):
            await feed._read_bar_streams(client)
        assert client.xread.await_count == 1
    asyncio.run(run())


def test_diagnostics_close_pool_on_failure_and_never_expose_credentials(monkeypatch):
    async def run():
        client = AsyncMock()
        client.ping.side_effect = ConnectionError('redis://user:never-disclose@invalid:6379')
        monkeypatch.setattr(feed.redis, 'from_url', lambda *a, **kw: client)
        result = await feed.get_mt5_redis_diagnostics()
        assert 'never-disclose' not in json.dumps(result)
        assert 'redis_url_prefix' not in result
        assert result['feed_healthy'] is False
        client.aclose.assert_awaited_once_with(close_connection_pool=True)
    asyncio.run(run())


def test_diagnostics_use_epoch_ages_and_numeric_subscriber_count(monkeypatch):
    async def run():
        client = AsyncMock()
        client.xinfo_stream.return_value = {'length': 5, 'last-generated-id': '1000-0'}
        client.pubsub_numsub.return_value = [('mt5:tick', 1)]
        monkeypatch.setattr(feed.redis, 'from_url', lambda *a, **kw: client)
        monkeypatch.setattr(feed.time, 'time', lambda: 1000)
        feed._diag.update(connected=True, stream_reader_active=True, last_tick_time=999)
        result = await feed.get_mt5_redis_diagnostics()
        assert result['last_tick_age_seconds'] == 1
        assert result['tick_channel_subscribers'] == 1
        assert result['feed_healthy'] is True
    asyncio.run(run())
