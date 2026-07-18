import inspect
from unittest.mock import AsyncMock

import pytest

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage


def make_context(storage=None, *, chat_id=1):
    storage = storage or MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=chat_id, user_id=1)
    return FSMContext(storage=storage, key=key)


class TestFSMContextGetValueContract:
    async def test_fsmval_001_get_value_is_an_async_fsm_context_operation(self):
        """GUID: FSMVAL-001 -- awaiting get_value(key) exposes single-value retrieval."""
        context = make_context()
        await context.set_data({"name": "Alice"})

        assert inspect.iscoroutinefunction(FSMContext.get_value)
        assert await context.get_value("name") == "Alice"

    @pytest.mark.parametrize("value", [None, False, 0, "", [], {}])
    async def test_fsmval_002_existing_key_returns_exact_falsy_or_empty_stored_value(
        self, value
    ):
        """GUID: FSMVAL-002 -- existing None, False, zero, string, list, and dict survive."""
        context = make_context()
        await context.set_data({"value": value})

        assert await context.get_value("value") == value

    async def test_fsmval_003_missing_key_in_nonempty_data_raises_key_error(self):
        """GUID: FSMVAL-003 -- requesting an absent key from stored data raises KeyError."""
        context = make_context()
        await context.set_data({"present": "value"})

        with pytest.raises(KeyError, match="missing"):
            await context.get_value("missing")

    async def test_fsmval_003_missing_key_with_no_stored_data_raises_key_error(self):
        """GUID: FSMVAL-003 -- requesting a key when no data exists raises KeyError."""
        context = make_context()

        with pytest.raises(KeyError, match="missing"):
            await context.get_value("missing")

    async def test_fsmval_004_distinct_storage_keys_return_only_their_own_value(self):
        """GUID: FSMVAL-004 -- get_value uses configured storage and unchanged StorageKey."""
        storage = MemoryStorage()
        first = make_context(storage, chat_id=1)
        second = make_context(storage, chat_id=2)
        await first.set_data({"value": "first"})
        await second.set_data({"value": "second"})

        assert await first.get_value("value") == "first"
        assert await second.get_value("value") == "second"

    async def test_fsmval_005_existing_get_data_storage_contract_supports_get_value(self):
        """GUID: FSMVAL-005 -- no new BaseStorage single-value method is required."""
        storage = AsyncMock()
        storage.get_data.return_value = {"value": object()}
        context = make_context(storage)

        result = await context.get_value("value")

        assert result is storage.get_data.return_value["value"]
        storage.get_data.assert_awaited_once_with(key=context.key)

    async def test_fsmval_005_bundled_get_data_storages_return_exact_existing_value(self):
        """GUID: FSMVAL-005 -- bundled BaseStorage implementations remain compatible."""
        context = make_context(MemoryStorage())
        value = object()
        await context.set_data({"value": value})

        assert await context.get_value("value") is value

    async def test_fsmval_006_get_value_leaves_stored_state_and_data_unchanged(self):
        """GUID: FSMVAL-006 -- retrieval does not mutate complete state or data."""
        context = make_context()
        await context.set_state("active")
        await context.set_data({"value": [1, 2], "other": "preserved"})
        before_state = await context.get_state()
        before_data = await context.get_data()

        await context.get_value("value")

        assert await context.get_state() == before_state
        assert await context.get_data() == before_data

    async def test_fsmval_008_get_value_preserves_existing_fsm_operation_results(self):
        """GUID: FSMVAL-008 -- data, state, update, clear, and isolation remain unchanged."""
        context = make_context()
        await context.set_state("active")
        await context.set_data({"value": 1})

        assert await context.get_value("value") == 1
        assert await context.update_data({"other": 2}) == {"value": 1, "other": 2}
        assert await context.get_state() == "active"
        assert await context.get_data() == {"value": 1, "other": 2}

        await context.clear()

        assert await context.get_state() is None
        assert await context.get_data() == {}
