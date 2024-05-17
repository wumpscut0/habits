import os
import pickle
from typing import Union, Any

from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, EncodableT, ExpiryT, AbsExpiryT

from client.utils import config

VERIFY_CODE_EXPIRATION = config.getint("limitations", "VERIFY_CODE_EXPIRATION")


class CustomRedis(Redis):
    def set(
        self,
        name: KeyT,
        value: EncodableT,
        ex: Union[ExpiryT, None] = None,
        px: Union[ExpiryT, None] = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,
        get: bool = False,
        exat: Union[AbsExpiryT, None] = None,
        pxat: Union[AbsExpiryT, None] = None,
    ) -> ResponseT:
        return super().set(
            name, pickle.dumps(value), ex, px, nx, xx, keepttl, get, exat, pxat,
        )

    def get(self, name: KeyT) -> ResponseT:
        result = super().get(name)
        if result is not None:
            return pickle.loads(result)

    def setex(self, name: KeyT, time: ExpiryT, value: EncodableT) -> ResponseT:
        return super().setex(
            name, time, pickle.dumps(value),
        )

    def getex(
        self,
        name: KeyT,
        ex: Union[ExpiryT, None] = None,
        px: Union[ExpiryT, None] = None,
        exat: Union[AbsExpiryT, None] = None,
        pxat: Union[AbsExpiryT, None] = None,
        persist: bool = False,
    ) -> ResponseT:
        result = super().getex(name, ex, px, exat, pxat, persist)
        if result is not None:
            return pickle.loads(result)


class Storage:
    storage = CustomRedis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=1)

    def __init__(self, user_id=None):
        self.user_id = user_id

    @property
    def is_user_exists(self):
        return self.storage.get(f"is_user_exists:{self.user_id}")

    @is_user_exists.setter
    def is_user_exists(self, data: Any):
        self.storage.set(f"is_user_exists:{self.user_id}", data)

    @property
    def admins(self):
        return self.storage.get(f"admins")

    @admins.setter
    def admins(self, data: Any):
        self.storage.set(f"admins", data)

    @property
    def user_token(self):
        return self.storage.get(f"token:{self.user_id}")

    @user_token.setter
    def user_token(self, data: Any):
        self.storage.set(f"token:{self.user_id}", data)

    @property
    def message_id(self):
        return self.storage.get(f"message_id:{self.user_id}")

    @message_id.setter
    def message_id(self, data: Any):
        self.storage.set(f"message_id:{self.user_id}", data)

    @property
    def hour(self):
        return self.storage.get(f"hour:{self.user_id}")

    @hour.setter
    def hour(self, data: Any):
        self.storage.set(f"hour:{self.user_id}", data)

    @property
    def minute(self):
        return self.storage.get(f"minute:{self.user_id}")

    @minute.setter
    def minute(self, data: Any):
        self.storage.set(f"minute:{self.user_id}", data)

    @property
    def trash(self):
        return self.storage.get(f"trash:{self.user_id}")

    @trash.setter
    def trash(self, data: Any):
        self.storage.set(f"trash:{self.user_id}", data)

    @property
    def verify_code(self):
        return self.storage.getex(f"verify_code:{self.user_id}")

    @verify_code.setter
    def verify_code(self, data: Any):
        self.storage.setex(f"verify_code:{self.user_id}", VERIFY_CODE_EXPIRATION, data)
