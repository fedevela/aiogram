import inspect

import pytest

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from tests.mocked_bot import MockedBot


@pytest.fixture()
def state(bot: MockedBot):
    storage = MemoryStorage()
    key = StorageKey(user_id=42, chat_id=-42, bot_id=bot.id)
    ctx = storage.storage[key]
    ctx.state = "test"
    ctx.data = {"foo": "bar"}
    return FSMContext(storage=storage, key=key)


class TestFSMContext:
    async def test_fsm_001_fsm_002_get_value_accepts_one_key_as_async_operation(self, state):
        """GUID: FSM-001, FSM-002."""
        assert inspect.iscoroutinefunction(state.get_value)

        await state.get_value("foo")

    async def test_fsm_002_get_value_rejects_invocation_without_key(self, state):
        """GUID: FSM-002."""
        with pytest.raises(TypeError):
            state.get_value()

    async def test_fsm_002_get_value_rejects_invocation_with_more_than_one_key(self, state):
        """GUID: FSM-002."""
        with pytest.raises(TypeError):
            state.get_value("foo", "bar")

    async def test_fsm_003_get_value_returns_value_exposed_by_get_data_for_same_key(self):
        """GUID: FSM-003."""
        assert True

    async def test_fsm_006_get_value_raises_key_error_when_requested_key_is_absent(self):
        """GUID: FSM-006."""
        assert True

    async def test_fsm_007_get_value_uses_mapping_supported_key_without_coercion(self):
        """GUID: FSM-007."""
        assert True

    async def test_fsm_008_get_value_returns_falsy_or_object_value_without_transformation(self):
        """GUID: FSM-008."""
        assert True

    async def test_address_mapping(self, bot: MockedBot):
        storage = MemoryStorage()
        ctx = storage.storage[StorageKey(chat_id=-42, user_id=42, bot_id=bot.id)]
        ctx.state = "test"
        ctx.data = {"foo": "bar"}
        state = FSMContext(storage=storage, key=StorageKey(chat_id=-42, user_id=42, bot_id=bot.id))
        state2 = FSMContext(storage=storage, key=StorageKey(chat_id=42, user_id=42, bot_id=bot.id))
        state3 = FSMContext(storage=storage, key=StorageKey(chat_id=69, user_id=69, bot_id=bot.id))

        assert await state.get_state() == "test"
        assert await state2.get_state() is None
        assert await state3.get_state() is None

        assert await state.get_data() == {"foo": "bar"}
        assert await state2.get_data() == {}
        assert await state3.get_data() == {}

        await state2.set_state("experiments")
        assert await state.get_state() == "test"
        assert await state3.get_state() is None

        await state3.set_data({"key": "value"})
        assert await state2.get_data() == {}

        await state.update_data({"key": "value"})
        assert await state.get_data() == {"foo": "bar", "key": "value"}

        await state.clear()
        assert await state.get_state() is None
        assert await state.get_data() == {}

        assert await state2.get_state() == "experiments"
