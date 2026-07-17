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

    # Pseudocode contract: FSMVAL-001, FSMVAL-002, FSMVAL-003, FSMVAL-004, FSMVAL-005
    # ASYNC FUNCTION get_value(key):
    #     data = AWAIT get_data()                         # FSMVAL-001, FSMVAL-005
    #     TRY:
    #         value = data[key]                          # FSMVAL-002
    #     CATCH KeyError:
    #         PROPAGATE KeyError without a default       # FSMVAL-003
    #         LEAVE stored FSM data unchanged            # FSMVAL-004 (failure path)
    #     LEAVE stored FSM data unchanged                # FSMVAL-004 (success path)
    #     RETURN value exactly as obtained from data     # FSMVAL-002
    # END FUNCTION
    # Preserve get_data() and its direct mapping-lookup semantics unchanged.  # FSMVAL-005

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(key=self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
