import logging
import redis
logging.basicConfig()

class LossError(Exception):
    """Raised when user won with zero guesses"""

def guesswon(r: redis.Redis, guess_wonid: int) -> None:
    with r.pipeline() as pipe:
        error_count = 0
        while True:
            try:
                pipe.watch(guess_wonid)
                nleft: bytes = r.hget(guess_wonid, "guesses")
                if nleft > b"0":
                    pipe.multi()
                    pipe.hincrby(guess_wonid, "Score", 6)
                    pipe.hincrby(guess_wonid, "Score", 5)
                    pipe.hincrby(guess_wonid, "Score", 4)
                    pipe.hincrby(guess_wonid, "Score", 3)
                    pipe.hincrby(guess_wonid, "Score", 2)
                    pipe.hincrby(guess_wonid, "Score", 1)
                    pipe.execute()
                    break
                else:
                    pipe.unwatch()
                    raise LossError(
                        f"Out of guesses, {guess_wonid} you lost"
                    )
            except redis.WatchError:
                error_count += 1
                logging.warning(
                    "WatchError #%d: %s; retrying",
                    error_count, guess_wonid
                )
    return None