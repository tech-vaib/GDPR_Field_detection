It only works with Azure Cache for Redis with Entra ID authentication enabled.

You must assign a Redis Data Access role to the managed identity.

The Python client must use AAD token authentication instead of password.


pip install redis azure-identity tenacity

AzureRedisClient

import json
import time
import threading
import redis
from azure.identity import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential

REDIS_HOST = "your-redis-name.redis.cache.windows.net"
REDIS_PORT = 6380
TOKEN_SCOPE = "https://redis.azure.com/.default"

class AzureRedisClient:

    def __init__(self):
        self.credential = DefaultAzureCredential()
        self._token = None
        self._token_expiry = 0
        self._lock = threading.Lock()

        self.redis_client = None
        self._connect()

    def _get_token(self):
        """Fetch or refresh Azure AD token"""
        with self._lock:

            # refresh token if expiring
            if self._token is None or time.time() > self._token_expiry - 300:
                token = self.credential.get_token(TOKEN_SCOPE)

                self._token = token.token
                self._token_expiry = token.expires_on

        return self._token

    def _connect(self):
        """Create Redis connection pool"""

        token = self._get_token()

        pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            username="default",
            password=token,
            ssl=True,
            max_connections=50,
            decode_responses=True
        )

        self.redis_client = redis.Redis(connection_pool=pool)

    def _refresh_connection_if_needed(self):
        """Reconnect if token expired"""

        if time.time() > self._token_expiry - 300:
            self._connect()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    def set(self, key, value, ttl=None):
        self._refresh_connection_if_needed()
        return self.redis_client.set(key, value, ex=ttl)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    def get(self, key):
        self._refresh_connection_if_needed()
        return self.redis_client.get(key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    def delete(self, key):
        self._refresh_connection_if_needed()
        return self.redis_client.delete(key)




ChatSessionStore

class ChatSessionStore:

    def __init__(self, redis_client):
        self.redis = redis_client
        self.session_ttl = 900  # 15 minutes
        self.max_messages = 8

    def get_context(self, session_id):

        key = f"chat:{session_id}"

        data = self.redis.get(key)

        if not data:
            return []

        return json.loads(data)

    def save_context(self, session_id, messages):

        # keep only last N messages
        messages = messages[-self.max_messages:]

        key = f"chat:{session_id}"

        self.redis.set(
            key,
            json.dumps(messages),
            ttl=self.session_ttl
        )

    def clear(self, session_id):

        key = f"chat:{session_id}"
        self.redis.delete(key)




Chat Flow Example:

redis_client = AzureRedisClient()
chat_store = ChatSessionStore(redis_client)

def handle_chat(session_id, user_message):

    context = chat_store.get_context(session_id)

    context.append({
        "role": "user",
        "content": user_message
    })

    response = call_llm(context)

    context.append({
        "role": "assistant",
        "content": response
    })

    chat_store.save_context(session_id, context)

    return response
