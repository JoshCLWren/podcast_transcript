import os
import urllib.parse as urlparse

from redis import Redis
from rq import Connection, Queue

if os.environ.get("env") != "development" or os.environ.get("env") is False:
    from rq import Connection, Queue
    from rq.worker import HerokuWorker as Worker
else:
    from rq import Connection, Queue, Worker

listen = ["high", "default", "low"]


redis_url = os.getenv("REDISTOGO_URL")
if not redis_url and os.environ.get("env") not in ["development", None]:
    print(f"env is {os.getenv('env')}")

    raise RuntimeError("Set up Redis To Go first.")

urlparse.uses_netloc.append("redis")
url = urlparse.urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
