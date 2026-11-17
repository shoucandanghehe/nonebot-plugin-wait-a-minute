import asyncio
import importlib
from unittest.mock import patch

import pytest
from nonebot.exception import FinishedException, PausedException, RejectedException, SkippedException


@pytest.mark.usefixtures('app')
@pytest.mark.parametrize(
    ('exception', 'is_failure'),
    [
        (ValueError(), True),
        (SkippedException(), True),
        (FinishedException(), False),
        (PausedException(), False),
        (RejectedException(), False),
    ],
)
async def test_failed_task_still_waits_for_other_work(*, exception: Exception, is_failure: bool) -> None:
    plugin = importlib.import_module('nonebot_plugin_wait_a_minute')
    failed = asyncio.Event()
    completed = []

    async def failure() -> None:
        raise exception

    async def remaining_work() -> None:
        await failed.wait()
        completed.append('work')

    tasks = [asyncio.create_task(remaining_work()), asyncio.create_task(failure())]
    tasks[1].add_done_callback(lambda _: failed.set())
    with (
        patch.object(plugin.Hook, 'tasks', tasks),
        patch.object(plugin, 'logger') as logger,
        patch.object(plugin.Hook, 'status', plugin.Status.RUNNING),
        patch.object(plugin.signal, 'raise_signal', side_effect=lambda _: completed.append('signal')),
    ):
        try:
            await plugin.Hook.check_task(plugin.signal.SIGTERM)
            assert completed == ['work', 'signal']
            assert plugin.Hook.status == plugin.Status.FINISHED
            assert logger.opt.call_count == int(is_failure)
            if is_failure:
                logger.opt.assert_called_once_with(exception=exception)
            with pytest.raises(type(exception)) as raised:
                await tasks[1]
            assert raised.value is exception
        finally:
            await asyncio.gather(*tasks, return_exceptions=True)
