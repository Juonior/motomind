import json
from typing import List, Dict
from redis.asyncio import Redis


class RedisContextStore:
    def __init__(self, redis_url: str, max_history_messages: int = 20) -> None:
        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self._max = max_history_messages

    @staticmethod
    def _key(session_key: str) -> str:
        return f"{session_key}:history"

    async def append(self, session_key: str, role: str, content: str) -> None:
        entry = json.dumps({"role": role, "content": content})
        key = self._key(session_key)
        await self._redis.rpush(key, entry)
        await self._redis.ltrim(key, -self._max, -1)

    async def history(self, session_key: str) -> List[Dict]:
        items = await self._redis.lrange(self._key(session_key), 0, -1)
        result: List[Dict] = []
        for raw in items:
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict) and "role" in obj and "content" in obj:
                    result.append(obj)
            except Exception:
                continue
        return result

    async def close(self) -> None:
        try:
            await self._redis.aclose()
        except Exception:
            pass


