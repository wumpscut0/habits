import os
import pickle
from typing import Union, Any

from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, ExpiryT, AbsExpiryT

from client.markups import InitializeMarkupInterface
from client.utils import config

VERIFY_CODE_EXPIRATION = config.getint("limitations", "VERIFY_CODE_EXPIRATION")
PASSWORD_EXPIRATION = config.getint("limitations", "PASSWORD_EXPIRATION")
EMAIL_EXPIRATION = config.getint("limitations", "EMAIL_EXPIRATION")


class CustomRedis(Redis):
    def set(
        self,
        name: KeyT,
        value: Any,
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

    def setex(self, name: KeyT, time: ExpiryT, value: Any) -> ResponseT:
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


class HourGlassAnimationIdsPull:
    storage = CustomRedis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=1)

    @property
    def pull(self):
        return self.storage.get(f"hour_glass_animation_pull")

    def add_id(self, animation_id: str):
        pull = self.pull
        pull.add(animation_id)
        self.pull = pull

    def remove_id(self, animation_id: str):
        pull = self.pull
        pull.add(animation_id)
        self.pull = pull

    @pull.setter
    def pull(self, data: set[str]):
        self.storage.set(f"hour_glass_animation_pull", data)


class Storage:
    storage = CustomRedis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=1)

    def __init__(self, user_id=None):
        self.user_id = user_id

    @property
    def context(self):
        return self.storage.get(f"context:{self.user_id}")

    @context.setter
    def context(self, data: Any):
        self.storage.set(f"context:{self.user_id}", data)

    @property
    def first_name(self):
        return self.storage.get(f"first_name:{self.user_id}")

    @first_name.setter
    def first_name(self, data: Any):
        self.storage.set(f"first_name:{self.user_id}", data)

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
    def message_ids_pull(self):
        pull = self.storage.get(f"message_ids_pull:{self.user_id}")
        if pull is None:
            return []
        return pull

    @property
    def last_message_id(self):
        try:
            return self.message_ids_pull[-1]
        except IndexError:
            pass

    def add_message_id_to_the_pull(self, message_id: int):
        pull = self.message_ids_pull
        pull.append(message_id)
        self.message_ids_pull = pull

    def pop_last_message_id_from_the_pull(self):
        pull = self.message_ids_pull
        try:
            pull.pop()
            self.message_ids_pull = pull
        except IndexError:
            pass

    @message_ids_pull.setter
    def message_ids_pull(self, data: Any):
        self.storage.set(f"message_ids_pull:{self.user_id}", data)

    @property
    def verify_code(self):
        return self.storage.getex(f"verify_code:{self.user_id}")

    @verify_code.setter
    def verify_code(self, data: Any):
        self.storage.setex(f"verify_code:{self.user_id}", VERIFY_CODE_EXPIRATION, data)

    @property
    def email(self):
        return self.storage.getex(f"email:{self.user_id}")

    @email.setter
    def email(self, data: Any):
        self.storage.setex(f"email:{self.user_id}", EMAIL_EXPIRATION, data)

    @property
    def password(self):
        return self.storage.getex(f"password:{self.user_id}")

    @password.setter
    def password(self, data: Any):
        self.storage.setex(f"password:{self.user_id}", PASSWORD_EXPIRATION, data)

    @property
    def hash(self):
        return self.storage.get(f"hash:{self.user_id}")

    @hash.setter
    def hash(self, data: Any):
        self.storage.set(f"hash:{self.user_id}", data)
