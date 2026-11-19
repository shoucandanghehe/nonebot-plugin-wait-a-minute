import asyncio
import importlib
from functools import partial
from threading import Event
from unittest.mock import Mock, patch

import pytest
from nonebot.exception import (
    FinishedException,
    IgnoredException,
    MockApiException,
    NetworkError,
    PausedException,
    RejectedException,
    SkippedException,
    StopPropagation,
)
from nonebot.matcher import Matcher


@pytest.mark.usefixtures('app')
@pytest.mark.parametrize('matcher_task', [False, True])
@pytest.mark.parametrize(
    'exception, logs_error',
    [
        (ValueError(), True),
        (NetworkError('test'), True),
        (FinishedException(), False),
        (PausedException(), False),
        (RejectedException(), False),
        (SkippedException(), False),
        (StopPropagation(), False),
        (IgnoredException('test'), False),
        (MockApiException(None), False),
    ],
)
async def test_shutdown_control_flow(*, exception: Exception, logs_error: bool, matcher_task: bool) -> None:
    plugin = importlib.import_module('nonebot_plugin_wait_a_minute')
    entered, release, failed = asyncio.Event(), asyncio.Event(), asyncio.Event()
    completed = []

    async def failure() -> None:
        entered.set()
        await release.wait()
        raise exception

    async def remaining_work() -> None:
        await failed.wait()
        completed.append('work')

    with (
        patch.object(plugin.Hook, 'tasks', []),
        patch.object(plugin.Hook, 'status', plugin.Status.NOT_RUNNING_YET),
        patch.object(plugin, 'logger') as logger,
        patch.object(plugin.signal, 'raise_signal', side_effect=lambda _: completed.append('signal')),
    ):
        if matcher_task:
            matcher = Matcher.new(handlers=[plugin.graceful()(failure)])()
            runner = asyncio.create_task(matcher.simple_run(Mock(), Mock(), {}))
            await entered.wait()
            task = plugin.Hook.tasks[0]
        else:
            task = runner = asyncio.create_task(failure())
            plugin.Hook.tasks.append(task)
        other = asyncio.create_task(remaining_work())
        plugin.Hook.tasks.append(other)
        task.add_done_callback(lambda _: failed.set())
        release.set()
        await plugin.Hook.check_task(plugin.signal.SIGTERM)
        await asyncio.gather(runner, return_exceptions=True)
        assert completed == ['work', 'signal']
        assert plugin.Hook.status == plugin.Status.FINISHED
        assert task.exception() is exception
        assert logger.opt.call_count == int(logs_error)


@pytest.mark.usefixtures('app')
async def test_shutdown_waits_for_sync_matcher_handler() -> None:
    plugin = importlib.import_module('nonebot_plugin_wait_a_minute')
    loop = asyncio.get_running_loop()
    entered, release = asyncio.Event(), Event()
    order = []

    def handler() -> None:
        loop.call_soon_threadsafe(entered.set)
        assert release.wait(5)
        order.append('handler')

    with (
        patch.object(plugin.Hook, 'tasks', []),
        patch.object(plugin.Hook, 'status', plugin.Status.NOT_RUNNING_YET),
        patch.object(plugin.signal, 'raise_signal', side_effect=lambda _: order.append('signal')),
    ):
        matcher = Matcher.new(handlers=[plugin.graceful()(handler)])()
        runner = asyncio.create_task(matcher.simple_run(Mock(), Mock(), {}))
        try:
            await asyncio.wait_for(entered.wait(), 5)
            assert len(plugin.Hook.tasks) == 1
            shutdown = asyncio.create_task(plugin.Hook.check_task(plugin.signal.SIGTERM))
            await asyncio.sleep(0)
            assert not shutdown.done()
            release.set()
            await asyncio.wait_for(asyncio.gather(runner, shutdown), 5)
            assert order == ['handler', 'signal']
        finally:
            release.set()
            await asyncio.gather(runner, return_exceptions=True)


@pytest.mark.usefixtures('app')
async def test_graceful_preserves_args_and_results() -> None:
    plugin = importlib.import_module('nonebot_plugin_wait_a_minute')

    def sync_handler(value: int, *, scale: int) -> int:
        return value * scale

    async def async_handler(value: int, *, scale: int) -> int:
        return sync_handler(value, scale=scale)

    def returning_awaitable(value: int, *, scale: int) -> object:
        return async_handler(value, scale=scale)

    with patch.object(plugin.Hook, 'tasks', []):
        assert (
            await plugin.graceful()(sync_handler)(2, scale=3),
            await plugin.graceful()(async_handler)(2, scale=4),
            await plugin.graceful()(partial(async_handler, 2))(scale=5),
            await plugin.graceful()(returning_awaitable)(2, scale=6),
        ) == (6, 8, 10, 12)


@pytest.mark.usefixtures('app')
async def test_graceful_block_skips_sync_handler_during_shutdown() -> None:
    plugin = importlib.import_module('nonebot_plugin_wait_a_minute')
    called = Mock()

    def handler() -> None:
        called()

    with (
        patch.object(plugin.Hook, 'status', plugin.Status.RUNNING),
        patch.object(plugin.Hook, 'tasks', []),
        pytest.raises(SkippedException),
    ):
        await plugin.graceful(block=True)(handler)()
    called.assert_not_called()
