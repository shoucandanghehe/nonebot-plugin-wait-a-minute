<!-- markdownlint-disable MD033 MD036 MD041  -->
<div align="center">
  <a href="https://v2.nonebot.dev/store">
    <img src="./img/NoneBotPlugin.png" width="300" alt="logo" />
  </a>

# 等会先

✨ 一个 NoneBot2 插件，让你可以在关机前执行一些操作 ✨

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyPI - Version](https://img.shields.io/pypi/v/nonebot-plugin-wait-a-minute)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

简体中文 | [English](./README.en-US.md)

</div>

## 🤔 这是什么

这个插件为 NoneBot2 实现了优雅关机（Graceful Shutdown）(查看 [nonebot/nonebot2#2479](https://github.com/nonebot/nonebot2/issues/2479))  
即等待事件**处理完毕后**再关机  
同时它还允许你在关机前运行一些函数，类似于[`on_shutdown`](https://nonebot.dev/docs/advanced/runtime-hook#%E7%BB%88%E6%AD%A2%E5%A4%84%E7%90%86)  
但是优先级更高，可以保证在`bot`断连之前执行

## 💿 安装

### 🚀 使用 uv

```bash
uv add nonebot-plugin-wait-a-minute
```

### 🚀 使用 PDM

```bash
pdm add nonebot-plugin-wait-a-minute
```

### 🚀 使用 poetry

```bash
poetry add nonebot-plugin-wait-a-minute
```

## ♿️ 如何使用

```python
from nonebot import require, on_command
from nonebot.matcher import Matcher

require('nonebot_plugin_wait_a_minute') # require plugin

from nonebot_plugin_wait_a_minute import graceful, on_shutdown_before

# 优雅关机
@on_command('foo').handle()
@graceful()  # 👈 添加 graceful 装饰器到 handle 装饰器下面
# 或者，你可以使用 @graceful(block=True) 来阻止进入关机等待时运行新的 handle
async def _(matcher: Matcher):
    matcher.send('foo')

# 关机前 hook
@on_shutdown_before
def _():
    # 整点啥()
    ...

# 或者使用 async
@on_shutdown_before
async def _():
    # await 整点啥()
    ...
```

## 📄 LICENSE

本项目使用 [MIT](./LICENSE) 许可证开源
