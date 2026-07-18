"""Verification contracts for :meth:`FSMContext.get_value`."""

import inspect

import pytest

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage


def make_context(storage: MemoryStorage, *, chat_id: int, user_id: int) -> FSMContext:
    return FSMContext(
        storage=storage,
        key=StorageKey(bot_id=1, chat_id=chat_id, user_id=user_id),
    )


async def test_FSMGV_001_get_value_is_awaitable_on_fsm_context() -> None:
    """GUID: FSMGV-001."""
    state = make_context(MemoryStorage(), chat_id=1, user_id=1)
    await state.set_data({"answer": 42})

    result = state.get_value("answer")

    assert inspect.isawaitable(result)
    assert await result == 42


async def test_FSMGV_002_existing_key_returns_value_from_same_context_get_data_mapping() -> None:
    """GUID: FSMGV-002."""
    state = make_context(MemoryStorage(), chat_id=1, user_id=1)
    await state.set_data({"requested": {"nested": "value"}})

    data = await state.get_data()

    assert await state.get_value("requested") is data["requested"]


async def test_FSMGV_003_same_key_in_distinct_contexts_returns_each_contexts_value() -> None:
    """GUID: FSMGV-003."""
    storage = MemoryStorage()
    first = make_context(storage, chat_id=1, user_id=1)
    second = make_context(storage, chat_id=2, user_id=2)
    await first.set_data({"shared": "first"})
    await second.set_data({"shared": "second"})

    assert await first.get_value("shared") == "first"
    assert await second.get_value("shared") == "second"


async def test_FSMGV_004_existing_key_lookup_leaves_stored_data_unchanged() -> None:
    """GUID: FSMGV-004."""
    state = make_context(MemoryStorage(), chat_id=1, user_id=1)
    await state.set_data({"requested": [1, 2], "other": {"kept": True}})
    before = await state.get_data()

    await state.get_value("requested")

    assert await state.get_data() == before


async def test_FSMGV_005_absent_key_lookup_raises_key_error() -> None:
    """GUID: FSMGV-005."""
    state = make_context(MemoryStorage(), chat_id=1, user_id=1)
    await state.set_data({"present": "value"})

    with pytest.raises(KeyError, match="missing"):
        await state.get_value("missing")


async def test_FSMGV_006_supported_mapping_keys_preserve_get_data_lookup_semantics() -> None:
    """GUID: FSMGV-006."""
    state = make_context(MemoryStorage(), chat_id=1, user_id=1)
    keys = ("1", "01", "Key", "key")
    values = ("one", "zero-one", "upper", "lower")
    await state.set_data(dict(zip(keys, values)))
    data = await state.get_data()

    for key in keys:
        assert await state.get_value(key) == data[key]


async def test_FSMGV_007_existing_keys_return_all_stored_falsy_values() -> None:
    """GUID: FSMGV-007."""
    falsy_values = (None, False, 0, "", [], (), set(), {})
    state = make_context(MemoryStorage(), chat_id=1, user_id=1)
    await state.set_data({str(index): value for index, value in enumerate(falsy_values)})

    for index, expected in enumerate(falsy_values):
        assert await state.get_value(str(index)) == expected


async def test_FSMGV_008_introducing_get_value_leaves_get_data_result_unchanged() -> None:
    """GUID: FSMGV-008."""
    state = make_context(MemoryStorage(), chat_id=1, user_id=1)
    expected = {"requested": "value", "other": [1, 2, 3]}
    await state.set_data(expected)
    before = await state.get_data()

    assert await state.get_value("requested") == "value"
    assert await state.get_data() == before == expected
