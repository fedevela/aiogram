import asyncio
import inspect
import json
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.redis import RedisStorage


VERIFICATION_MAP_PATH = Path(__file__).with_name("fsmvalue_verification_map.json")
CANONICAL_REQUIREMENT_IDS = {
    "FSMVALUE-001",
    "FSMVALUE-002",
    "FSMVALUE-004",
    "FSMVALUE-005",
    "FSMVALUE-006",
    "FSMVALUE-007",
    "FSMVALUE-009",
    "FSMVALUE-010",
    "FSMVALUE-011",
    "FSMVALUE-012",
}


class ContractStorage(BaseStorage):
    def __init__(self) -> None:
        self.data: Dict[StorageKey, Dict[str, Any]] = {}
        self.states: Dict[StorageKey, Optional[str]] = {}
        self.get_data_calls = []

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        self.states[key] = state.state if hasattr(state, "state") else state

    async def get_state(self, key: StorageKey) -> Optional[str]:
        return self.states.get(key)

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        self.data[key] = data.copy()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        self.get_data_calls.append(key)
        return self.data.get(key, {}).copy()

    async def close(self) -> None:
        pass


class OverridingStorage(ContractStorage):
    def __init__(self) -> None:
        super().__init__()
        self.override_calls = []

    async def get_value(
        self, key: StorageKey, dict_key: str, default: Optional[Any] = None
    ) -> Optional[Any]:
        self.override_calls.append((key, dict_key, default))
        return "overridden"


class FailingStorage(ContractStorage):
    def __init__(self, failure: BaseException) -> None:
        super().__init__()
        self.failure = failure

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        raise self.failure


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


def test_fsmvalue_requirement_map_is_bidirectional_and_complete():
    verification_map = json.loads(VERIFICATION_MAP_PATH.read_text())
    requirements = verification_map["requirements"]
    artifacts = verification_map["artifacts"]

    assert set(requirements) == CANONICAL_REQUIREMENT_IDS
    expected_artifacts = {}
    for requirement_id, cases in requirements.items():
        for case in cases:
            artifact_id = f"{case['path']}::{case['name']}"
            expected_artifacts.setdefault(artifact_id, []).append(requirement_id)

    assert artifacts == {
        artifact_id: sorted(requirement_ids)
        for artifact_id, requirement_ids in sorted(expected_artifacts.items())
    }


async def test_fsmvalue_001_get_value_accepts_storage_key_string_key_and_optional_none_default():
    """FSMVALUE-001: the asynchronous accessor exposes the canonical call contract."""
    signature = inspect.signature(BaseStorage.get_value)
    parameters = list(signature.parameters.values())

    assert inspect.iscoroutinefunction(BaseStorage.get_value)
    assert [parameter.name for parameter in parameters] == [
        "self",
        "key",
        "dict_key",
        "default",
    ]
    assert parameters[1].annotation is StorageKey
    assert parameters[2].annotation is str
    assert parameters[3].default is None

    storage = ContractStorage()
    key = make_storage_key()
    await storage.set_data(key, {"answer": 42})
    assert await storage.get_value(key, "answer") == 42
    assert await storage.get_value(key, "missing") is None


async def test_fsmvalue_002_default_get_value_awaits_get_data_with_the_unchanged_storage_key():
    """FSMVALUE-002: the default accessor delegates using the complete original key."""
    storage = ContractStorage()
    key = make_storage_key()
    await storage.set_data(key, {"answer": 42})

    assert await storage.get_value(key, "answer") == 42
    assert storage.get_data_calls == [key]
    assert storage.get_data_calls[0] is key


async def test_fsmvalue_002_storage_subclass_override_is_used_when_get_value_is_awaited():
    """FSMVALUE-002: a backend may override the default accessor implementation."""
    storage = OverridingStorage()
    key = make_storage_key()

    assert await storage.get_value(key, "answer", "fallback") == "overridden"
    assert storage.override_calls == [(key, "answer", "fallback")]
    assert storage.get_data_calls == []


async def test_fsmvalue_004_each_exact_string_key_returns_its_untransformed_supported_value():
    """FSMVALUE-004: exact-key lookup preserves every backend-supported value type."""
    storage = ContractStorage()
    key = make_storage_key()
    marker = object()
    values = {
        "zero": 0,
        "false": False,
        "empty": "",
        "none": None,
        "list": [1, 2],
        "mapping": {"nested": "value"},
        "object": marker,
    }
    await storage.set_data(key, values)

    for dict_key, expected in values.items():
        assert await storage.get_value(key, dict_key, "fallback") is expected


