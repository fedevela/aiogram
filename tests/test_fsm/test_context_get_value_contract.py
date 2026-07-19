import asyncio
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage


VERIFICATION_MAP_PATH = Path(__file__).with_name("fsmcontext_get_value_verification_map.json")
VERIFICATION_ARTIFACT_PATH = "tests/test_fsm/test_context_get_value_contract.py"
CANONICAL_REQUIREMENT_IDS = {
    "FSMVALUE-003",
    "FSMVALUE-007",
    "FSMVALUE-009",
    "FSMVALUE-010",
    "FSMVALUE-012",
}


def make_storage_key(**changes: Any) -> StorageKey:
    values = {
        "bot_id": 1,
        "chat_id": 2,
        "user_id": 3,
        "thread_id": 4,
        "business_connection_id": "business",
        "destiny": "destiny",
    }
    values.update(changes)
    return StorageKey(**values)


def test_fsmcontext_get_value_requirement_map_is_bidirectional_and_complete():
    verification_map = json.loads(VERIFICATION_MAP_PATH.read_text())
    requirements = verification_map["requirements"]
    artifacts = verification_map["artifacts"]

    assert set(requirements) == CANONICAL_REQUIREMENT_IDS
    expected_artifacts = {}
    for requirement_id, cases in requirements.items():
        for case in cases:
            assert case["path"] == VERIFICATION_ARTIFACT_PATH
            assert callable(globals().get(case["name"]))
            artifact_id = f"{case['path']}::{case['name']}"
            expected_artifacts.setdefault(artifact_id, []).append(requirement_id)

    assert artifacts == {
        artifact_id: sorted(requirement_ids)
        for artifact_id, requirement_ids in sorted(expected_artifacts.items())
    }


async def test_fsmvalue_003_context_delegates_complete_unchanged_key_name_and_omitted_none_default():
    """FSMVALUE-003: context lookup awaits storage with its exact key, name, and None."""
    storage = AsyncMock(spec=BaseStorage)
    storage.get_value.return_value = "Alice"
    key = make_storage_key()
    state = FSMContext(storage=storage, key=key)

    assert await state.get_value("name") == "Alice"
    storage.get_value.assert_awaited_once_with(key=key, dict_key="name", default=None)
    assert storage.get_value.await_args.kwargs["key"] is key


async def test_fsmvalue_003_context_delegates_supplied_default_and_returns_storage_result():
    """FSMVALUE-003: an absent-key lookup forwards its exact default and returns the result."""
    storage = AsyncMock(spec=BaseStorage)
    default = object()
    storage_result = object()
    storage.get_value.return_value = storage_result
    key = make_storage_key()
    state = FSMContext(storage=storage, key=key)

    assert await state.get_value("absent", default) is storage_result
    storage.get_value.assert_awaited_once_with(key=key, dict_key="absent", default=default)
    assert storage.get_value.await_args.kwargs["default"] is default


async def test_fsmvalue_007_context_lookup_is_isolated_by_every_storage_key_identity_dimension():
    """FSMVALUE-007: bot, chat, user, thread, business connection, and destiny isolate reads."""
    storage = MemoryStorage()
    keys = [
        make_storage_key(),
        make_storage_key(bot_id=10),
        make_storage_key(chat_id=20),
        make_storage_key(user_id=30),
        make_storage_key(thread_id=40),
        make_storage_key(business_connection_id="other-business"),
        make_storage_key(destiny="other-destiny"),
    ]
    contexts = [FSMContext(storage=storage, key=key) for key in keys]

    for index, context in enumerate(contexts):
        await context.set_data({"value": index})

    assert [await context.get_value("value") for context in contexts] == list(range(len(contexts)))


async def test_fsmvalue_009_context_get_value_does_not_change_established_fsm_state():
    """FSMVALUE-009: context individual-value reads preserve the established FSM state."""
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=make_storage_key())
    await state.set_state("established")
    await state.set_data({"present": "value"})

    await state.get_value("present")
    await state.get_value("absent")

    assert await state.get_state() == "established"


async def test_fsmvalue_010_repeated_context_get_value_calls_do_not_change_complete_stored_data():
    """FSMVALUE-010: repeated present and absent context reads preserve all stored data."""
    storage = MemoryStorage()
    state = FSMContext(storage=storage, key=make_storage_key())
    snapshot = {"present": [1, 2], "none": None, "nested": {"key": "value"}}
    await state.set_data(snapshot)

    for _ in range(3):
        assert await state.get_value("present") == [1, 2]
        assert await state.get_value("absent") is None
        assert await state.get_value("absent", "fallback") == "fallback"

    assert await state.get_data() == snapshot


async def test_fsmvalue_012_context_get_value_propagates_storage_read_exception_to_caller():
    """FSMVALUE-012: a storage read exception remains observable to the context caller."""
    failure = RuntimeError("storage read failed")
    storage = AsyncMock(spec=BaseStorage)
    storage.get_value.side_effect = failure
    state = FSMContext(storage=storage, key=make_storage_key())

    with pytest.raises(RuntimeError) as raised:
        await state.get_value("name", "fallback")

    assert raised.value is failure


async def test_fsmvalue_012_context_get_value_propagates_storage_read_cancellation_to_caller():
    """FSMVALUE-012: storage read cancellation remains observable to the context caller."""
    cancellation = asyncio.CancelledError()
    storage = AsyncMock(spec=BaseStorage)
    storage.get_value.side_effect = cancellation
    state = FSMContext(storage=storage, key=make_storage_key())

    with pytest.raises(asyncio.CancelledError) as raised:
        await state.get_value("name", "fallback")

    assert raised.value is cancellation
