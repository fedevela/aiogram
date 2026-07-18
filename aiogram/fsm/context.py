from typing import Any, Dict, Optional

from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey


class FSMContext:
    def __init__(self, storage: BaseStorage, key: StorageKey) -> None:
        self.storage = storage
        self.key = key

    async def set_state(self, state: StateType = None) -> None:
        await self.storage.set_state(key=self.key, state=state)

    async def get_state(self) -> Optional[str]:
        return await self.storage.get_state(key=self.key)

    async def set_data(self, data: Dict[str, Any]) -> None:
        await self.storage.set_data(key=self.key, data=data)

    async def get_data(self) -> Dict[str, Any]:
        return await self.storage.get_data(key=self.key)

    # GUID: FSMVAL-001, FSMVAL-004, FSMVAL-005
    # ASYNC PROCEDURE get_value(key: str) -> Any:
    #   data <- AWAIT self.storage.get_data(key=self.key)
    #   Preserve the configured storage instance and pass the context's StorageKey unchanged;
    #   depend only on the existing BaseStorage.get_data contract for every backend.
    # GUID: FSMVAL-002, FSMVAL-003
    #   RETURN data[key] by mapping subscription so every present value is returned exactly,
    #   including falsy and empty values; if key is absent (also when data is empty),
    #   propagate the subscription's KeyError without substituting a default.
    # GUID: FSMVAL-006, FSMVAL-008
    #   Perform no state or data write and do not alter the retrieved mapping; leave existing
    #   data, state, update, clear, and isolation control flows and outcomes unchanged.

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(key=self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
