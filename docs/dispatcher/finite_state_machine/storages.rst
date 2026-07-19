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


Single-value lookup architecture record
=======================================

This record assigns every obligation above to an implementation locus.  It preserves the
current storage topology: shared algorithms live on ``BaseStorage``; backend data ownership
remains behind ``get_data``; and identity encoding remains behind ``StorageKey`` and
``KeyBuilder``.  It introduces no runtime behavior by itself.

Architecture traceability map
-----------------------------

* ``FSMVALUE-001`` and
  ``test_fsmvalue_001_get_value_accepts_storage_key_string_key_and_optional_none_default``
  map ``DISPATCH_GET_VALUE`` and ``BASE_STORAGE_GET_VALUE`` to the concrete,
  asynchronous ``BaseStorage.get_value`` contract in ``aiogram/fsm/storage/base.py``.
* ``FSMVALUE-002``,
  ``test_fsmvalue_002_default_get_value_awaits_get_data_with_the_unchanged_storage_key``,
  and ``test_fsmvalue_002_storage_subclass_override_is_used_when_get_value_is_awaited``
  map all three procedures to the overridable ``BaseStorage.get_value`` method and its
  dependency on the existing ``BaseStorage.get_data`` port.
* ``FSMVALUE-004`` and
  ``test_fsmvalue_004_each_exact_string_key_returns_its_untransformed_supported_value``
  map ``BASE_STORAGE_GET_VALUE`` to exact mapping lookup inside ``BaseStorage.get_value``.
* ``FSMVALUE-005`` and
  ``test_fsmvalue_005_absent_key_returns_none_or_the_caller_supplied_default`` map
  ``BASE_STORAGE_GET_VALUE`` to the same method's caller-default branch.
* ``FSMVALUE-006`` and
  ``test_fsmvalue_006_present_falsy_or_none_value_wins_over_the_supplied_default`` map
  ``BASE_STORAGE_GET_VALUE`` to presence-based mapping semantics in that method.
* ``FSMVALUE-007`` and
  ``test_fsmvalue_007_lookup_is_isolated_by_every_storage_key_identity_dimension`` map
  ``BASE_STORAGE_GET_VALUE`` and ``GET_DATA_FOR_SINGLE_VALUE`` to unchanged
  ``StorageKey`` forwarding, the immutable ``StorageKey`` value, Memory's record index,
  and Redis/Mongo ``KeyBuilder`` adapters.
* ``FSMVALUE-009`` and
  ``test_fsmvalue_009_present_and_absent_get_value_reads_do_not_change_fsm_state`` map
  ``BASE_STORAGE_GET_VALUE`` and ``GET_DATA_FOR_SINGLE_VALUE`` to the read-only
  ``get_value`` to ``get_data`` call path, with no state port dependency.
* ``FSMVALUE-010`` and
  ``test_fsmvalue_010_repeated_present_and_absent_get_value_reads_do_not_change_data`` map
  those procedures to the same read-only path and to each backend's established
  ``get_data`` copy/deserialization behavior.
* ``FSMVALUE-011`` and
  ``test_fsmvalue_011_memory_redis_mongo_and_custom_backends_share_accessor_results`` map
  all three procedures to the inherited ``BaseStorage.get_value`` algorithm and the
  Memory, Redis, Mongo, and custom ``get_data`` adapters.
* ``FSMVALUE-012``,
  ``test_fsmvalue_012_backend_read_exception_remains_observable_without_fallback``, and
  ``test_fsmvalue_012_read_cancellation_remains_observable_without_fallback`` map
  ``BASE_STORAGE_GET_VALUE`` and ``GET_DATA_FOR_SINGLE_VALUE`` to unguarded await and
  failure propagation across the ``get_data`` seam.

Owning loci and contracts
-------------------------

``aiogram/fsm/storage/base.py`` — accessor owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** ``FSMVALUE-001``, ``FSMVALUE-002``, ``FSMVALUE-004``,
  ``FSMVALUE-005``, ``FSMVALUE-006``, ``FSMVALUE-007``, ``FSMVALUE-009``,
  ``FSMVALUE-010``, ``FSMVALUE-011``, and ``FSMVALUE-012``.
* **Procedures:** ``DISPATCH_GET_VALUE`` and ``BASE_STORAGE_GET_VALUE``; it initiates
  ``GET_DATA_FOR_SINGLE_VALUE`` through the existing virtual ``get_data`` call.
* **Responsibility:** own the backend-independent, single-value read algorithm as a
  concrete ``BaseStorage`` method.  The implementation signature is asynchronous, accepts
  one unchanged ``StorageKey``, one exact ``str`` data key, and an optional caller default
  whose omitted value is ``None``, and returns ``Any``.
* **Incoming dependency:** callers depend only on the ``BaseStorage`` contract.  Python's
  normal virtual dispatch selects an overriding backend method when one exists.
* **Outgoing dependency:** the default method awaits ``self.get_data`` exactly once with
  the original ``StorageKey`` and then applies mapping key/default semantics.  It does not
  depend on ``get_state``, mutation methods, event isolation, a concrete backend, or a key
  builder.
