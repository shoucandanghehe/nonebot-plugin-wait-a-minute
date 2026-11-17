import asyncio
import importlib
import unittest
from unittest.mock import patch

import nonebot

nonebot.init(driver='~none')
plugin = importlib.import_module('nonebot_plugin_wait_a_minute')


class ShutdownTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_task_still_waits_for_other_work(self) -> None:
        failed = asyncio.Event()
        completed = []

        async def failure() -> None:
            raise ValueError

        async def remaining_work() -> None:
            await failed.wait()
            completed.append('work')

        tasks = [asyncio.create_task(remaining_work()), asyncio.create_task(failure())]
        tasks[1].add_done_callback(lambda _: failed.set())
        with (
            patch.object(plugin.Hook, 'tasks', tasks),
            patch.object(plugin.Hook, 'status', plugin.Status.RUNNING),
            patch.object(plugin.signal, 'raise_signal', side_effect=lambda _: completed.append('signal')),
        ):
            try:
                await plugin.Hook.check_task(plugin.signal.SIGTERM)
                self.assertEqual(completed, ['work', 'signal'])
                self.assertEqual(plugin.Hook.status, plugin.Status.FINISHED)
            finally:
                await asyncio.gather(*tasks, return_exceptions=True)
