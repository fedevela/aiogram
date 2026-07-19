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


FSM context single-value delegation procedural contract
=======================================================

The context accessor is a transparent asynchronous boundary over the storage accessor
defined above.  This procedure records the context-owned logic only; value selection,
backend access, and physical identity encoding remain owned by ``BaseStorage.get_value``,
``get_data``, and the configured backend.

Requirement-to-logic traceability
---------------------------------

All context-level obligations map to ``FSM_CONTEXT_GET_VALUE``:

* ``FSMVALUE-003`` —
  ``test_fsmvalue_003_context_delegates_complete_unchanged_key_name_and_omitted_none_default``
  and
  ``test_fsmvalue_003_context_delegates_supplied_default_and_returns_storage_result``
* ``FSMVALUE-007`` —
  ``test_fsmvalue_007_context_lookup_is_isolated_by_every_storage_key_identity_dimension``
* ``FSMVALUE-009`` —
  ``test_fsmvalue_009_context_get_value_does_not_change_established_fsm_state``
* ``FSMVALUE-010`` —
  ``test_fsmvalue_010_repeated_context_get_value_calls_do_not_change_complete_stored_data``
* ``FSMVALUE-012`` —
  ``test_fsmvalue_012_context_get_value_propagates_storage_read_exception_to_caller`` and
  ``test_fsmvalue_012_context_get_value_propagates_storage_read_cancellation_to_caller``

Context accessor delegation
---------------------------

.. code-block:: text

    PROCEDURE FSM_CONTEXT_GET_VALUE(context, data_key, default = None)
      REQUIREMENT_IDS: FSMVALUE-003, FSMVALUE-007, FSMVALUE-009, FSMVALUE-010,
        FSMVALUE-012
      VERIFICATION:
        test_fsmvalue_003_context_delegates_complete_unchanged_key_name_and_omitted_none_default
        test_fsmvalue_003_context_delegates_supplied_default_and_returns_storage_result
        test_fsmvalue_007_context_lookup_is_isolated_by_every_storage_key_identity_dimension
        test_fsmvalue_009_context_get_value_does_not_change_established_fsm_state
        test_fsmvalue_010_repeated_context_get_value_calls_do_not_change_complete_stored_data
        test_fsmvalue_012_context_get_value_propagates_storage_read_exception_to_caller
        test_fsmvalue_012_context_get_value_propagates_storage_read_cancellation_to_caller

      PRECONDITIONS
        context.storage is the BaseStorage configured for this FSMContext
        context.key is the context's complete immutable StorageKey
        context.key retains bot_id, chat_id, user_id, thread_id,
          business_connection_id, and destiny
        data_key is the exact caller-supplied data key

      RESOLVE DEFAULT
        IF the caller omitted default
          delegated_default := None
        ELSE
          delegated_default := the exact caller-supplied default
        END IF

      DELEGATE / AWAIT / RETURN
        AWAIT context.storage.get_value(
          key = context.key,
          dict_key = data_key,
          default = delegated_default,
        ) exactly once
        RETURN the storage result directly to the caller

      IDENTITY / DATA FLOW INVARIANTS
        FORWARD context.key as the same complete StorageKey value
        DO NOT reconstruct, normalize, copy, or omit any StorageKey dimension
        DO NOT normalize or transform data_key or delegated_default
        DO NOT inspect, copy, coerce, cache, or replace the storage result

      STATE / MUTATION INVARIANTS
        DO NOT call context.get_state, context.set_state, context.set_data,
          context.update_data, or context.clear
        DO NOT call any storage mutation operation
        DO NOT mutate context.storage, context.key, FSM state, or stored FSM data
        Successful completion causes no state transition and emits no event
        Repeated invocation performs one new independent delegation per call and retains
          the same no-transition and no-mutation guarantees

      ORDERING / CONCURRENCY
        Begin no context-owned transaction, lock, retry, or background work
        Suspend only while awaiting the configured storage accessor
        Use the configured storage's existing read consistency and completion behavior

      ON FAILURE from storage.get_value, including read exception or cancellation
        DO NOT return delegated_default or any other successful result
        DO NOT catch, retry, compensate, translate, wrap, or suppress the failure
        PROPAGATE the same failure to the context caller
    END PROCEDURE

Owning boundary and implementation sequence
-------------------------------------------

``aiogram/fsm/context.py`` owns ``FSM_CONTEXT_GET_VALUE`` because ``FSMContext`` already
owns transparent delegation of state and data operations through its configured
``storage`` and ``key`` attributes.  The implementation is one asynchronous method whose
body is one awaited return expression forwarding ``key=self.key``, the exact data key, and
the resolved default to ``self.storage.get_value``.  It introduces no validation branch,
fallback handling, backend selection, persistence operation, or failure boundary.

