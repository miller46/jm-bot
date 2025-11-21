import signal
import threading
from datetime import datetime
import time

from log import logging


class Lifecycle:
    logger = logging.getLogger()

    def __init__(self):
        self.delay = 0
        self.startup_function = None
        self.shutdown_function = None
        self.every_timers = []

        self.terminated_internally = False
        self.terminated_externally = False
        self.fatal_termination = False
        self._at_least_one_every = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.info(f"Start your engines")

        if self.delay > 0:
            self.logger.info(f"{self.delay}s initial delay...")
            time.sleep(self.delay)

        if self.startup_function:
            self.logger.info("Running startup function")
            self.startup_function()

        self._start_every_timers()

        self._main_loop()

        self.logger.info("Shutting down")

        if len(self.every_timers) > 0:
            self.logger.info("Waiting for timers to terminate...")
            for timer in self.every_timers:
                timer[1].wait()

        if self.shutdown_function:
            self.logger.info("Running shutdown function")
            self.shutdown_function()
            self.logger.info("Shutdown completed")
        self.logger.info("Terminated")
        exit(10 if self.fatal_termination else 0)

    def initial_delay(self, initial_delay: int):
        assert (isinstance(initial_delay, int))
        self.delay = initial_delay

    def on_startup(self, callback):
        assert (callable(callback))
        assert (self.startup_function is None)
        self.startup_function = callback

    def on_shutdown(self, callback):
        assert (callable(callback))

        assert (self.shutdown_function is None)
        self.shutdown_function = callback

    def terminate(self, message=None):
        if message is not None:
            self.logger.warning(message)

        self.terminated_internally = True

    def every(self, frequency_in_seconds: int, callback):
        self.every_timers.append((frequency_in_seconds, AsyncCallback(callback)))

    def _sigint_sigterm_handler(self, sig, frame):
        if self.terminated_externally:
            self.logger.warning("Graceful termination - SIGINT/SIGTERM already in progress")
        else:
            self.logger.warning("Received SIGINT/SIGTERM, will terminate gracefully")
            self.terminated_externally = True

    def _start_every_timers(self):
        for timer in self.every_timers:
            self._start_every_timer(timer[0], timer[1])

        if len(self.every_timers) > 0:
            self.logger.info("Started timer(s)")

    def _start_every_timer(self, frequency_in_seconds: int, callback):
        def setup_timer(delay):
            timer = threading.Timer(delay, func)
            timer.daemon = True
            timer.start()

        def func():
            try:
                if not self.terminated_internally and not self.terminated_externally:
                    def on_start():
                        self.logger.debug(f"Processing timer...")

                    def on_finish():
                        self.logger.debug(f"Finished processing timer")

                    if not callback.trigger(on_start, on_finish):
                        self.logger.debug(f"Ignoring timer, previous one already running")
                else:
                    self.logger.debug(f"Ignoring timer, already terminating")
            except:
                setup_timer(frequency_in_seconds)
                raise
            setup_timer(frequency_in_seconds)

        setup_timer(1)
        self._at_least_one_every = True

    def _main_loop(self):
        # terminate gracefully on either SIGINT or SIGTERM
        signal.signal(signal.SIGINT, self._sigint_sigterm_handler)
        signal.signal(signal.SIGTERM, self._sigint_sigterm_handler)

        while self._at_least_one_every:
            time.sleep(1)

            # if the keeper logic asked us to terminate, we do so
            if self.terminated_internally:
                self.logger.warning("Termination triggered internally")
                break

            # if SIGINT/SIGTERM asked us to terminate, we do so
            if self.terminated_externally:
                self.logger.warning("Terminating, SIGINT/SIGTERM signal received")
                break


class AsyncCallback:

    def __init__(self, callback):
        self.callback = callback
        self.thread = None

    def trigger(self, on_start=None, on_finish=None, *args) -> bool:
        if self.thread is None or not self.thread.is_alive():
            def thread_target():
                if on_start is not None:
                    on_start()
                if len(args) > 0:
                    self.callback(args[0])
                else:
                    self.callback()
                if on_finish is not None:
                    on_finish()

            self.thread = threading.Thread(target=thread_target)
            self.thread.start()
            return True
        else:
            return False

    def wait(self):
        if self.thread is not None:
            self.thread.join()
