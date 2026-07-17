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

    async def test_fsm_003_get_value_returns_value_exposed_by_get_data_for_same_key(self, state):
        """GUID: FSM-003."""
        data = await state.get_data()

        assert await state.get_value("foo") == data["foo"]

    async def test_fsm_004_stored_data_remains_unchanged_after_get_value_call(self, state):
        """GUID: FSM-004."""
        data_before = await state.get_data()

        await state.get_value("foo")

        assert await state.get_data() == data_before

    async def test_fsm_005_established_fsm_state_remains_unchanged_after_get_value_call(
        self, state
    ):
        """GUID: FSM-005."""
        state_before = await state.get_state()
        assert state_before == "test"

        await state.get_value("foo")

        assert await state.get_state() == state_before

    async def test_fsm_006_get_value_raises_key_error_when_requested_key_is_absent(self, state):
        """GUID: FSM-006."""
        with pytest.raises(KeyError):
            await state.get_value("missing")

    async def test_fsm_007_get_value_uses_mapping_supported_key_without_coercion(self, state):
        """GUID: FSM-007."""
        await state.set_data({1: "integer key", "1": "string key"})

        assert await state.get_value(1) == "integer key"

    async def test_fsm_008_get_value_returns_falsy_or_object_value_without_transformation(
        self, state
    ):
        """GUID: FSM-008."""
        stored_object = object()
        await state.set_data({"falsy": 0, "object": stored_object})

        assert await state.get_value("falsy") == 0
        assert await state.get_value("object") is stored_object

    async def test_fsm_009_get_data_exposes_same_stored_data_after_get_value_is_added_and_called(
        self, state
    ):
        """GUID: FSM-009."""
        data_before = await state.get_data()

        await state.get_value("foo")

        assert data_before == {"foo": "bar"}
        assert await state.get_data() == data_before

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
