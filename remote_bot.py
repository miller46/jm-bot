from base_bot import BaseBot

from abc import ABC, abstractmethod
import redis


class BotWithRedisRemoteConfig(BaseBot):

    def __init__(self, args: list, **kwargs):
        super().__init__(args, **kwargs)
        self.redis_host = self.arguments.redis_host
        self.redis_port = self.arguments.redis_port
        self.redis_username = self.arguments.redis_username
        self.redis_password = self.arguments.redis_password
        self.redis = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True,
            username=self.redis_username,
            password=self.redis_password,
        )
        can_connect = self.verify_redis_connection()
        assert can_connect, "Unable to connect to redis (Invalid credentials?)"

    def init_args(self, parser):
        parser.add_argument("--redis-host", help="Redis server host", default="localhost", type=str)
        parser.add_argument("--redis-port", help="Redis server port", default=6379, type=int)
        parser.add_argument("--redis-username", help="Redis username", default="default", type=str)
        parser.add_argument("--redis-password", help="Redis password", default="", type=str)

    def verify_redis_connection(self):
        try:
            return self.redis.ping()
        except redis.ConnectionError as e:
            self.logging.error(f"Redis connection failed: {e}")
            return False
        except redis.AuthenticationError as e:
            self.logging.error(f"Redis authentication failed: {e}")
            return False
        except Exception as e:
            self.logging.error(f"Redis error: {e}")
            return False

    @abstractmethod
    def on_startup(self):
        pass

    @abstractmethod
    def on_run_loop(self):
        pass

    @abstractmethod
    def on_shutdown(self):
        pass

    def save_remote_status(self, status):
        last_run_key_name = f"{self.rig_id}_last_run"
        self.redis.set(last_run_key_name, status)

    def is_kill_switch_called(self):
        remote_config_key = f"{self.rig_id}_kill_switch"
        kill_switch = self.redis.get(remote_config_key)
        if kill_switch is None:
            self.logging.warning(f"Kill switch None (can happen if kill switch has never been set before or if rig_id changes)")
            return False
        elif type(kill_switch) is not bool:
            self.logging.warning(f"Kill switch unexpected format: {kill_switch}")
            return False
        else:
            return kill_switch