async def test_fsmvalue_005_absent_key_returns_none_or_the_caller_supplied_default():
    """FSMVALUE-005: missing lookup distinguishes omitted and supplied defaults."""
    storage = ContractStorage()
    key = make_storage_key()
    fallback = object()

    assert await storage.get_value(key, "missing") is None
    assert await storage.get_value(key, "missing", fallback) is fallback


async def test_fsmvalue_006_present_falsy_or_none_value_wins_over_the_supplied_default():
    """FSMVALUE-006: key presence, rather than value truthiness, controls fallback."""
    storage = ContractStorage()
    key = make_storage_key()
    values = {"zero": 0, "false": False, "empty": "", "none": None}
    await storage.set_data(key, values)

    for dict_key, expected in values.items():
        assert await storage.get_value(key, dict_key, "fallback") is expected


async def test_fsmvalue_007_lookup_is_isolated_by_every_storage_key_identity_dimension():
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

    for index, key in enumerate(keys):
        await storage.set_data(key, {"value": index})

    assert [await storage.get_value(key, "value") for key in keys] == list(range(len(keys)))


async def test_fsmvalue_009_present_and_absent_get_value_reads_do_not_change_fsm_state():
    """FSMVALUE-009: individual-value reads leave FSM state unchanged."""
    storage = MemoryStorage()
    key = make_storage_key()
    await storage.set_state(key, "state")
    await storage.set_data(key, {"present": "value"})

    await storage.get_value(key, "present")
    await storage.get_value(key, "missing")

    assert await storage.get_state(key) == "state"


async def test_fsmvalue_010_repeated_present_and_absent_get_value_reads_do_not_change_data():
    """FSMVALUE-010: single and repeated reads leave the complete data snapshot unchanged."""
    storage = MemoryStorage()
    key = make_storage_key()
    snapshot = {"present": [1, 2], "none": None}
    await storage.set_data(key, snapshot)

    for _ in range(3):
        await storage.get_value(key, "present")
        await storage.get_value(key, "missing", "fallback")

    assert await storage.get_data(key) == snapshot


async def test_fsmvalue_011_memory_redis_mongo_and_custom_backends_share_accessor_results():
    """FSMVALUE-011: all supported and contract-conforming backends share lookup semantics."""
    key = make_storage_key(destiny="default")
    data = {"value": 42, "zero": 0, "false": False, "empty": "", "none": None}

    memory_storage = MemoryStorage()
    await memory_storage.set_data(key, data)

    redis_client = AsyncMock()
    redis_client.get.return_value = json.dumps(data)
    redis_storage = RedisStorage(redis=redis_client)

    collection = MagicMock()
    collection.find_one = AsyncMock(return_value={"data": data.copy()})
    mongo_storage = MongoStorage.__new__(MongoStorage)
    mongo_storage._collection = collection
    mongo_storage._key_builder = redis_storage.key_builder

    custom_storage = ContractStorage()
    await custom_storage.set_data(key, data)

    for storage in (memory_storage, redis_storage, mongo_storage, custom_storage):
        assert await storage.get_value(key, "value") == 42
        assert await storage.get_value(key, "missing") is None
        assert await storage.get_value(key, "missing", "fallback") == "fallback"
        assert await storage.get_value(key, "zero", "fallback") == 0
        assert await storage.get_value(key, "false", "fallback") is False
        assert await storage.get_value(key, "empty", "fallback") == ""
        assert await storage.get_value(key, "none", "fallback") is None


async def test_fsmvalue_012_backend_read_exception_remains_observable_without_fallback():
    """FSMVALUE-012: backend exceptions propagate instead of becoming successful lookups."""
    failure = RuntimeError("backend read failed")
    storage = FailingStorage(failure)

    with pytest.raises(RuntimeError) as raised:
        await storage.get_value(make_storage_key(), "missing", "fallback")

    assert raised.value is failure


async def test_fsmvalue_012_read_cancellation_remains_observable_without_fallback():
    """FSMVALUE-012: cancellation propagates instead of becoming a successful lookup."""
    cancellation = asyncio.CancelledError()
    storage = FailingStorage(cancellation)

    with pytest.raises(asyncio.CancelledError) as raised:
        await storage.get_value(make_storage_key(), "missing", "fallback")

    assert raised.value is cancellation
