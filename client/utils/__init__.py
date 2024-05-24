import math
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
    EMAIL = "📧"
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
    FROG = "🐸"
    HOURGLASS_START = "⏳"
    HOURGLASS_END = "⌛️"
    MOYAI = "🗿"
    CLOWN = "🤡"
    WHEELCHAIR = "♿️"
    CRYING_CAT = "😿"
    LEFT = "⬅"
    RIGHT = "➡"
    BUG = "🪲"
    INCOMING_ENVELOPE = "📨"
    UNLOCK = "🔓"
    PENCIL = "✏️"
    BROKEN_HEARTH = "💔"
    ZZZ = "💤"
    ZAP = "⚡️"
    YUM = "😋"
    WATCH = "⌚️"
    DECIDUOUS_TREE = "🌳"
    DROPLET = "💧"
    FALLEN_LEAF = "🍂"


config = ConfigParser()

config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), "config.ini")))


def create_progress_text(
        divisible: int,
        divider: int,
        *,
        progress_element: str = Emoji.GREEN_BIG_SQUARE,
        remaining_element: str = Emoji.GREY_BUG_SQUARE,
        length_widget: int = 10,
        show_digits: bool = True
):
    if divisible > divider:
        percent = 100
        progress = progress_element * length_widget
    else:
        float_fraction = divisible / divider * length_widget
        percent = math.ceil(float_fraction * 10)
        fraction = math.ceil(float_fraction)
        grey_progress = (length_widget - fraction) * remaining_element
        green_progress = fraction * progress_element
        progress = green_progress + grey_progress

    if show_digits:
        return f"{progress} {percent}%"
    return progress
