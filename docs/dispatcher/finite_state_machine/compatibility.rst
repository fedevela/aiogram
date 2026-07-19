###########################
FSM accessor compatibility
###########################

This document records the implementation-independent compatibility procedures for adding
``get_value`` to the FSM storage, context, and scene APIs.  The procedures preserve the
established mutation paths and make the supported-Python import-and-await gate explicit;
they introduce no additional runtime behavior.

Requirement-to-logic traceability
=================================

``FSMVALUE-013`` maps to these procedures and verification obligations:

* ``PRESERVE_STORAGE_OPERATION_CONTRACTS`` —
  ``test_fsmvalue_013_memory_redis_and_mongo_established_storage_operations_preserve_inputs_results_isolation_and_mutations``
* ``PRESERVE_FSM_CONTEXT_WORKFLOWS`` —
  ``test_fsmvalue_013_fsm_context_established_state_and_data_workflows_preserve_results_and_mutations``
* ``PRESERVE_SCENE_WIZARD_WORKFLOWS`` —
  ``test_fsmvalue_013_scene_wizard_established_state_and_data_workflows_preserve_results_and_mutations``
* ``INHERIT_DEFAULT_GET_VALUE_IN_CUSTOM_STORAGE`` —
  ``test_fsmvalue_013_custom_storage_with_only_preexisting_abstract_operations_remains_concrete_and_inherits_default_get_value``

``FSMVALUE-014`` maps to ``IMPORT_AND_AWAIT_FSM_GET_VALUE_ON_SUPPORTED_CPYTHON`` and
these five matrix obligations:

* ``test_fsmvalue_014_cpython_3_9_public_fsm_apis_import_and_get_value_coroutines_await_successfully``
* ``test_fsmvalue_014_cpython_3_10_public_fsm_apis_import_and_get_value_coroutines_await_successfully``
* ``test_fsmvalue_014_cpython_3_11_public_fsm_apis_import_and_get_value_coroutines_await_successfully``
* ``test_fsmvalue_014_cpython_3_12_public_fsm_apis_import_and_get_value_coroutines_await_successfully``
* ``test_fsmvalue_014_cpython_3_13_public_fsm_apis_import_and_get_value_coroutines_await_successfully``

Established storage operations
==============================

.. code-block:: text

    PROCEDURE PRESERVE_STORAGE_OPERATION_CONTRACTS(storage, key, isolated_key)
      REQUIREMENT_IDS: FSMVALUE-013
      VERIFICATION:
        test_fsmvalue_013_memory_redis_and_mongo_established_storage_operations_preserve_inputs_results_isolation_and_mutations

      PRECONDITIONS
        storage is one configured MemoryStorage, RedisStorage, or MongoStorage instance
        key and isolated_key are complete, unequal StorageKey values
        No get_value call changes the signatures or dispatch of the established operations

      SET / GET STATE
        AWAIT storage.set_state(key, supplied_state)
        IF supplied_state is a State
          persisted_state := supplied_state.state
        ELSE
          persisted_state := supplied_state
        END IF
        AWAIT storage.get_state(key) and RETURN persisted_state
        AWAIT storage.get_state(isolated_key) and RETURN its independently persisted state
        AWAIT storage.set_state(key, None)
        TRANSITION key state from persisted_state to absent without changing key data

      SET / GET DATA
        AWAIT storage.set_data(key, supplied_mapping)
        PERSIST the backend's established representation under key
        IF storage is MemoryStorage
          COPY supplied_mapping before retaining it and RETURN a copy from get_data
        ELSE IF storage is RedisStorage
          SERIALIZE supplied_mapping and apply configured data_ttl; deserialize on get_data
        ELSE IF storage is MongoStorage
          SET the document data field with upsert behavior; read that field on get_data
        END IF
        AWAIT storage.get_data(key) and RETURN the equivalent complete mapping
        AWAIT storage.get_data(isolated_key) and RETURN only isolated_key's mapping
        Never merge data belonging to unequal StorageKey identities

      UPDATE DATA
        AWAIT storage.update_data(key, partial_mapping)
        MERGE partial_mapping into key's current mapping with partial values winning
        PERSIST the merged mapping using the backend's established update boundary
        RETURN the complete merged mapping
        IF partial_mapping is empty
          PRESERVE and RETURN the current mapping unchanged
        END IF

      CLEAR DATA
        AWAIT storage.set_data(key, empty mapping)
        IF storage is MemoryStorage
          REPLACE key's retained mapping with an empty mapping
        ELSE IF storage is RedisStorage
          DELETE key's data record
        ELSE IF storage is MongoStorage
          UNSET key's data field and delete the document only when no fields remain
        END IF
        AWAIT storage.get_data(key) and RETURN an empty mapping without changing key state

      CLOSE
        AWAIT storage.close() exactly as before get_value was added
        IF storage is MemoryStorage
          COMPLETE without external cleanup
        ELSE IF storage is RedisStorage
          CLOSE the client and its connection pool
        ELSE IF storage is MongoStorage
          CLOSE the client
        END IF

      ORDERING / ISOLATION / REPEATED INVOCATION
        COMPLETE each awaited operation before its result is consumed by the next step
        Preserve StorageKey identity through every call and configured KeyBuilder boundary
        Preserve each backend's existing atomicity and concurrent-read/write semantics
        Do not add accessor-owned locks, transactions, retries, events, or compensation
        Repeating an operation follows that operation's established replace, merge, clear,
          read, or close semantics and never invokes get_value implicitly

      ON FAILURE from validation, key building, serialization, backend I/O, or close
        PROPAGATE the established exception or cancellation from the operation that failed
        DO NOT translate it into a get_value default and DO NOT execute later ordered steps
        Retain exactly the mutation already committed by that backend before the failure
    END PROCEDURE

