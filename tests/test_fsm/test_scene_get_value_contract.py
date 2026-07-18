from unittest.mock import AsyncMock

import pytest

from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import SceneWizard, ScenesManager
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage


def make_wizard(state: FSMContext) -> SceneWizard:
    return SceneWizard(
        scene_config=AsyncMock(),
        manager=AsyncMock(spec=ScenesManager),
        state=state,
        update_type="message",
        event=AsyncMock(),
        data={},
    )


def make_context() -> FSMContext:
    return FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=42, chat_id=-42, user_id=42),
    )


class TestSceneWizardGetValueContract:
    async def test_fsmval_007_existing_key_delegates_to_fsm_context_and_returns_exact_value(
        self,
    ):
        """GUID: FSMVAL-007 -- an existing key returns the delegated exact value."""
        state = make_context()
        value = object()
        await state.set_data({"key": value})
        state.get_value = AsyncMock(wraps=state.get_value)
        wizard = make_wizard(state)

        result = await wizard.get_value("key")

        assert result is value
        state.get_value.assert_awaited_once_with("key")

    async def test_fsmval_007_missing_key_preserves_delegated_key_error(self):
        """GUID: FSMVAL-007 -- a missing key exposes the FSMContext KeyError."""
        state = make_context()
        state.get_value = AsyncMock(wraps=state.get_value)
        wizard = make_wizard(state)

        with pytest.raises(KeyError, match="missing"):
            await wizard.get_value("missing")

        state.get_value.assert_awaited_once_with("missing")

    async def test_fsmval_007_existing_key_retrieval_preserves_complete_state_and_data(
        self,
    ):
        """GUID: FSMVAL-007 -- delegated retrieval leaves state and data unchanged."""
        state = make_context()
        stored_data = {"key": "value", "other": {"nested": True}}
        await state.set_state("Scene:active")
        await state.set_data(stored_data)
        wizard = make_wizard(state)
        state_before = await state.get_state()
        data_before = await state.get_data()

        assert await wizard.get_value("key") == "value"

        assert await state.get_state() == state_before
        assert await state.get_data() == data_before