* **Crossing data and failures:** one ``StorageKey`` and no mutable state cross into
  ``get_data``; one backend-supported data mapping or one read failure crosses back.  The
  selected stored value or caller default crosses to the caller without transformation.
  Exceptions and cancellation cross unchanged because this locus adds no catch, retry, or
  translation boundary.
* **Compatibility:** ``get_value`` is concrete rather than abstract.  Existing Memory,
  Redis, Mongo, and custom ``BaseStorage`` subclasses therefore remain constructible and
  inherit the default; an override remains substitutable and is selected normally.
* **Validation seam:** the signature, delegation, override, exact-key, default, falsy,
  immutability, backend-consistency, and failure cases named in the traceability map.

``aiogram/fsm/storage/{memory,redis,mongo}.py`` — data owners and adapters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** ``FSMVALUE-002``, ``FSMVALUE-007``, ``FSMVALUE-009``,
  ``FSMVALUE-010``, ``FSMVALUE-011``, and ``FSMVALUE-012``.
* **Procedure:** ``GET_DATA_FOR_SINGLE_VALUE``.
* **Responsibility:** retain ownership of record lookup, backend I/O, serialization,
  backend-supported value types, and existing read consistency.  No backend override is
  required for the default contract.
* **Incoming dependency:** ``BaseStorage.get_value`` calls the polymorphic ``get_data``
  port.  Custom storage implementations participate through that same existing port.
* **Outgoing dependencies:** Memory indexes its in-process record map; Redis uses its
  configured ``KeyBuilder``, Redis client, and JSON codec; Mongo uses its configured
  ``KeyBuilder``, collection, and BSON codec.
* **Crossing data and failures:** each adapter receives the complete ``StorageKey`` and
  returns its established ``Dict[str, Any]`` view.  Key-building, I/O, and codec failures
  remain owned by the adapter and propagate through the accessor without translation.
* **Lifecycle and consistency:** lookup opens no transaction, acquires no accessor-level
  lock, publishes no event, performs no retry, and owns no state transition.  Concurrent
  behavior remains exactly the selected backend's existing ``get_data`` behavior.
* **Validation seam:** the shared storage contract suite plus focused backend fixtures;
  isolation tests configure key builders to preserve every applicable identity dimension.

``aiogram/fsm/storage/base.py`` — identity boundary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirement:** ``FSMVALUE-007``.
* **Procedures:** ``BASE_STORAGE_GET_VALUE`` and ``GET_DATA_FOR_SINGLE_VALUE``.
* **Responsibility:** ``StorageKey`` owns the complete immutable identity tuple.
  ``KeyBuilder`` owns conversion of that tuple for external backends.  The accessor has no
  authority to reconstruct, normalize, or omit identity fields.
* **Dependency direction:** the accessor depends on ``StorageKey`` as a value contract;
  only backend adapters depend on ``KeyBuilder``.  ``KeyBuilder`` does not depend on the
  accessor.
* **Crossing data:** bot, chat, user, thread, business connection, and destiny dimensions
  cross together.  Backend configuration is responsible for preserving dimensions that
  apply to its physical key scheme.
* **Validation seam:**
  ``test_fsmvalue_007_lookup_is_isolated_by_every_storage_key_identity_dimension`` and
  ``tests/test_fsm/storage/test_key_builder.py``.

``tests/test_fsm/storage`` — contract verification owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements and procedures:** all requirement IDs and all three procedures in the
  architecture traceability map.
* **Responsibility:** ``test_get_value_contract.py`` owns focused behavioral verification;
  ``fsmvalue_verification_map.json`` owns bidirectional requirement-to-verification
  traceability; existing storage fixtures provide Memory, Redis, and Mongo adapters.
* **Dependency direction:** tests depend on the public storage abstractions and concrete
  fixtures.  Production modules never depend on test artifacts.
* **Observed seams:** an instrumented custom subclass observes unchanged delegation; an
  overriding subclass observes dispatch; backend fixtures observe inherited behavior; a
  failing custom ``get_data`` implementation observes exception and cancellation flow.

Integration and implementation sequence
---------------------------------------

The synchronous portion is only in-memory mapping selection after the asynchronous backend
read.  The sole asynchronous seam is ``BaseStorage.get_value`` awaiting the polymorphic
``get_data`` operation.  There is no queue, event, job, persistence migration, deployment
configuration, authorization boundary, compensation path, or new observability channel.
``FSMContext`` and dispatcher middleware continue to assemble and carry ``StorageKey``
values but gain no responsibility under this storage-level issue.

Implementation should proceed in this dependency order:

1. Add the concrete ``BaseStorage.get_value`` declaration and default algorithm without
   changing abstract methods or backend implementations.
2. Replace the focused verification placeholders with executable contract cases, using a
   custom default-inheriting storage and an overriding storage before exercising supported
   backend fixtures.
3. Validate the focused contract, existing storage and key-builder tests, type checking,
   formatting, and documentation.  No data migration or staged deployment is required.
