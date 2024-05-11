import os
import pickle
from base64 import b64decode, b64encode
from configparser import ConfigParser
from typing import Dict, Union

import jwt
from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, EncodableT, ExpiryT, AbsExpiryT


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


storage = CustomRedis(db=2)


class Emoji:
    OK = "✅"
    DENIAL = "❌"
    INFO = "ℹ"
    BACK = "⬇"
    KEY = "🔑"
    DOOR = "🚪"
    BRAIN = "🧠"
    MEGAPHONE = "📢"
    SHINE_STAR = "🌟"
    WARNING = "⚠"
    SHIELD = "🛡"
    CYCLE = "🔄"
    BELL = "🔔"
    NOT_BELL = "🔕"
    EYE = "👁"
    SPROUT = "🌱"
    DIAGRAM = "📊"
    BULB = "💡"
    GEAR = "⚙"
    ENVELOPE = "✉️"
    LOCK_AND_KEY = "🔐"
    PLUS = "➕"
    UP = "🆙"
    SKIP = "⏭️"
    GREEN_BIG_SQUARE = "🟩"
    GREY_BUG_SQUARE = "⬜️"
    RED_QUESTION = "❓"
    GREY_QUESTION = "❔"
    BAN = "🚫"
    GREEN_CIRCLE = "🟢"
    YELLOW_CIRCLE = "🟡"
    ORANGE_CIRCLE = "🟠"
    RED_CIRCLE = "🔴"
    FLAG_FINISH = "🏁"
    DART = "🎯"
    REPORT = "🧾"
    LIST_WITH_PENCIL = "📝"
    NEW = "🆕"
    TROPHY = "🏆"
    CLOCK = "🕒"


class SerializableMixin:
    async def serialize(self):
        return b64encode(pickle.dumps(self)).decode()


async def deserialize(sequence: str):
    return pickle.loads(b64decode(sequence.encode()))


config = ConfigParser()

config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), "config.ini")))


async def get_service_key():
    return jwt.encode({"password": os.getenv('SERVICES_PASSWORD')}, os.getenv('JWT'))


async def encode_jwt(payload: Dict):
    return jwt.encode(payload, os.getenv('JWT'))


