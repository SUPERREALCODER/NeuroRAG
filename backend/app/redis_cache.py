import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def get_cached_answer(tenant_id: int, query: str):
    key = f"{tenant_id}:{query}"
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    return None

def set_cached_answer(tenant_id: int, query: str, answer: dict, expire: int = 3600):
    key = f"{tenant_id}:{query}"
    r.set(key, json.dumps(answer), ex=expire)
