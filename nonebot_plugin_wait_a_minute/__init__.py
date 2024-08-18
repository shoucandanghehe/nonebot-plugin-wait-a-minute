from __future__ import annotations

import signal
from asyncio import Task, gather, get_event_loop
from enum import Enum, auto
from types import FrameType
from typing import Any, Callable, ClassVar, Optional, TypeVar

from nonebot import get_driver
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot.utils import is_coroutine_callable, run_sync
from typing_extensions import TypeAlias

__plugin_meta__ = PluginMetadata(
    name='nonebot-plugin-wait-a-minute',
    description='A nonebot plugin for waiting for an event to complete before closing it',
    usage='@on_shutdown_before',
    type='library',
    homepage='https://github.com/shoucandanghehe/nonebot-plugin-wait-a-minute',
    config=None,
    supported_adapters=None,
)

T = TypeVar('T')

SigHandleFunc: TypeAlias = Callable[[int, Optional[FrameType]], Any]

driver = get_driver()


class Status(Enum):
    NOT_RUNNING_YET = auto()
    RUNNING = auto()
    FINISHED = auto()


class Hook:
    status: Status = Status.NOT_RUNNING_YET
    funcs: ClassVar[list[Callable[[], Any]]] = []
    tasks: ClassVar[list[Task]] = []
    callback: Task | None = None

    @classmethod
    def register(cls, func: Callable[[], T]) -> Callable[[], T]:
        cls.funcs.append(func)
        return func

    @classmethod
    def sig_handle(cls, original_handle: signal._HANDLER) -> SigHandleFunc:
        def inner(signum: int, frame: FrameType | None) -> None:  # noqa: ARG001
            if not cls.funcs:
                cls.status = Status.FINISHED

            if cls.status == Status.NOT_RUNNING_YET:
                cls.status = Status.RUNNING
                loop = get_event_loop()
                for i in cls.funcs:
                    if is_coroutine_callable(i):
                        cls.tasks.append(loop.create_task(i()))
                    else:
                        cls.tasks.append(loop.create_task(run_sync(i)()))
                cls.callback = loop.create_task(cls.check_task(signum))
            elif cls.status == Status.RUNNING:
                logger.warning(f'signal {signum} received, but wait a minute pls')
            elif cls.status == Status.FINISHED:
                signal.signal(signum, original_handle)
                signal.raise_signal(signum)

        return inner

    @classmethod
    async def check_task(cls, signum: int) -> None:
        if cls.tasks:
            await gather(*cls.tasks)
        cls.status = Status.FINISHED
        signal.raise_signal(signum)


@driver.on_startup
async def _() -> None:
    signal.signal(signal.SIGINT, Hook.sig_handle(signal.getsignal(signal.SIGINT)))
    signal.signal(signal.SIGTERM, Hook.sig_handle(signal.getsignal(signal.SIGTERM)))
    logger.success('Signal hook installed')


on_shutdown_before = Hook.register

__all__ = ['on_shutdown_before']