FSM context workflows
=====================

.. code-block:: text

    PROCEDURE PRESERVE_FSM_CONTEXT_WORKFLOWS(context, operation, arguments)
      REQUIREMENT_IDS: FSMVALUE-013
      VERIFICATION:
        test_fsmvalue_013_fsm_context_established_state_and_data_workflows_preserve_results_and_mutations

      PRECONDITIONS
        context retains its configured BaseStorage and complete StorageKey
        operation is set_state, get_state, set_data, get_data, update_data, or clear

      DECIDE / DELEGATE
        IF operation is set_state
          AWAIT context.storage.set_state(key = context.key, state = arguments.state)
          RETURN None after the storage mutation completes
        ELSE IF operation is get_state
          AWAIT context.storage.get_state(key = context.key)
          RETURN the storage result unchanged
        ELSE IF operation is set_data
          AWAIT context.storage.set_data(key = context.key, data = arguments.data)
          RETURN None after the storage mutation completes
        ELSE IF operation is get_data
          AWAIT context.storage.get_data(key = context.key)
          RETURN the complete storage result unchanged
        ELSE IF operation is update_data
          merged_input := a new mapping containing keyword arguments
          IF arguments.data is truthy
            UPDATE merged_input with arguments.data so explicit data values win on collision
          END IF
          AWAIT context.storage.update_data(key = context.key, data = merged_input)
          RETURN the complete storage result unchanged
        ELSE IF operation is clear
          AWAIT context.set_state(None) to completion
          THEN AWAIT context.set_data(empty mapping) to completion
          TRANSITION context from its prior state/data to absent state and empty data
          RETURN None
        END IF

      IDENTITY / MUTATION INVARIANTS
        Forward the same context.key object for every direct storage delegation
        Mutate only the record identified by that complete key
        Adding get_value introduces no branch, validation, lock, event, or background task
        Repeated invocation retains each preexisting operation's semantics

      ON FAILURE from a delegated await
        PROPAGATE the same exception or cancellation without retry or translation
        IF clear's state reset succeeded but its data reset fails
          LEAVE the state reset committed and the prior data according to storage behavior
          DO NOT roll back or compensate, matching the established two-await sequence
        END IF
    END PROCEDURE

Scene wizard workflows
======================

