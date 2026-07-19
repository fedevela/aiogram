import inspect
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import SceneWizard, ScenesManager
from aiogram.fsm.storage.base import BaseStorage, DefaultKeyBuilder, StateType, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.redis import RedisStorage


VERIFICATION_MAP_PATH = Path(__file__).with_name("fsmvalue_compatibility_verification_map.json")
VERIFICATION_ARTIFACT_PATH = "tests/test_fsm/test_fsmvalue_compatibility_contract.py"
CANONICAL_REQUIREMENT_IDS = {"FSMVALUE-013", "FSMVALUE-014"}
PROJECT_ROOT = Path(__file__).parents[2]


class PreGetValueStorage(BaseStorage):
    """A custom storage implementing only the abstract operations predating get_value."""

    def __init__(self) -> None:
        self.states: Dict[StorageKey, Optional[str]] = {}
        self.data: Dict[StorageKey, Dict[str, Any]] = {}
        self.closed = False

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        self.states[key] = state.state if hasattr(state, "state") else state

    async def get_state(self, key: StorageKey) -> Optional[str]:
        return self.states.get(key)

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        self.data[key] = data.copy()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        return self.data.get(key, {}).copy()

    async def close(self) -> None:
        self.closed = True


class InMemoryRedis:
    def __init__(self) -> None:
        self.values: Dict[str, Any] = {}
        self.closed = False

    async def set(self, key: str, value: Any, **kwargs: Any) -> None:
        self.values[key] = value

    async def get(self, key: str) -> Any:
        return self.values.get(key)

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def aclose(self, **kwargs: Any) -> None:
        self.closed = True


