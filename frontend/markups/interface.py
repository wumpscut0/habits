from frontend.markups import SerializableMixin
from frontend.markups.authorization import Authorization


class Interface(SerializableMixin):
    def __init__(self):
        self._authorization = Authorization()

    @property
    def authorization(self):
        return self._authorization
