import asyncio
import importlib
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
