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

    # ARCHITECTURE: FSM-001, FSM-002
    # Ownership: FSMContext is the public boundary for the asynchronous get_value
    # contract; place it with the context-facing data operations in this class.
    # Contract: the eventual coroutine signature has one required `key` parameter
    # after `self`, with no variadic positional parameters.
    # Dependency: keep lookup behind FSMContext's existing BaseStorage dependency;
    # these requirements add no storage API and define no lookup-result semantics.
    # Integration seam: implementation belongs here, between get_data and update_data.

    # GUID: FSM-001, FSM-002 - asynchronous single-key FSMContext API
    # PSEUDOCODE: async def get_value(self, key):
    #   INPUT: one required key identifying an entry in this context's stored data.
    #   CALL CONTRACT:
    #     - Expose get_value as a public coroutine operation on FSMContext.
    #     - Require key in the operation signature; if omitted, reject the invocation
    #       during argument binding before the coroutine body can execute.
    #     - Declare no additional positional parameters or variadic arguments; if a
    #       second key argument is supplied, reject it during argument binding.
    #   TRANSITION: after exactly one key is bound, enter the asynchronous operation
    #     and hand off lookup/result behavior to its separately specified obligation.
    #   OUTPUT: an awaitable invocation; lookup results and missing-key behavior are
    #     intentionally not defined by FSM-001 or FSM-002.

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(key=self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
