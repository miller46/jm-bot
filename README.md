# jm-bot

Base class for continuously running bots. 

## Features

- **Scheduled execution** - Run tasks at specified intervals
- **Lifecycle hooks** - Startup, shutdown, and main loop callbacks
- **Remote monitoring** - Optional remote config and kill switch support
- **Night mode** - Don't run during certain hours (e.g. don't run at night)
- **Graceful shutdown** - Clean signal handling (SIGINT/SIGTERM)
- **Thread-safe** - Async callbacks with overlap prevention

## Usage

Implement the abstract python functions in a child class and invoke that class with the CLI commands (see example in Example section below).

```python
from base_bot import BaseBot
import sys


class MyBot(BaseBot):

    def on_startup(self):
        # Initialize resources
        pass

    def on_run_loop(self):
        # Main bot logic (runs every N seconds)
        pass

    def on_shutdown(self):
        # Cleanup
        pass


if __name__ == '__main__':
    MyBot(sys.argv[1:]).main()
```

## CLI Arguments

- `--run-every` - Execution interval in seconds (default: 60)
- `--delay` - Initial startup delay in seconds (default: 0)
- `--rig-id` - Remote monitoring identifier
- `--run-less-at-night` - Enable reduced nighttime execution
- `--run-less-at-night-start` - Night mode start hour UTC (default: 1)
- `--run-less-at-night-end` - Night mode end hour UTC (default: 11)

## Example

```bash
python my_bot.py --run-every 300 --delay 10 --rig-id production-1
```