.. code-block:: text

    PROCEDURE PRESERVE_SCENE_WIZARD_WORKFLOWS(wizard, operation, arguments)
      REQUIREMENT_IDS: FSMVALUE-013
      VERIFICATION:
        test_fsmvalue_013_scene_wizard_established_state_and_data_workflows_preserve_results_and_mutations

      PRECONDITIONS
        wizard.state is the FSMContext supplied at SceneWizard construction
        operation is set_data, get_data, update_data, or clear_data

      DECIDE / DELEGATE
        IF operation is set_data
          AWAIT wizard.state.set_data(data = arguments.data)
          RETURN None after completion
        ELSE IF operation is get_data
          AWAIT wizard.state.get_data()
          RETURN the context result unchanged
        ELSE IF operation is update_data
          merged_input := a new mapping containing keyword arguments
          IF arguments.data is truthy
            UPDATE merged_input with arguments.data so explicit data values win on collision
          END IF
          AWAIT wizard.state.update_data(data = merged_input)
          RETURN the context result unchanged
        ELSE IF operation is clear_data
          AWAIT wizard.set_data(empty mapping)
          TRANSITION only scene data to empty; preserve FSM state and scene lifecycle state
          RETURN None
        END IF

      STATE / ORDERING INVARIANTS
        Do not invoke enter, leave, exit, back, goto, scene actions, or history operations
        Complete the single selected delegation before returning
        Adding get_value does not alter argument precedence, results, or mutations
        Repeated and concurrent calls retain the configured context/storage semantics

      ON FAILURE from the selected delegation
        PROPAGATE the same exception or cancellation
        DO NOT retry, compensate, translate, invoke another workflow, or return a fallback
    END PROCEDURE

Backward-compatible custom storage
==================================

.. code-block:: text

    PROCEDURE INHERIT_DEFAULT_GET_VALUE_IN_CUSTOM_STORAGE(custom_storage_type, key,
      data_key, default = None)
      REQUIREMENT_IDS: FSMVALUE-013
      VERIFICATION:
        test_fsmvalue_013_custom_storage_with_only_preexisting_abstract_operations_remains_concrete_and_inherits_default_get_value

      PRECONDITIONS
        custom_storage_type subclasses BaseStorage
        It implements only the previously required abstract methods:
          set_state, get_state, set_data, get_data, and close
        It does not declare get_value

      VALIDATE CLASS CONTRACT
        BaseStorage.get_value remains asynchronous and concrete, without abstractmethod
        Therefore custom_storage_type has no new abstract operation and remains instantiable

      INSTANTIATE / DELEGATE
        custom_storage := instantiate custom_storage_type using its established constructor
        operation := custom_storage.get_value(key, data_key, default)
        operation is awaitable because the inherited method is asynchronous
        AWAIT operation
        The inherited method AWAITS custom_storage.get_data(key = key) exactly once
        IF returned data contains the exact data_key
          RETURN its associated value, including any falsy value or None
        ELSE
          RETURN default
        END IF

      MUTATION / SUBSTITUTION INVARIANTS
        Do not mutate state or data during lookup
        Do not require backend registration, an adapter, or a concrete get_value override
        IF a custom storage later overrides get_value
          USE normal virtual dispatch and preserve that override's result and failure behavior
        END IF

      ON FAILURE from construction or get_data
        PROPAGATE the same failure without fallback, retry, translation, or compensation
    END PROCEDURE

Supported CPython import-and-await matrix
=========================================

