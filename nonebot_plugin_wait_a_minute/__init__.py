from __future__ import annotations

import signal
from asyncio import Task, create_task, gather, get_event_loop
from enum import Enum, auto
from functools import wraps
from types import FrameType
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Optional, TypeVar

from nonebot import get_driver
from nonebot.consts import WINDOWS
from nonebot.exception import SkippedException
from nonebot.log import logger
from nonebot.matcher import Matcher  # noqa: TCH002 # NoneBot Dependency Injection Require
from nonebot.message import run_preprocessor
from nonebot.plugin import PluginMetadata
from nonebot.utils import is_coroutine_callable, run_sync
from typing_extensions import ParamSpec, TypeAlias

from .config import Config, config

if TYPE_CHECKING:
    from collections.abc import Coroutine

__plugin_meta__ = PluginMetadata(
    name='Wait a minute',
    description='A nonebot plugin for waiting for an event to complete before closing it',
    usage='@on_shutdown_before',
    type='library',
    homepage='https://github.com/shoucandanghehe/nonebot-plugin-wait-a-minute',
    config=Config,
    supported_adapters=None,
)

T = TypeVar('T')
P = ParamSpec('P')

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
    def graceful(
        cls, *, block: bool = False
    ) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
        def decorator(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if cls.status == Status.RUNNING and block is True:
                    logger.warning('block is True, so this handle will be skipped')
                    raise SkippedException
                cls.tasks.append(task := create_task(func(*args, **kwargs)))
                task.add_done_callback(lambda _: cls.tasks.remove(task))
                return await task

            wrapper.__setattr__('__graceful_hook__', True)
            return wrapper

        return decorator

    @classmethod
    def sig_handle(cls, original_handle: signal._HANDLER) -> SigHandleFunc:
        def inner(signum: int, frame: FrameType | None) -> None:  # noqa: ARG001
            if not cls.funcs and not cls.tasks:
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
        while True:
            if cls.tasks:
                await gather(*cls.tasks)
                cls.tasks = [i for i in cls.tasks if not i.done()]
            else:
                break
        cls.status = Status.FINISHED
        signal.raise_signal(signum)


@driver.on_startup
async def _() -> None:
    signal.signal(signal.SIGINT, Hook.sig_handle(signal.getsignal(signal.SIGINT)))
    signal.signal(signal.SIGTERM, Hook.sig_handle(signal.getsignal(signal.SIGTERM)))
    if WINDOWS is True:
        signal.signal(signal.SIGBREAK, Hook.sig_handle(signal.getsignal(signal.SIGBREAK)))
    logger.success('Signal hook installed')


if config.wait.block_other:

    @run_preprocessor
    async def _(matcher: Matcher):
        if Hook.status in {Status.RUNNING, Status.FINISHED}:
            matcher.remain_handlers = [
                i for i in matcher.remain_handlers if getattr(i.call, '__graceful_hook__', False)
            ]


on_shutdown_before = Hook.register
graceful = Hook.graceful

__all__ = ['on_shutdown_before', 'graceful']
