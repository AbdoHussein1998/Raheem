"""Legacy interface documentation only; concrete implementations use composition.

Kept for external-import compatibility, but not inherited by infrastructure classes.
"""


class ConnectionManagerInterface:

    @classmethod
    async def init_class(cls):
        pass

    async def connect(self):
        pass
    async def disconnect(self):
        pass
    async def reconnect(self):
        pass
    async def ensure_connected(self):
        pass