.. code-block:: text

    PROCEDURE IMPORT_AND_AWAIT_FSM_GET_VALUE_ON_SUPPORTED_CPYTHON(python_version)
      REQUIREMENT_IDS: FSMVALUE-014
      VERIFICATION:
        test_fsmvalue_014_cpython_3_9_public_fsm_apis_import_and_get_value_coroutines_await_successfully
        test_fsmvalue_014_cpython_3_10_public_fsm_apis_import_and_get_value_coroutines_await_successfully
        test_fsmvalue_014_cpython_3_11_public_fsm_apis_import_and_get_value_coroutines_await_successfully
        test_fsmvalue_014_cpython_3_12_public_fsm_apis_import_and_get_value_coroutines_await_successfully
        test_fsmvalue_014_cpython_3_13_public_fsm_apis_import_and_get_value_coroutines_await_successfully

      PRECONDITIONS
        python_version is exactly one of 3.9, 3.10, 3.11, 3.12, or 3.13
        The project is installed under that CPython interpreter
        pyproject requires-python and classifiers admit that version
        The source remains valid for the configured minimum syntax and typing target, Python 3.9

      IMPORT PUBLIC MODULES
        IMPORT BaseStorage and StorageKey from aiogram.fsm.storage.base
        IMPORT FSMContext from aiogram.fsm.context
        IMPORT SceneWizard from aiogram.fsm.scene
        Do not require a version-specific alias or compatibility adapter

      ARRANGE VALID COLLABORATORS
        CREATE a concrete contract-conforming BaseStorage with data for one StorageKey
        CREATE FSMContext(storage = concrete storage, key = that same StorageKey)
        CREATE SceneWizard with that FSMContext and otherwise valid constructor collaborators

      INVOKE / VALIDATE AWAITABILITY
        storage_operation := concrete_storage.get_value(key, present_key, default)
        context_operation := context.get_value(present_key, default)
        scene_operation := wizard.get_value(present_key, default)
        FOR operation IN storage_operation, context_operation, scene_operation IN ORDER
          CONFIRM operation is awaitable
          AWAIT operation exactly once
          CONFIRM completion returns the contractually stored value unchanged
        END FOR

      DEFAULT BRANCH
        AWAIT each API with an absent key and caller default
        CONFIRM each completion returns that exact default

      COMPATIBILITY / COMPLETION INVARIANTS
        BaseStorage lookup delegates to get_data with the unchanged StorageKey
        FSMContext delegates to storage with its unchanged key
        SceneWizard delegates to its unchanged FSMContext
        No invocation mutates FSM state or data or starts background work
        The matrix job succeeds only after imports and every await complete on its interpreter

      ON IMPORT, SYNTAX, TYPING, CONSTRUCTION, OR AWAIT FAILURE
        FAIL the current python_version matrix obligation
        PROPAGATE the diagnostic; do not skip, retry on another version, or report success
        Other matrix versions remain independent and continue because CI fail-fast is false
    END PROCEDURE

The public import loci are ``aiogram/fsm/storage/base.py``, ``aiogram/fsm/context.py``,
and ``aiogram/fsm/scene.py``.  The supported interpreter contract is declared in
``pyproject.toml`` and exercised by the ``python-version`` matrix in
``.github/workflows/tests.yml``.  The complete bidirectional verification index remains
``tests/test_fsm/fsmvalue_compatibility_verification_map.json``; the procedures above do
not change production source, schemas, persistence formats, transactions, or generated
boundaries.

FSM compatibility architecture record
=====================================

This record gives every ``FSMVALUE-013`` and ``FSMVALUE-014`` procedure an
implementation-ready home in the existing FSM layering.  It preserves the direction
``SceneWizard -> FSMContext -> BaseStorage -> configured backend`` and introduces no new
backend adapter, persistence representation, lifecycle participant, or public-module
alias.

Architecture traceability map
-----------------------------

``FSMVALUE-013``
~~~~~~~~~~~~~~~~

* ``PRESERVE_STORAGE_OPERATION_CONTRACTS`` and
  ``test_fsmvalue_013_memory_redis_and_mongo_established_storage_operations_preserve_inputs_results_isolation_and_mutations``
  map to the abstract operation contracts in ``aiogram/fsm/storage/base.py``, their
  existing Memory, Redis, and Mongo implementations, and the shared parametrized seam in
  ``tests/test_fsm/storage/test_storages.py``.  Backend data ownership, key encoding,
  mutation, isolation, serialization, and connection cleanup remain at those loci.
* ``PRESERVE_FSM_CONTEXT_WORKFLOWS`` and
  ``test_fsmvalue_013_fsm_context_established_state_and_data_workflows_preserve_results_and_mutations``
  map to ``FSMContext`` in ``aiogram/fsm/context.py`` and its regression seam in
  ``tests/test_fsm/test_context.py``.  The context remains the sole owner of binding a
  configured storage to one complete ``StorageKey``.
* ``PRESERVE_SCENE_WIZARD_WORKFLOWS`` and
  ``test_fsmvalue_013_scene_wizard_established_state_and_data_workflows_preserve_results_and_mutations``
  map to the data-facade methods on ``SceneWizard`` in ``aiogram/fsm/scene.py`` and the
  existing ``TestSceneWizard`` cases in ``tests/test_fsm/test_scene.py``.  Scene lifecycle
  methods, ``ScenesManager``, and ``HistoryManager`` remain outside the data-access path.
* ``INHERIT_DEFAULT_GET_VALUE_IN_CUSTOM_STORAGE`` and
  ``test_fsmvalue_013_custom_storage_with_only_preexisting_abstract_operations_remains_concrete_and_inherits_default_get_value``
  map to the concrete, non-abstract ``BaseStorage.get_value`` declaration and the
  contract-subclass seam in ``tests/test_fsm/storage/test_get_value_contract.py``.
  Custom storages acquire lookup through inheritance without a new required override.

