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

    # PSEUDOCODE — FSMContext single-value lookup
    #
    # ASYNC PROCEDURE get_value(key):  [FSMGV-001]
    #     data := AWAIT self.get_data()  [FSMGV-002, FSMGV-003]
    #     // Read from the mapping returned for this exact context; do not copy,
    #     // update, remove, normalize, or otherwise mutate its stored data.  [FSMGV-004]
    #     value := data[key]
    #     // Direct mapping subscription preserves supported key identity and lookup
    #     // semantics, including propagating KeyError when key is absent.  [FSMGV-005, FSMGV-006]
    #     // Presence is decided by subscription, never by the truthiness of value.  [FSMGV-007]
    #     RETURN value
    # END PROCEDURE
    # Existing get_data control flow and its returned mapping remain unchanged.  [FSMGV-008]

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(key=self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
