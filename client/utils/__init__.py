import os
import pickle
from base64 import b64decode, b64encode
from configparser import ConfigParser


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