``FSMVALUE-014``
~~~~~~~~~~~~~~~~

``IMPORT_AND_AWAIT_FSM_GET_VALUE_ON_SUPPORTED_CPYTHON`` maps all five verification
obligations to the same public source and execution topology:

* ``test_fsmvalue_014_cpython_3_9_public_fsm_apis_import_and_get_value_coroutines_await_successfully``
* ``test_fsmvalue_014_cpython_3_10_public_fsm_apis_import_and_get_value_coroutines_await_successfully``
* ``test_fsmvalue_014_cpython_3_11_public_fsm_apis_import_and_get_value_coroutines_await_successfully``
* ``test_fsmvalue_014_cpython_3_12_public_fsm_apis_import_and_get_value_coroutines_await_successfully``
* ``test_fsmvalue_014_cpython_3_13_public_fsm_apis_import_and_get_value_coroutines_await_successfully``

The import loci are ``aiogram.fsm.storage.base.BaseStorage``,
``aiogram.fsm.context.FSMContext``, and ``aiogram.fsm.scene.SceneWizard``.  Their method
signatures use the repository's Python 3.9-compatible ``typing`` forms.  The supported
version declaration and distribution classifiers are owned by ``pyproject.toml``; the
independent CPython 3.9--3.13 installation, import, lint, type, and await execution jobs
are owned by the non-fail-fast matrix in ``.github/workflows/tests.yml``.  The five named
cases remain the focused verification index consumed within each matrix environment, not
five version branches in production code.

Placement and ownership
-----------------------

``aiogram/fsm/storage/base.py`` -- storage contract and fallback owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements and procedures:** ``FSMVALUE-013`` through
  ``INHERIT_DEFAULT_GET_VALUE_IN_CUSTOM_STORAGE`` and
  ``PRESERVE_STORAGE_OPERATION_CONTRACTS``; ``FSMVALUE-014`` through
  ``IMPORT_AND_AWAIT_FSM_GET_VALUE_ON_SUPPORTED_CPYTHON``.
* **Responsibility:** keep ``get_value(key, dict_key, default=None)`` asynchronous,
  concrete, and adjacent to the abstract complete-data read.  The default implementation
  awaits polymorphic ``self.get_data(key=key)`` once and owns only exact-key/default
  selection.
* **Incoming dependencies:** ``FSMContext`` and direct storage consumers depend on the
  ``BaseStorage`` contract.  Third-party storage subclasses implement the pre-existing
  abstract state, data, and close ports.
* **Outgoing dependencies:** the fallback depends only on the subclass-provided
  ``get_data`` port.  It does not import a concrete backend, context, scene, test, or CI
  concern.
* **State and failure ownership:** it owns no state and invokes no mutation.  ``get_data``
  exceptions and cancellations cross the await unchanged; no default is substituted for
  a failed read.

Concrete storage modules -- persistence and lifecycle owners
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Loci:** ``aiogram/fsm/storage/memory.py``, ``redis.py``, and ``mongo.py``.
* **Responsibility:** retain all established implementations of ``set_state``,
  ``get_state``, ``set_data``, ``get_data``, ``update_data``, and ``close``.  Memory owns
  copied in-process records; Redis owns key building, JSON encoding, TTL, and client/pool
  cleanup; Mongo owns document fields, upserts, field removal, and client cleanup.
* **Substitution boundary:** these implementations inherit the base fallback.  No backend
  override, registration, migration, data-field addition, or connection-lifecycle change
  is required for either requirement.
* **Consistency:** lookup receives each backend's existing read consistency.  It adds no
  lock, transaction, retry, cache, compensation, queue, publication, or background task.

``aiogram/fsm/context.py`` -- identity-bound FSM facade owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements and procedures:** ``FSMVALUE-013`` through
  ``PRESERVE_FSM_CONTEXT_WORKFLOWS``; ``FSMVALUE-014`` through the context portion of
  ``IMPORT_AND_AWAIT_FSM_GET_VALUE_ON_SUPPORTED_CPYTHON``.
