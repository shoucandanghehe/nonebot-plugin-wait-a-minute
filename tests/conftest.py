import nonebot
import pytest
from nonebug import NONEBOT_INIT_KWARGS, NONEBOT_START_LIFESPAN


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {'driver': '~none'}
    # Keep startup from replacing the test process's real signal handlers.
    config.stash[NONEBOT_START_LIFESPAN] = False


@pytest.fixture(scope='session', autouse=True)
def after_nonebot_init(_nonebot_init: None) -> None:
    assert nonebot.load_plugin('nonebot_plugin_wait_a_minute') is not None
