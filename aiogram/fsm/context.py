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

    # ARCHITECTURE: FSM-003, FSM-006, FSM-007, FSM-008
    # Ownership: FSMContext owns single-value lookup semantics because the value is
    # selected from the context-facing data mapping, not by a storage-backend port.
    # Boundary: obtain that mapping through this class's get_data() operation so the
    # existing BaseStorage retrieval contract remains the only persistence boundary.
    # Contract: use the caller's mapping-supported key unchanged and expose the
    # mapping lookup's value or native KeyError without adaptation or fallback.
    # Dependency: get_value depends inward on get_data; BaseStorage and its adapters
    # must not depend on, duplicate, or specialize this context-level selection.
    # Integration seam: the concrete body below owns selection while the traceable
    # tests in tests/test_fsm/test_context.py own behavioral validation.
    async def get_value(self, key: Any) -> Any:
        """Expose the asynchronous single-key operation (FSM-001, FSM-002)."""
        # PSEUDOCODE — single stored FSM data value retrieval:
        # 1. [FSM-003] AWAIT this context's get_data() to obtain the stored data mapping.
        # 2. [FSM-007] Use key exactly as supplied as the mapping lookup key; do not coerce,
        #    normalize, reinterpret, or traverse it.
        # 3. [FSM-006] LOOK UP data[key]; if the mapping has no such key, allow that lookup's
        #    KeyError to propagate to the caller.
        # 4. [FSM-003, FSM-008] RETURN the lookup result exactly as stored, including falsy
        #    values and object identity, without validation, copying, or transformation.
        # 5. [FSM-008] If existing storage retrieval fails, propagate that failure unchanged.
        data = await self.get_data()
        return data[key]

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(key=self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
