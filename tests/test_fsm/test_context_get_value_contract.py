"""Verification contracts for FSMContext single-value retrieval."""

from copy import deepcopy
from inspect import iscoroutinefunction

import pytest

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage


@pytest.fixture()
def context():
    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=2, user_id=3)
    return FSMContext(storage=storage, key=key)


class TestFSMContextGetValueContract:
    async def test_fsmval_001_public_get_value_is_async_and_awaitable(self, context):
        """GUID: FSMVAL-001."""
        await context.set_data({"answer": 42})

        assert iscoroutinefunction(FSMContext.get_value)
        assert await context.get_value("answer") == 42

    async def test_fsmval_002_present_key_returns_exact_value_from_get_data_mapping_lookup(
        self, context
    ):
        """GUID: FSMVAL-002."""
        value = object()
        await context.set_data({"present": value})
        expected = (await context.get_data())["present"]

        assert await context.get_value("present") is expected

    async def test_fsmval_003_absent_key_raises_key_error_without_implicit_default(
        self, context
    ):
        """GUID: FSMVAL-003."""
        await context.set_data({"present": "value"})

        with pytest.raises(KeyError, match="absent"):
            await context.get_value("absent")

    async def test_fsmval_004_successful_get_value_preserves_stored_data_snapshot(
        self, context
    ):
        """GUID: FSMVAL-004; successful retrieval transition."""
        await context.set_data({"present": {"nested": [1, 2, 3]}, "other": True})
        snapshot = deepcopy(await context.get_data())

        await context.get_value("present")

        assert await context.get_data() == snapshot

    async def test_fsmval_004_absent_key_error_preserves_stored_data_snapshot(
        self, context
    ):
        """GUID: FSMVAL-004; failed retrieval transition."""
        await context.set_data({"present": {"nested": [1, 2, 3]}, "other": True})
        snapshot = deepcopy(await context.get_data())

        with pytest.raises(KeyError):
            await context.get_value("absent")

        assert await context.get_data() == snapshot

    async def test_fsmval_005_get_data_mapping_lookup_remains_supported_and_unchanged(
        self, context
    ):
        """GUID: FSMVAL-005."""
        await context.set_data({"present": "value"})

        data = await context.get_data()

        assert data["present"] == "value"
        with pytest.raises(KeyError, match="absent"):
            data["absent"]