``aiogram/fsm/storage/base.py`` remains the outgoing contract.  Normal virtual dispatch
selects the configured storage's inherited or overridden ``get_value`` implementation;
the context neither bypasses that method through ``get_data`` nor duplicates its mapping
lookup.  The existing Memory, Redis, Mongo, and custom storage paths therefore retain
their established identity, serialization, isolation, and error behavior.

``tests/test_fsm/test_context_get_value_contract.py`` owns the seven named context-level
verification obligations, while
``tests/test_fsm/fsmcontext_get_value_verification_map.json`` preserves their
bidirectional requirement mapping.  Implementation follows one dependency step: add the
transparent method to ``FSMContext`` without changing ``BaseStorage``, concrete backends,
middleware context construction, schemas, migrations, queues, or runtime configuration.


FSM context single-value delegation architecture record
========================================================

This record gives ``FSM_CONTEXT_GET_VALUE`` an implementation-ready home while preserving
the existing FSM dependency direction.  The context remains a caller-facing facade over a
configured ``BaseStorage`` and one complete ``StorageKey``; it does not become a data owner,
backend adapter, identity encoder, transaction boundary, or failure boundary.

Architecture traceability map
-----------------------------

* ``FSMVALUE-003``,
  ``test_fsmvalue_003_context_delegates_complete_unchanged_key_name_and_omitted_none_default``,
  and
  ``test_fsmvalue_003_context_delegates_supplied_default_and_returns_storage_result`` map
  ``FSM_CONTEXT_GET_VALUE`` to a new concrete asynchronous ``FSMContext.get_value`` method
  in ``aiogram/fsm/context.py`` and to its existing outgoing ``BaseStorage.get_value``
  contract in ``aiogram/fsm/storage/base.py``.
* ``FSMVALUE-007`` and
  ``test_fsmvalue_007_context_lookup_is_isolated_by_every_storage_key_identity_dimension``
  map ``FSM_CONTEXT_GET_VALUE`` to unchanged forwarding of ``FSMContext.key`` and to the
  frozen ``StorageKey`` identity contract.  Storage implementations and their configured
  key builders remain responsible for physical isolation after the complete key crosses
  the context-to-storage seam.
* ``FSMVALUE-009`` and
  ``test_fsmvalue_009_context_get_value_does_not_change_established_fsm_state`` map
  ``FSM_CONTEXT_GET_VALUE`` to the read-only context-to-storage path.  The method has no
  dependency on ``FSMContext.set_state``, ``BaseStorage.set_state``, or any lifecycle
  transition.
* ``FSMVALUE-010`` and
  ``test_fsmvalue_010_repeated_context_get_value_calls_do_not_change_complete_stored_data``
  map ``FSM_CONTEXT_GET_VALUE`` to one independent storage delegation per invocation.  The
  context neither receives nor mutates the complete data mapping and does not call any
  context or storage mutation port.
* ``FSMVALUE-012``,
  ``test_fsmvalue_012_context_get_value_propagates_storage_read_exception_to_caller``, and
  ``test_fsmvalue_012_context_get_value_propagates_storage_read_cancellation_to_caller``
  map ``FSM_CONTEXT_GET_VALUE`` to an unguarded await of ``BaseStorage.get_value``.  The
  context adds no catch, retry, fallback, translation, compensation, or cancellation
  boundary.

Placement and ownership
-----------------------

``aiogram/fsm/context.py`` — context delegation owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** ``FSMVALUE-003``, ``FSMVALUE-007``, ``FSMVALUE-009``,
  ``FSMVALUE-010``, and ``FSMVALUE-012``.
* **Procedure:** ``FSM_CONTEXT_GET_VALUE``.
* **Responsibility:** expose ``get_value(data_key, default=None)`` alongside the existing
  ``get_state`` and ``get_data`` facade methods.  Its entire authority is to await
  ``self.storage.get_value(key=self.key, dict_key=data_key, default=default)`` and return
  that result directly.
* **Owned state:** none.  ``storage`` and ``key`` are constructor-supplied collaborators;
  the accessor reads both references but has no mutation authority over either one.
* **Incoming dependencies:** handlers, scenes, middleware-injected state objects, and
  direct callers depend on the public ``FSMContext`` API.  No caller needs access to a
  concrete storage backend.
* **Outgoing dependency:** depend only on the existing ``BaseStorage.get_value`` method.
  Do not call ``get_data`` directly, because that would bypass a conforming storage
  override and duplicate storage-owned value/default semantics.