class InMemoryMongoCollection:
    def __init__(self) -> None:
        self.documents: Dict[str, Dict[str, Any]] = {}

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        document = self.documents.get(query["_id"])
        return deepcopy(document) if document is not None else None

    async def update_one(
        self, filter: Dict[str, Any], update: Dict[str, Any], **kwargs: Any
    ) -> None:
        document = self.documents.setdefault(filter["_id"], {"_id": filter["_id"]})
        document.update(deepcopy(update["$set"]))

    async def find_one_and_update(
        self, filter: Dict[str, Any], update: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        document = self.documents.setdefault(filter["_id"], {"_id": filter["_id"]})
        for path, value in update.get("$set", {}).items():
            if path.startswith("data."):
                document.setdefault("data", {})[path.removeprefix("data.")] = deepcopy(value)
            else:
                document[path] = deepcopy(value)
        for field in update.get("$unset", {}):
            document.pop(field, None)
        return {key: deepcopy(value) for key, value in document.items() if key != "_id"}

    async def delete_one(self, filter: Dict[str, Any]) -> None:
        self.documents.pop(filter["_id"], None)


def make_key(**changes: Any) -> StorageKey:
    values = {"bot_id": 1, "chat_id": 2, "user_id": 3}
    values.update(changes)
    return StorageKey(**values)


def make_mongo_storage() -> MongoStorage:
    storage = MongoStorage.__new__(MongoStorage)
    storage._client = MagicMock()
    storage._collection = InMemoryMongoCollection()
    storage._key_builder = DefaultKeyBuilder(with_bot_id=True)
    return storage


def make_wizard(state: FSMContext) -> SceneWizard:
    return SceneWizard(
        scene_config=AsyncMock(),
        manager=AsyncMock(spec=ScenesManager),
        state=state,
        update_type="message",
        event=AsyncMock(),
        data={},
    )


def test_fsmvalue_compatibility_requirement_map_is_bidirectional_and_complete():
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


async def test_fsmvalue_013_memory_redis_and_mongo_established_storage_operations_preserve_inputs_results_isolation_and_mutations():  # noqa: E501
    """FSMVALUE-013: existing backend operation contracts remain unchanged."""
    redis_client = InMemoryRedis()
    storages = [
        MemoryStorage(),
        RedisStorage(redis=redis_client),
        make_mongo_storage(),
    ]

    for storage in storages:
        key = make_key()
        isolated_key = make_key(user_id=4)
        assert await storage.get_state(key) is None
        assert await storage.get_data(key) == {}

        await storage.set_state(key, "active")
        await storage.set_data(key, {"count": 1})
        assert await storage.get_state(key) == "active"
        assert await storage.get_data(key) == {"count": 1}
        assert await storage.get_state(isolated_key) is None
        assert await storage.get_data(isolated_key) == {}
        assert await storage.update_data(key, {"name": "Ada"}) == {
            "count": 1,
            "name": "Ada",
        }
        assert await storage.get_data(key) == {"count": 1, "name": "Ada"}

        await storage.set_state(key, None)
        await storage.set_data(key, {})
        assert await storage.get_state(key) is None
        assert await storage.get_data(key) == {}
        await storage.close()

    assert redis_client.closed
    assert storages[2]._client.close.called


async def test_fsmvalue_013_fsm_context_established_state_and_data_workflows_preserve_results_and_mutations():  # noqa: E501
    """FSMVALUE-013: adding the accessor does not alter established FSMContext workflows."""
    storage = MemoryStorage()
    context = FSMContext(storage=storage, key=make_key())
    isolated = FSMContext(storage=storage, key=make_key(chat_id=9))

    await context.set_state("active")
    await context.set_data({"one": 1})
    assert await context.get_state() == "active"
    assert await context.get_data() == {"one": 1}
    assert await context.update_data({"two": 2}, three=3) == {"one": 1, "three": 3, "two": 2}
    assert await isolated.get_state() is None
    assert await isolated.get_data() == {}

    await context.clear()
    assert await context.get_state() is None
    assert await context.get_data() == {}


async def test_fsmvalue_013_scene_wizard_established_state_and_data_workflows_preserve_results_and_mutations():  # noqa: E501
    """FSMVALUE-013: adding the accessor does not alter established SceneWizard workflows."""
    context = FSMContext(storage=MemoryStorage(), key=make_key())
    wizard = make_wizard(context)
    await context.set_state("scene")

    await wizard.set_data({"one": 1})
    assert await wizard.get_data() == {"one": 1}
    assert await wizard.update_data({"two": 2}, three=3) == {
        "one": 1,
        "three": 3,
        "two": 2,
    }
    assert await context.get_state() == "scene"
    await wizard.clear_data()
    assert await wizard.get_data() == {}
    assert await context.get_state() == "scene"


async def test_fsmvalue_013_custom_storage_with_only_preexisting_abstract_operations_remains_concrete_and_inherits_default_get_value():  # noqa: E501
    """FSMVALUE-013: get_value remains a default, non-abstract storage operation."""
    assert "get_value" not in PreGetValueStorage.__dict__
    assert "get_value" not in BaseStorage.__abstractmethods__
    assert not inspect.isabstract(PreGetValueStorage)

    storage = PreGetValueStorage()
    key = make_key()
    fallback = object()
    await storage.set_data(key, {"present": None})
    assert await storage.get_value(key, "present", fallback) is None
    assert await storage.get_value(key, "missing", fallback) is fallback


async def assert_supported_python_public_api_contract(version: str) -> None:
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text()
    workflow = (PROJECT_ROOT / ".github/workflows/tests.yml").read_text()
    assert f"Programming Language :: Python :: {version}" in pyproject
    assert f"- '{version}'" in workflow
    assert inspect.iscoroutinefunction(BaseStorage.get_value)
    assert inspect.iscoroutinefunction(FSMContext.get_value)
    assert inspect.iscoroutinefunction(SceneWizard.get_value)

    storage = PreGetValueStorage()
    context = FSMContext(storage=storage, key=make_key())
    wizard = make_wizard(context)
    await context.set_data({"answer": 42})
    storage_operation = storage.get_value(context.key, "answer")
    context_operation = context.get_value("answer")
    wizard_operation = wizard.get_value("answer")
    assert inspect.isawaitable(storage_operation)
    assert inspect.isawaitable(context_operation)
    assert inspect.isawaitable(wizard_operation)
    assert await storage_operation == 42
    assert await context_operation == 42
    assert await wizard_operation == 42


async def test_fsmvalue_014_cpython_3_9_public_fsm_apis_import_and_get_value_coroutines_await_successfully():  # noqa: E501
    """FSMVALUE-014: public get_value APIs remain compatible with CPython 3.9."""
    await assert_supported_python_public_api_contract("3.9")


async def test_fsmvalue_014_cpython_3_10_public_fsm_apis_import_and_get_value_coroutines_await_successfully():  # noqa: E501
    """FSMVALUE-014: public get_value APIs remain compatible with CPython 3.10."""
    await assert_supported_python_public_api_contract("3.10")


async def test_fsmvalue_014_cpython_3_11_public_fsm_apis_import_and_get_value_coroutines_await_successfully():  # noqa: E501
    """FSMVALUE-014: public get_value APIs remain compatible with CPython 3.11."""
    await assert_supported_python_public_api_contract("3.11")


async def test_fsmvalue_014_cpython_3_12_public_fsm_apis_import_and_get_value_coroutines_await_successfully():  # noqa: E501
    """FSMVALUE-014: public get_value APIs remain compatible with CPython 3.12."""
    await assert_supported_python_public_api_contract("3.12")


async def test_fsmvalue_014_cpython_3_13_public_fsm_apis_import_and_get_value_coroutines_await_successfully():  # noqa: E501
    """FSMVALUE-014: public get_value APIs remain compatible with CPython 3.13."""
    await assert_supported_python_public_api_contract("3.13")
