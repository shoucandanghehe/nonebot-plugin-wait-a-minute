from __future__ import annotations

from nonebot import get_plugin_config
from pydantic import BaseModel, Field


class ScopedConfig(BaseModel):
    block_other: bool = True


class Config(BaseModel):
    wait: ScopedConfig = Field(default_factory=ScopedConfig)


config = get_plugin_config(Config)