* **Compatibility:** adding a concrete method does not alter context construction or any
  existing context method.  There is no new constructor argument, exported symbol,
  configuration field, or lifecycle hook.

``aiogram/fsm/storage/base.py`` — outgoing value-read contract and identity owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** all five requirements through the context's outgoing seam;
  ``FSMVALUE-007`` additionally binds the complete identity contract here.
* **Procedure:** ``FSM_CONTEXT_GET_VALUE`` delegates into the previously recorded
  ``DISPATCH_GET_VALUE`` and ``BASE_STORAGE_GET_VALUE`` procedures.
* **Responsibility:** ``BaseStorage.get_value`` owns polymorphic value selection, caller
  default semantics, and the backend read.  The frozen ``StorageKey`` owns bot, chat,
  user, thread, business connection, and destiny identity as one value.
* **Contract crossing the seam:** the exact ``FSMContext.key``, exact caller data key, and
  exact default cross into storage; the storage result or raised failure crosses back.
  The context does not reconstruct a ``StorageKey`` or unpack any identity dimension.
* **Substitution:** normal virtual dispatch must reach an inherited or overridden
  ``get_value`` implementation.  The context therefore depends on ``BaseStorage``, never
  on Memory, Redis, Mongo, or a custom storage class.

``aiogram/fsm/middleware.py`` and ``aiogram/fsm/scene.py`` — identity assembly and reuse
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirement:** ``FSMVALUE-007``.
* **Procedure:** precondition supply for ``FSM_CONTEXT_GET_VALUE``; neither module owns
  the lookup procedure.
* **Responsibility:** middleware continues to assemble the complete ``StorageKey`` from
  bot and event identity after applying the configured FSM strategy.  Scene history may
  derive a new frozen key with a different destiny before constructing another context.
* **Dependency direction:** these modules construct ``FSMContext`` values; the context
  never depends back on middleware, event models, FSM strategy, or scene management.
* **Structural delta:** none.  Existing constructors already supply the complete key and
  configured storage required by the accessor.

``aiogram/fsm/storage/{memory,redis,mongo}.py`` and custom storages — data owners
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** ``FSMVALUE-007``, ``FSMVALUE-009``, ``FSMVALUE-010``, and
  ``FSMVALUE-012`` after delegation leaves the context boundary.
* **Procedure:** downstream execution of ``FSM_CONTEXT_GET_VALUE`` through the existing
  storage procedures.
* **Responsibility:** retain record ownership, physical identity encoding, read
  consistency, serialization, backend I/O, and backend failure behavior.  No backend
  implementation change is required by the context accessor.
* **Lifecycle and failure ownership:** backend connections continue to be closed by their
  established storage lifecycle.  A read opens no context-owned lock or transaction and
  publishes no event.  Backend, codec, key-building, and cancellation failures propagate
  through both storage and context without translation.

Boundaries, flow, and validation seams
--------------------------------------

The only new public contract is the asynchronous ``FSMContext.get_value`` method.  Its
call topology is:

.. code-block:: text

    caller
      -> FSMContext.get_value(data_key, default)
      -> configured BaseStorage.get_value(context.key, data_key, default)
      -> inherited or overridden storage read path
      -> result or unchanged failure

This is a synchronous call relationship containing asynchronous awaits, not a queue,
event, job, or background-work seam.  ``FSMContext`` owns completion only until the
delegated await returns or raises.  Storage retains data and consistency ownership; no
new cache, persistence schema, migration, authorization check, deployment setting,
observability event, retry policy, or compensation path is introduced.

``tests/test_fsm/test_context_get_value_contract.py`` is the focused context-boundary
verification seam.  Its instrumented storage collaborator must observe exact argument
identity and polymorphic dispatch; ``MemoryStorage`` contexts must demonstrate isolation
and read-only behavior; failing collaborators must demonstrate unchanged exception and
cancellation propagation.  ``tests/test_fsm/fsmcontext_get_value_verification_map.json``
continues to own bidirectional requirement-to-verification traceability.  Production
modules do not depend on either test artifact.

Implementation sequence
-----------------------

1. Add the one-expression asynchronous method to ``FSMContext`` using the existing
   ``BaseStorage.get_value`` contract; do not change context construction or storage
   implementations.
2. Replace the seven focused context verification placeholders with executable delegation,
   isolation, immutability, and failure-propagation cases.
3. Run the focused context contract, existing context/storage regression seams, formatting,
   typing, and documentation validation.  No migration or staged rollout is required.
