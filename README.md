<!-- markdownlint-disable MD033 MD036 MD041  -->
<div align="center">
  <a href="https://v2.nonebot.dev/store">
    <img src="./img/NoneBotPlugin.png" width="300" alt="logo" />
  </a>

# NoneBot Plugin Wait a minute

✨ A nonebot plugin for running some func before closing the bot ✨

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyPI - Version](https://img.shields.io/pypi/v/nonebot-plugin-wait-a-minute)
[![pdm-managed](https://img.shields.io/endpoint?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fpdm-project%2F.github%2Fbadge.json)](https://pdm-project.org)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
</div>

## 💿 Install

### 🚀 Use PDM

```bash
pdm add nonebot-plugin-wait-a-minute
```

### 🚀 Use poetry

```bash
poetry add nonebot-plugin-wait-a-minute
```

## ♿️ How To Use

```python
from nonebot import require

require('nonebot_plugin_wait_a_minute') # require plugin

from nonebot_plugin_wait_a_minute import on_shutdown_before

@on_shutdown_before
def _():
    # do something
    ...

# or use async func
@on_shutdown_before
async def _():
    # await do something
    ...
```

## 📄 LICENSE

This project is open source using the [MIT](./LICENSE) license
