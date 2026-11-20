"""Legacy interface documentation only; concrete implementations use composition.

Kept for external-import compatibility, but not inherited by infrastructure classes.
"""




from typing import Any, AsyncGenerator, Dict, List, Optional


class DocumentInterfaceDML:

    @classmethod
    async def init_class(self):
        pass

    # ==================== INSERT ====================

    async def insert_one(self) -> Optional[Any]:
        pass
    async def insert_many(self) -> Optional[List[Any]]:
       pass

    # ==================== READ ====================

    async def get_one(self,) -> Optional[Dict[str, Any]]:
        pass

    async def stream_many_docs(self,) -> AsyncGenerator[List[Dict[str, Any]], None]:
        pass

    async def get_many(self,) -> List[Dict[str, Any]]:
       pass

    # ==================== UPDATE ====================

    async def update_one(self,) -> bool:
        pass
    async def update_many(self,) -> bool:
        pass


    # ==================== DELETE ====================
    async def delete_one(self):
        pass
    async def delete_many(self):
        pass
