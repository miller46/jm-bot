import sys
from remote_bot import BotWithRedisRemoteConfig

class ExampleRedisBot(BotWithRedisRemoteConfig):

    def on_startup(self):
        self.logging.info("Startup")
        pass

    def on_run_loop(self):
        self.logging.info("Loop")
        pass

    def on_shutdown(self):
        self.logging.info("Shutdown")
        pass


if __name__ == '__main__':
    ExampleRedisBot(sys.argv[1:]).main()