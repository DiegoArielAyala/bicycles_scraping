import uuid
import redis

from django.conf import settings


class RedisLock():
    def __init__(self, name, timeout=1800):
        self.key = f"lock:{name}"
        self.timeout = timeout
        self.token = str(uuid.uuid4())
        self.client = redis.Redis.from_url(settings.REDIS_URL)

    def __enter__(self):
        aquired = self.client.set(
            self.key,
            self.token,
            nx=True,
            ex=self.timeout
        )

        if not aquired:
            raise LockNotAcquiredError(f"Could not aquire lock: {self.key}")

        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        release_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        self.client.eval(release_script, 1, self.key, self.token)


class LockNotAcquiredError(Exception):
    pass