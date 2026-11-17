import asyncio
import importlib
import signal
import unittest
from typing import ClassVar
from unittest.mock import patch

import nonebot

nonebot.init(driver='~none')
plugin = importlib.import_module('nonebot_plugin_wait_a_minute')


class ShutdownTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        class TestHook(plugin.Hook):
            funcs: ClassVar[list] = []
            tasks: ClassVar[list] = []
            status = plugin.Status.NOT_RUNNING_YET
            callback: asyncio.Task | None = None

        self.hook = TestHook

    async def asyncTearDown(self) -> None:
        tasks = [*self.hook.tasks]
        if self.hook.callback is not None:
            tasks.append(self.hook.callback)
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def check_shutdown(self, *, cancel: bool = False, handler: bool = False) -> None:
        release = asyncio.Event()
        failed = asyncio.Event()
        finished = asyncio.Event()

        async def failure() -> None:
            failed.set()
            if cancel:
                raise asyncio.CancelledError
            message = 'shutdown regression'
            raise ValueError(message)

        @self.hook.register
        async def remaining_work() -> None:
            await release.wait()
            finished.set()

        if handler:
            task = asyncio.create_task(self.hook.graceful()(failure)())
            # Let the wrapper register its tracked task before shutdown starts.
            await asyncio.sleep(0)
            self.addAsyncCleanup(asyncio.gather, task, return_exceptions=True)
        else:
            self.hook.register(failure)

        original = signal.SIG_DFL
        handle = self.hook.sig_handle(original)
        with (
            patch.object(plugin.signal, 'signal') as restore,
            patch.object(plugin.signal, 'raise_signal') as forward,
            patch.object(plugin, 'logger') as logger,
        ):
            handle(signal.SIGTERM, None)
            await asyncio.wait_for(failed.wait(), timeout=1)
            await asyncio.sleep(0)
            self.assertEqual(self.hook.status, plugin.Status.RUNNING)
            self.assertFalse(finished.is_set())
            forward.assert_not_called()
            release.set()
            if self.hook.callback is None:
                self.fail('Shutdown callback was not started')
            await asyncio.wait_for(self.hook.callback, timeout=1)
            self.assertTrue(finished.is_set())
            self.assertEqual(self.hook.status, plugin.Status.FINISHED)
            forward.assert_called_once_with(signal.SIGTERM)
            handle(signal.SIGTERM, None)
            restore.assert_called_once_with(signal.SIGTERM, original)
            self.assertEqual(forward.call_count, 2)
            if cancel:
                logger.warning.assert_called_once()
            else:
                logger.opt.assert_called_once()
                logger.opt.return_value.error.assert_called_once()

    async def test_failing_hook_does_not_abandon_other_work(self) -> None:
        await self.check_shutdown()

    async def test_cancelled_hook_does_not_abandon_other_work(self) -> None:
        await self.check_shutdown(cancel=True)

    async def test_failing_handler_does_not_abandon_other_work(self) -> None:
        await self.check_shutdown(handler=True)
