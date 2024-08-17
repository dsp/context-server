# Context Server

This repository contains language specific libraries to build `context-server` for Zed's Context Server feature.
Context server allow programs to provide commands and tools for Zed's assistant panel. They make it easy to
build the workflows and integration *you* care about into Zed's AI features.

## Getting Started

### Python

#### Using PIP
Install `context-server` via PIP.
```sh
$ pip install context-server
```

#### Using pyproject.toml
Create a new `pyproject.toml` or edit your existing one. Add `dependencies = ["context-server"]`. For example:

```toml
[project]
name = "YOUR PROJECT"
version = "0.1.0"
description = "YOUR DESCRIPTION"
authors = []
dependencies = ["context-server"]
readme = "README.md"
requires-python = ">= 3.8"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### Create a project
```python
from context_server.server import ContextServer
from context_server.types import PromptInfo
from context_server.transport import Stdio

app = ContextServer(__name__)

@app.prompt_list()
def list_prompts() -> list[PromptInfo]:
    ...

app.runloop(Stdio())
```
