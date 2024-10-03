<!-- markdownlint-disable MD033 MD036 MD041  -->
<div align="center">
  <a href="https://v2.nonebot.dev/store">
    <img src="./img/NoneBotPlugin.png" width="300" alt="logo" />
  </a>

# Wait a Minute

✨ A nonebot plugin for running some func before closing the bot ✨

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyPI - Version](https://img.shields.io/pypi/v/nonebot-plugin-wait-a-minute)
[![pdm-managed](https://img.shields.io/endpoint?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fpdm-project%2F.github%2Fbadge.json)](https://pdm-project.org)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

[简体中文](./README.md) | English

</div>

## 🤔 What is this

This plugin implements graceful shutdown for NoneBot2 (see [nonebot/nonebot2#2479](https://github.com/nonebot/nonebot2/issues/2479))  
It waits for events to **finish processing** before shutdown  
It also allows you to run some functions before shutdown, similar to [`on_shutdown`](https://nonebot.dev/docs/advanced/runtime-hook#%E7%BB%88%E6%AD%A2%E5%A4%84%E7%90%86)  
But with higher priority, ensuring execution before `bot` disconnects

## 💿 Installation

### 🚀 Using uv

```bash
uv add nonebot-plugin-wait-a-minute
```

### 🚀 Using PDM

```bash
pdm add nonebot-plugin-wait-a-minute
```

### 🚀 Using poetry

```bash
poetry add nonebot-plugin-wait-a-minute
```

## ♿️ How to use

```python
from nonebot import require, on_command
from nonebot.matcher import Matcher

require('nonebot_plugin_wait_a_minute') # require plugin

from nonebot_plugin_wait_a_minute import graceful, on_shutdown_before

# Graceful shutdown
@on_command('foo').handle()
@graceful()  # 👈 Add graceful decorator below the handle decorator
# Or, you can use @graceful(block=True) to prevent new handles from running during shutdown wait
async def _(matcher: Matcher):
    matcher.send('foo')

# Pre-shutdown hook
@on_shutdown_before
def _():
    # Do something()
    ...

# Or use async
@on_shutdown_before
async def _():
    # await Do something()
    ...
```

## 📄 LICENSE

This project is open-sourced under the [MIT](./LICENSE) license
