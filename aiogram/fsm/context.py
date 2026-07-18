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

    # FSMVALUE-001, FSMVALUE-002: async get_value(key: str) -> Any
    # FSMVALUE-003, FSMVALUE-004: data := await storage.get_data(key=self.key), using
    # the existing storage contract and this context's complete, strategy-derived address.
    # FSMVALUE-002: if key is not a member of data, raise KeyError(key), including when
    # data is empty; do not substitute a default or infer absence from the stored value.
    # FSMVALUE-001: otherwise return data[key] exactly, including a value of None.
    # FSMVALUE-005: on both branches, perform no state or data write; success and failure
    # therefore leave the observable FSM state and complete stored data unchanged.

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(key=self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
