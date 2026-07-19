########
Storages
########

Storages out of the box
=======================

MemoryStorage
-------------

.. autoclass:: aiogram.fsm.storage.memory.MemoryStorage
    :members: __init__
    :member-order: bysource

RedisStorage
------------

.. autoclass:: aiogram.fsm.storage.redis.RedisStorage
    :members: __init__, from_url
    :member-order: bysource

MongoStorage
------------

.. autoclass:: aiogram.fsm.storage.mongo.MongoStorage
    :members: __init__, from_url
    :member-order: bysource

KeyBuilder
------------

Keys inside Redis and Mongo storages can be customized via key builders:

.. autoclass:: aiogram.fsm.storage.base.KeyBuilder
    :members:
    :member-order: bysource

.. autoclass:: aiogram.fsm.storage.base.DefaultKeyBuilder
    :members:
    :member-order: bysource


Writing own storages
====================

.. autoclass:: aiogram.fsm.storage.base.BaseStorage
    :members:
    :member-order: bysource


Single-value lookup procedural contract
=======================================

The following implementation-independent procedures define the ``BaseStorage.get_value``
contract.  They are durable design logic for the accessor; they do not describe additional
runtime behavior beyond the linked requirements and verification obligations.

Requirement-to-verification traceability
----------------------------------------

``BaseStorage.get_value`` maps to these obligations:

* ``FSMVALUE-001`` —
  ``test_fsmvalue_001_get_value_accepts_storage_key_string_key_and_optional_none_default``
* ``FSMVALUE-002`` —
  ``test_fsmvalue_002_default_get_value_awaits_get_data_with_the_unchanged_storage_key`` and
  ``test_fsmvalue_002_storage_subclass_override_is_used_when_get_value_is_awaited``
* ``FSMVALUE-004`` —
  ``test_fsmvalue_004_each_exact_string_key_returns_its_untransformed_supported_value``
* ``FSMVALUE-005`` —
  ``test_fsmvalue_005_absent_key_returns_none_or_the_caller_supplied_default``
* ``FSMVALUE-006`` —
  ``test_fsmvalue_006_present_falsy_or_none_value_wins_over_the_supplied_default``
* ``FSMVALUE-007`` —
  ``test_fsmvalue_007_lookup_is_isolated_by_every_storage_key_identity_dimension``
* ``FSMVALUE-009`` —
  ``test_fsmvalue_009_present_and_absent_get_value_reads_do_not_change_fsm_state``
* ``FSMVALUE-010`` —
  ``test_fsmvalue_010_repeated_present_and_absent_get_value_reads_do_not_change_data``
* ``FSMVALUE-011`` —
  ``test_fsmvalue_011_memory_redis_mongo_and_custom_backends_share_accessor_results``
* ``FSMVALUE-012`` —
  ``test_fsmvalue_012_backend_read_exception_remains_observable_without_fallback`` and
  ``test_fsmvalue_012_read_cancellation_remains_observable_without_fallback``

Accessor dispatch
-----------------

.. code-block:: text

    PROCEDURE DISPATCH_GET_VALUE(storage, storage_key, data_key, default = None)
      REQUIREMENT_IDS: FSMVALUE-001, FSMVALUE-002, FSMVALUE-011
      VERIFICATION:
        test_fsmvalue_001_get_value_accepts_storage_key_string_key_and_optional_none_default
        test_fsmvalue_002_storage_subclass_override_is_used_when_get_value_is_awaited
        test_fsmvalue_011_memory_redis_mongo_and_custom_backends_share_accessor_results

      PRECONDITIONS
        storage implements BaseStorage
        storage_key is one complete StorageKey value
        data_key is the exact caller-supplied string
        default is the caller-supplied value, or None when omitted

      DECIDE
        IF storage's concrete class overrides get_value
          DELEGATE the complete call (storage_key, data_key, default) to that override
          AWAIT and RETURN the override's result
        ELSE
          DELEGATE the complete call to BASE_STORAGE_GET_VALUE
          AWAIT and RETURN the default implementation's result
        END IF

      ON FAILURE any exception or asynchronous cancellation
        PROPAGATE the same failure to the caller
    END PROCEDURE

Default accessor
----------------