* **Responsibility:** preserve the constructor-supplied ``BaseStorage`` and complete
  ``StorageKey`` as the context's bound identity.  Existing state/data methods keep their
  exact delegations and sequencing; ``get_value`` forwards ``self.key``, the data key,
  and default to the storage contract and returns the awaited result unchanged.
* **Boundary:** callers do not encode storage keys or select persistence backends.
  ``FSMContext`` does not read complete data to implement single-value lookup, so value
  selection remains polymorphic at the storage boundary.
* **Lifecycle and failure:** ``clear`` remains the ordered state reset followed by data
  reset, with its existing partial-failure behavior.  Lookup is an independent read and
  adds no rollback, retry, or error translation to any workflow.

``aiogram/fsm/scene.py`` -- scene-facing data facade owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements and procedures:** ``FSMVALUE-013`` through
  ``PRESERVE_SCENE_WIZARD_WORKFLOWS``; ``FSMVALUE-014`` through the scene portion of
  ``IMPORT_AND_AWAIT_FSM_GET_VALUE_ON_SUPPORTED_CPYTHON``.
* **Responsibility:** keep ``set_data``, ``get_data``, ``update_data``, ``clear_data``, and
  ``get_value`` as thin asynchronous delegations to the constructor-supplied
  ``FSMContext``.  Existing merge precedence and return behavior stay at the wizard
  facade.
* **Non-participants:** scene entry, leave, exit, navigation, action dispatch, history,
  registry, and manager construction have no dependency on lookup and receive no new
  state or event.
* **Failure boundary:** delegated results, exceptions, and cancellations cross unchanged;
  the wizard owns no retry, fallback, compensation, or observability side effect.

Packaging, CI, and verification owners
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``pyproject.toml`` owns the minimum interpreter declaration, CPython classifiers, type
  checker settings, and formatter target.  New declarations must remain valid at the
  Python 3.9 syntax and typing floor.
* ``.github/workflows/tests.yml`` owns cross-version installation and execution.  Its
  CPython 3.9--3.13 matrix has ``fail-fast: false``, so every interpreter is an independent
  compatibility obligation; production code must not dispatch on interpreter version.
* ``tests/test_fsm/test_fsmvalue_compatibility_contract.py`` and
  ``tests/test_fsm/fsmvalue_compatibility_verification_map.json`` own the focused named
  obligations and bidirectional traceability.  Existing storage, context, scene, and
  get-value contract tests are the executable collaborators those obligations extend.
  Production modules have no dependency on verification artifacts.

Contracts and dependency direction
----------------------------------

The synchronous dependency graph contains one awaited, read-only call chain:

.. code-block:: text

    scene caller
      -> SceneWizard.get_value(data_key, default)
      -> FSMContext.get_value(data_key, default)
      -> BaseStorage.get_value(context.key, dict_key, default)
      -> configured storage.get_data(context.key)
      -> unchanged value/default, exception, or cancellation

``StorageKey`` is owned by the storage contract and bound by ``FSMContext``.  The scene
facade never observes it.  The data key and optional default flow downward unchanged; only
the context adds identity.  Complete storage data crosses only the backend-to-base seam,
where exact-key selection occurs.  No complete mapping crosses the context or scene
boundary for this accessor.

The existing mutation graph is separate: scene data methods delegate to context mutation
methods, which delegate to the configured storage.  Adding the read chain does not insert
itself into ``set_state``, ``get_state``, ``set_data``, ``get_data``, ``update_data``,
``clear``, ``clear_data``, or ``close``.  There are no asynchronous integration seams
beyond direct coroutine awaits: no events, brokers, jobs, queues, callbacks, or eventual
consistency protocol participate.

Validation seams and implementation sequence
--------------------------------------------

Implementation follows ownership from the inside out:

1. Preserve the concrete ``BaseStorage.get_value`` fallback and its non-abstract status;
   do not alter backend persistence implementations.
2. Preserve the thin ``FSMContext.get_value`` identity-binding delegation and all
   pre-existing context workflow methods.
3. Preserve the thin ``SceneWizard.get_value`` facade and keep lifecycle collaborators
   excluded.
4. Execute the focused compatibility contract in the supported matrix while retaining
   the existing storage, context, and scene regressions as their owning test seams.

No schema migration, compatibility adapter, generated artifact, configuration switch,
deployment ordering, or rollback mechanism is needed.  The architectural record is the
only phase delta; runtime behavior remains stable.
