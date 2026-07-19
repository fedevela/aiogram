import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import SceneWizard, ScenesManager
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

VERIFICATION_MAP_PATH = Path(__file__).with_name("scene_get_value_verification_map.json")
VERIFICATION_ARTIFACT_PATH = "tests/test_fsm/test_scene_get_value_contract.py"
CANONICAL_REQUIREMENT_IDS = {
    "FSMVALUE-008",
    "FSMVALUE-009",
    "FSMVALUE-010",
    "FSMVALUE-012",
}


def make_storage_key() -> StorageKey:
    return StorageKey(bot_id=1, chat_id=2, user_id=3)


def make_wizard(state: FSMContext) -> SceneWizard:
    return SceneWizard(
        scene_config=AsyncMock(),
        manager=AsyncMock(spec=ScenesManager),
        state=state,
        update_type="message",
        event=AsyncMock(),
        data={},
    )


def test_scene_get_value_requirement_map_is_bidirectional_and_complete():
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


async def test_fsmvalue_008_scene_wizard_delegates_data_key_with_omitted_none_default_and_returns_context_result():  # noqa: E501
    """FSMVALUE-008: wizard lookup awaits context with the exact key and omitted None."""
    state = AsyncMock(spec=FSMContext)
    context_result = object()
    state.get_value.return_value = context_result
    wizard = make_wizard(state)

    assert await wizard.get_value("name") is context_result
    state.get_value.assert_awaited_once_with(data_key="name", default=None)


async def test_fsmvalue_008_scene_wizard_delegates_exact_data_key_and_supplied_default_and_returns_context_result_unchanged():  # noqa: E501
    """FSMVALUE-008: wizard lookup forwards the exact key and default and preserves the result."""
    state = AsyncMock(spec=FSMContext)
    default = object()
    context_result = object()
    state.get_value.return_value = context_result
    wizard = make_wizard(state)

    assert await wizard.get_value("absent", default) is context_result
    state.get_value.assert_awaited_once_with(data_key="absent", default=default)
    assert state.get_value.await_args.kwargs["default"] is default


async def test_fsmvalue_009_scene_wizard_get_value_once_or_repeatedly_for_present_or_absent_keys_preserves_fsm_state():  # noqa: E501
    """FSMVALUE-009: all scene-level individual-value reads preserve established state."""
    state = FSMContext(storage=MemoryStorage(), key=make_storage_key())
    wizard = make_wizard(state)
    await state.set_state("established")
    await state.set_data({"present": "value"})

    assert await wizard.get_value("present") == "value"
    for _ in range(3):
        assert await wizard.get_value("absent") is None
        assert await wizard.get_value("absent", "fallback") == "fallback"

    assert await state.get_state() == "established"


async def test_fsmvalue_010_scene_wizard_get_value_once_or_repeatedly_for_present_or_absent_keys_preserves_complete_data():  # noqa: E501
    """FSMVALUE-010: all scene-level individual-value reads preserve the complete data snapshot."""
    state = FSMContext(storage=MemoryStorage(), key=make_storage_key())
    wizard = make_wizard(state)
    snapshot = {"present": [1, 2], "none": None, "nested": {"key": "value"}}
    await state.set_data(snapshot)

    for _ in range(3):
        assert await wizard.get_value("present") == [1, 2]
        assert await wizard.get_value("none", "fallback") is None
        assert await wizard.get_value("absent") is None
        assert await wizard.get_value("absent", "fallback") == "fallback"

    assert await state.get_data() == snapshot


async def test_fsmvalue_012_scene_wizard_get_value_propagates_storage_read_exception_to_scene_caller():  # noqa: E501
    """FSMVALUE-012: a storage read exception remains observable at the scene boundary."""
    failure = RuntimeError("storage read failed")
    storage = AsyncMock(spec=BaseStorage)
    storage.get_value.side_effect = failure
    wizard = make_wizard(FSMContext(storage=storage, key=make_storage_key()))

    with pytest.raises(RuntimeError) as raised:
        await wizard.get_value("name", "fallback")

    assert raised.value is failure
    storage.get_value.assert_awaited_once()


async def test_fsmvalue_012_scene_wizard_get_value_propagates_storage_read_cancellation_to_scene_caller():  # noqa: E501
    """FSMVALUE-012: storage read cancellation remains observable at the scene boundary."""
    cancellation = asyncio.CancelledError()
    storage = AsyncMock(spec=BaseStorage)
    storage.get_value.side_effect = cancellation
    wizard = make_wizard(FSMContext(storage=storage, key=make_storage_key()))

    with pytest.raises(asyncio.CancelledError) as raised:
        await wizard.get_value("name", "fallback")

    assert raised.value is cancellation
    storage.get_value.assert_awaited_once()