.. code-block:: text

    PROCEDURE BASE_STORAGE_GET_VALUE(storage, storage_key, data_key, default = None)
      REQUIREMENT_IDS: FSMVALUE-001, FSMVALUE-002, FSMVALUE-004, FSMVALUE-005,
        FSMVALUE-006, FSMVALUE-007, FSMVALUE-009, FSMVALUE-010, FSMVALUE-011,
        FSMVALUE-012
      VERIFICATION:
        test_fsmvalue_001_get_value_accepts_storage_key_string_key_and_optional_none_default
        test_fsmvalue_002_default_get_value_awaits_get_data_with_the_unchanged_storage_key
        test_fsmvalue_004_each_exact_string_key_returns_its_untransformed_supported_value
        test_fsmvalue_005_absent_key_returns_none_or_the_caller_supplied_default
        test_fsmvalue_006_present_falsy_or_none_value_wins_over_the_supplied_default
        test_fsmvalue_007_lookup_is_isolated_by_every_storage_key_identity_dimension
        test_fsmvalue_009_present_and_absent_get_value_reads_do_not_change_fsm_state
        test_fsmvalue_010_repeated_present_and_absent_get_value_reads_do_not_change_data
        test_fsmvalue_011_memory_redis_mongo_and_custom_backends_share_accessor_results
        test_fsmvalue_012_backend_read_exception_remains_observable_without_fallback
        test_fsmvalue_012_read_cancellation_remains_observable_without_fallback

      PRECONDITIONS
        storage_key retains bot_id, chat_id, user_id, thread_id,
          business_connection_id, and destiny unchanged
        data_key is not normalized, transformed, or used as a truth-value condition

      LOAD / RECEIVE
        AWAIT storage.get_data(key = storage_key) exactly once
        RECEIVE data as the backend-supported mapping for that complete identity

      DECIDE
        IF data contains the exact string key data_key
          result := the value associated with data_key
          // Presence wins even when result is 0, False, empty string, or None.
        ELSE
          result := default
        END IF

      STATE / MUTATION INVARIANTS
        DO NOT call get_state, set_state, set_data, or update_data
        DO NOT mutate data or any value contained in data
        DO NOT acquire a write transaction or emit a storage event
        Repeated invocation performs the same independent read and preserves stored state and data

      RETURN result without copying, coercing, decoding, or substituting it

      ON FAILURE from get_data, including backend exception or cancellation
        DO NOT inspect data_key
        DO NOT return default
        DO NOT retry, compensate, translate, or suppress the failure
        PROPAGATE the same failure to the caller
    END PROCEDURE

Backend data delegation
-----------------------

.. code-block:: text

    PROCEDURE GET_DATA_FOR_SINGLE_VALUE(storage, storage_key)
      REQUIREMENT_IDS: FSMVALUE-002, FSMVALUE-007, FSMVALUE-009, FSMVALUE-010,
        FSMVALUE-011, FSMVALUE-012
      VERIFICATION:
        test_fsmvalue_002_default_get_value_awaits_get_data_with_the_unchanged_storage_key
        test_fsmvalue_007_lookup_is_isolated_by_every_storage_key_identity_dimension
        test_fsmvalue_009_present_and_absent_get_value_reads_do_not_change_fsm_state
        test_fsmvalue_010_repeated_present_and_absent_get_value_reads_do_not_change_data
        test_fsmvalue_011_memory_redis_mongo_and_custom_backends_share_accessor_results
        test_fsmvalue_012_backend_read_exception_remains_observable_without_fallback
        test_fsmvalue_012_read_cancellation_remains_observable_without_fallback

      DELEGATE
        IF storage is MemoryStorage
          LOOK UP the record by the complete immutable StorageKey
          RETURN a shallow copy of that record's data mapping
        ELSE IF storage is RedisStorage
          BUILD the data record key from the unchanged StorageKey using the configured KeyBuilder
          AWAIT the Redis read; RETURN an empty mapping when absent
          OTHERWISE decode and deserialize the stored data mapping
        ELSE IF storage is MongoStorage
          BUILD the document identity from the unchanged StorageKey using the configured KeyBuilder
          AWAIT the Mongo read; RETURN an empty mapping when the document or data is absent
          OTHERWISE return the document's data mapping
        ELSE
          AWAIT the custom storage's contract-conforming get_data(storage_key)
          RETURN its backend-supported data mapping
        END IF

      IDENTITY INVARIANT
        KeyBuilder configuration MUST preserve each applicable StorageKey dimension
        No branch may substitute, reconstruct, or drop a StorageKey field during delegation

      CONCURRENCY / REPEATED READS
        Each invocation is one asynchronous read with no accessor-level lock or retry
        Concurrent writes follow the backend's existing get_data consistency semantics
        Completion of any read causes no accessor-owned state transition

      ON FAILURE during key building, backend I/O, decoding, or deserialization
        PROPAGATE the same failure; do not produce an empty mapping or default result
    END PROCEDURE
