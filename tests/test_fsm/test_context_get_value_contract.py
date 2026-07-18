from unittest.mock import AsyncMock

import pytest

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage


def make_key(**kwargs):
    values = {"bot_id": 1, "chat_id": 2, "user_id": 3}
    values.update(kwargs)
    return StorageKey(**values)


class TestFSMContextGetValueContract:
    async def test_fsmvalue_001_present_key_returns_exact_stored_value(self):
        """FSMVALUE-001: present data[key] -> exact stored value."""
        value = object()
        storage = MemoryStorage()
        context = FSMContext(storage=storage, key=make_key())
        await context.set_data({"value": value})

        assert await context.get_value("value") is value

    async def test_fsmvalue_001_present_key_stored_as_none_returns_none(self):
        """FSMVALUE-001: present data[key] containing None -> stored None, not absence."""
        storage = MemoryStorage()
        context = FSMContext(storage=storage, key=make_key())
        await context.set_data({"value": None})

        assert await context.get_value("value") is None

    async def test_fsmvalue_002_absent_key_in_existing_data_raises_key_error(self):
        """FSMVALUE-002: existing data without key -> KeyError."""
        storage = MemoryStorage()
        context = FSMContext(storage=storage, key=make_key())
        await context.set_data({"other": "value"})

        with pytest.raises(KeyError) as error:
            await context.get_value("missing")

        assert error.value.args == ("missing",)

    async def test_fsmvalue_002_absent_key_when_context_has_no_data_raises_key_error(self):
        """FSMVALUE-002: context with no data and requested key -> KeyError."""
        context = FSMContext(storage=MemoryStorage(), key=make_key())

        with pytest.raises(KeyError):
            await context.get_value("missing")

    async def test_fsmvalue_003_get_value_uses_existing_storage_get_data_contract(self):
        """FSMVALUE-003: configured get_data(StorageKey) -> value without new storage API."""
        key = make_key(thread_id=4, business_connection_id="business", destiny="scene")
        storage = AsyncMock(spec=BaseStorage)
        storage.get_data.return_value = {"answer": 42}
        context = FSMContext(storage=storage, key=key)

        assert await context.get_value("answer") == 42
        storage.get_data.assert_awaited_once_with(key=key)
        assert not hasattr(BaseStorage, "get_value")

    async def test_fsmvalue_004_distinct_context_addresses_return_their_own_value(self):
        """FSMVALUE-004: distinct complete or strategy-derived keys -> isolated values."""
        storage = MemoryStorage()
        first = FSMContext(storage=storage, key=make_key(thread_id=10, destiny="first"))
        second = FSMContext(storage=storage, key=make_key(thread_id=20, destiny="second"))
        await first.set_data({"shared": "first value"})
        await second.set_data({"shared": "second value"})

        assert await first.get_value("shared") == "first value"
        assert await second.get_value("shared") == "second value"

    async def test_fsmvalue_005_successful_read_preserves_state_and_complete_data(self):
        """FSMVALUE-005: successful present-key read -> state and complete data unchanged."""
        storage = MemoryStorage()
        context = FSMContext(storage=storage, key=make_key())
        await context.set_state("active")
        await context.set_data({"requested": [1, 2], "other": {"nested": True}})
        state_before = await context.get_state()
        data_before = await context.get_data()

        assert await context.get_value("requested") == [1, 2]
        assert await context.get_state() == state_before
        assert await context.get_data() == data_before

    async def test_fsmvalue_005_missing_key_read_preserves_state_and_complete_data(self):
        """FSMVALUE-005: missing-key read raising KeyError -> state and complete data unchanged."""
        storage = MemoryStorage()
        context = FSMContext(storage=storage, key=make_key())
        await context.set_state("active")
        await context.set_data({"existing": "value"})
        state_before = await context.get_state()
        data_before = await context.get_data()

        with pytest.raises(KeyError):
            await context.get_value("missing")

        assert await context.get_state() == state_before
        assert await context.get_data() == data_before
