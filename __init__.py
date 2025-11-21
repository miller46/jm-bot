import sys
import argparse
from datetime import datetime
from abc import ABC, abstractmethod

from lifecycle import Lifecycle
from log import logging


class BaseBot(ABC):

    DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    def __init__(self, args: list, **kwargs):
        self.parser = argparse.ArgumentParser(prog='venv')
        self.arguments = self.init_args(args)
        self.run_every = self.arguments.run_every
        self.rig_id = self.arguments.rig_id
        self.delay = self.arguments.delay
        self.run_less_at_night = self.arguments.run_less_at_night
        self.run_less_at_night_start = self.arguments.run_less_at_night_start
        self.run_less_at_night_end = self.arguments.run_less_at_night_end
        self.kill_switch_called = False
        self.update_less_at_night = False
        self.remote_config = None
        self.success_message = None
        self.error_message = None
        self.system_message = None

    def init_args(self, args):
        self.parser.add_argument("--rig-id", help="Name of remote monitoring ID", default="", type=str)
        self.parser.add_argument("--run-every", help="Run 'update' every N seconds", default=1*60, type=int)
        self.parser.add_argument("--delay", help="Initial startup delay", default=0, type=int)
        self.parser.add_argument("--run-less-at-night", help="Don't run during nighttime hours", default=False, type=bool)
        self.parser.add_argument("--run-less-at-night-start", help="Run less at night hour begin (UTC)", default=1, type=int)
        self.parser.add_argument("--run-less-at-night-end", help="Run less at night hour end (UTC)", default=11, type=int)
        known_args, unknown_args = self.parser.parse_known_args(args)
        return known_args

    def main(self):
        self.remote_config = self.get_remote_config()
        if self.remote_config is None:
            logging.error("!!! No remote config !!!\n\nRemote monitoring is not enabled")

        with Lifecycle() as lifecycle:
            run_every_seconds = self.run_every
            if run_every_seconds is None:
                raise Exception(f"Run every N seconds param not set - cannot start loop")
            if self.delay > 0:
                lifecycle.delay = self.delay
            if self.on_startup is not None:
                lifecycle.startup_function = self.on_startup
            if self.on_shutdown is not None:
                lifecycle.shutdown_function = self.on_shutdown
            lifecycle.every(run_every_seconds, self._update_loop)

    def _update_loop(self):
        self.remote_config = self.get_remote_config()
        if self.is_kill_switch_called():
            logging.error("Not executing - Kill Switch called")
            return
        if self.is_run_less_at_node_mode():
            logging.error(f"Not executing - 'Update less often in the middle of the night' mode ...  zzzz")
            return
        self.on_run_loop()
        self.save_remote_status()

    def is_kill_switch_called(self):
        if self.remote_config is None:
            logging.error(f"Rig config not set - no remote monitoring or remote kill switch ")
            return False
        else:
            return self.remote_config.kill_switch

    def is_run_less_at_node_mode(self):
        if self.run_less_at_night:
            hour = datetime.utcnow().hour  # NOTE: UTC time
            if self.run_less_at_night_start <= hour <= self.run_less_at_night_end and hour % 4 != 0:
                return True
        return False

    @staticmethod
    def get_current_datetime():
        return datetime.utcnow().strftime(BaseBot.DATE_FORMAT)

    @abstractmethod
    def on_startup(self):
        pass

    @abstractmethod
    def on_run_loop(self):
        pass

    @abstractmethod
    def on_shutdown(self):
        pass

    def get_remote_config(self):
        return None

    def save_remote_status(self):
        pass

if __name__ == '__main__':
    BaseBot(sys.argv[1:]).main()