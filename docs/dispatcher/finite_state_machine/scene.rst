.. _Scenes:

=============
Scenes Wizard
=============

.. versionadded:: 3.2

.. warning::

    This feature is experimental and may be changed in future versions.

**aiogram's** basics API is easy to use and powerful,
allowing the implementation of simple interactions such as triggering a command or message
for a response.
However, certain tasks require a dialogue between the user and the bot.
This is where Scenes come into play.

Understanding Scenes
====================

A Scene in **aiogram** is like an abstract, isolated namespace or room that a user can be
ushered into via the code. When a user is within a Scene, most other global commands or
message handlers are bypassed, unless they are specifically designed to function outside of the Scenes.
This helps in creating an experience of focused interactions.
Scenes provide a structure for more complex interactions,
effectively isolating and managing contexts for different stages of the conversation.
They allow you to control and manage the flow of the conversation in a more organized manner.

Scene Lifecycle
---------------

Each Scene can be "entered", "left" of "exited", allowing for clear transitions between different
stages of the conversation.
For instance, in a multi-step form filling interaction, each step could be a Scene -
the bot guides the user from one Scene to the next as they provide the required information.

Scene Listeners
---------------

Scenes have their own hooks which are command or message listeners that only act while
the user is within the Scene.
These hooks react to user actions while the user is 'inside' the Scene,
providing the responses or actions appropriate for that context.
When the user is ushered from one Scene to another, the actions and responses change
accordingly as the user is now interacting with the set of listeners inside the new Scene.
These 'Scene-specific' hooks or listeners, detached from the global listening context,
allow for more streamlined and organized bot-user interactions.


Scene Interactions
------------------

Each Scene is like a self-contained world, with interactions defined within the scope of that Scene.
As such, only the handlers defined within the specific Scene will react to user's input during
the lifecycle of that Scene.


Scene Benefits
--------------

Scenes can help manage more complex interaction workflows and enable more interactive and dynamic
dialogs between the user and the bot.
This offers great flexibility in handling multi-step interactions or conversations with the users.

How to use Scenes
=================

For example we have a quiz bot, which asks the user a series of questions and then displays the results.

Lets start with the data models, in this example simple data models are used to represent
the questions and answers, in real life you would probably use a database to store the data.

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :lines: 25-101
    :caption: Questions list

Then, we need to create a Scene class that will represent the quiz game scene:

.. note::

    Keyword argument passed into class definition describes the scene name - is the same as state of the scene.

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :pyobject: QuizScene
    :emphasize-lines: 1
    :lines: -7
    :caption: Quiz Scene


Also we need to define a handler that helps to start the quiz game:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Start command handler
    :lines: 260-262

Once the scene is defined, we need to register it in the SceneRegistry:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :pyobject: create_dispatcher
    :caption: Registering the scene

So, now we can implement the quiz game logic, each question is sent to the user one by one,
and the user's answer is checked at the end of all questions.

Now we need to write an entry point for the question handler:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Question handler entry point
    :pyobject: QuizScene.on_enter


Once scene is entered, we should expect the user's answer, so we need to write a handler for it,
this handler should expect the text message, save the answer and retake
the question handler for the next question:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Answer handler
    :pyobject: QuizScene.answer

When user answer with unknown message, we should expect the text message again:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Unknown message handler
    :pyobject: QuizScene.unknown_message

When all questions are answered, we should show the results to the user, as you can see in the code below,
we use `await self.wizard.exit()` to exit from the scene when questions list is over in the `QuizScene.on_enter` handler.

Thats means that we need to write an exit handler to show the results to the user:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Show results handler
    :pyobject: QuizScene.on_exit

Also we can implement a actions to exit from the quiz game or go back to the previous question:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Exit handler
    :pyobject: QuizScene.exit

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Back handler
    :pyobject: QuizScene.back

Now we can run the bot and test the quiz game:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Run the bot
    :lines: 291-

Complete them all

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Quiz Example


Components
==========

- :class:`aiogram.fsm.scene.Scene` - represents a scene, contains handlers
- :class:`aiogram.fsm.scene.SceneRegistry` - container for all scenes in the bot, used to register scenes and resolve them by name
- :class:`aiogram.fsm.scene.ScenesManager` - manages scenes for each user, used to enter, leave and resolve current scene for user
- :class:`aiogram.fsm.scene.SceneConfig` - scene configuration, used to configure scene
- :class:`aiogram.fsm.scene.SceneWizard` - scene wizard, used to interact with user in scene from active scene handler
- Markers - marker for scene handlers, used to mark scene handlers


.. autoclass:: aiogram.fsm.scene.Scene
    :members:

.. autoclass:: aiogram.fsm.scene.SceneRegistry
    :members:

.. autoclass:: aiogram.fsm.scene.ScenesManager
    :members:

.. autoclass:: aiogram.fsm.scene.SceneConfig
    :members:

.. autoclass:: aiogram.fsm.scene.SceneWizard
    :members:


SceneWizard single-value lookup procedural contract
===================================================

The scene accessor is a transparent asynchronous facade over
``FSMContext.get_value``.  The procedure below records the complete scene-owned logic;
the context and configured storage retain ownership of FSM identity, value selection,
persistence, and read consistency.

Requirement-to-logic traceability
---------------------------------

All scene-level obligations map to ``SCENE_WIZARD_GET_VALUE``:

* ``FSMVALUE-008`` —
  ``test_fsmvalue_008_scene_wizard_delegates_data_key_with_omitted_none_default_and_returns_context_result``
  and
  ``test_fsmvalue_008_scene_wizard_delegates_exact_data_key_and_supplied_default_and_returns_context_result_unchanged``
* ``FSMVALUE-009`` —
  ``test_fsmvalue_009_scene_wizard_get_value_once_or_repeatedly_for_present_or_absent_keys_preserves_fsm_state``
* ``FSMVALUE-010`` —
  ``test_fsmvalue_010_scene_wizard_get_value_once_or_repeatedly_for_present_or_absent_keys_preserves_complete_data``
* ``FSMVALUE-012`` —
  ``test_fsmvalue_012_scene_wizard_get_value_propagates_storage_read_exception_to_scene_caller``
  and
  ``test_fsmvalue_012_scene_wizard_get_value_propagates_storage_read_cancellation_to_scene_caller``

Scene accessor delegation
-------------------------

.. code-block:: text

    PROCEDURE SCENE_WIZARD_GET_VALUE(wizard, data_key, default = None)
      REQUIREMENT_IDS: FSMVALUE-008, FSMVALUE-009, FSMVALUE-010, FSMVALUE-012
      VERIFICATION:
        test_fsmvalue_008_scene_wizard_delegates_data_key_with_omitted_none_default_and_returns_context_result
        test_fsmvalue_008_scene_wizard_delegates_exact_data_key_and_supplied_default_and_returns_context_result_unchanged
        test_fsmvalue_009_scene_wizard_get_value_once_or_repeatedly_for_present_or_absent_keys_preserves_fsm_state
        test_fsmvalue_010_scene_wizard_get_value_once_or_repeatedly_for_present_or_absent_keys_preserves_complete_data
        test_fsmvalue_012_scene_wizard_get_value_propagates_storage_read_exception_to_scene_caller
        test_fsmvalue_012_scene_wizard_get_value_propagates_storage_read_cancellation_to_scene_caller

      INPUTS / PRECONDITIONS
        wizard.state is the FSMContext supplied when this SceneWizard was constructed
        data_key is the exact caller-supplied data key
        default is either omitted or is the exact caller-supplied object
        No scene lifecycle transition, authorization decision, or data validation is required

      RESOLVE DEFAULT
        IF the caller omitted default
          delegated_default := None
        ELSE
          delegated_default := the exact caller-supplied default
        END IF

      DELEGATE / AWAIT
        AWAIT wizard.state.get_value(
          data_key = data_key,
          default = delegated_default,
        ) exactly once
        RECEIVE context_result only after that await completes successfully

      DATA FLOW INVARIANTS
        FORWARD data_key without normalization, copying, validation, or substitution
        FORWARD delegated_default without copying, coercion, or substitution
        DO NOT inspect, copy, cache, coerce, or replace context_result

      STATE / MUTATION INVARIANTS
        DO NOT call wizard.state.get_state, set_state, get_data, set_data,
          update_data, or clear
        DO NOT invoke enter, leave, exit, back, retake, goto, manager history,
          scene actions, persistence mutations, events, or notifications
        Successful completion causes no FSM or scene state transition
        Successful completion preserves the complete stored FSM data
        Repeated invocation performs one independent context delegation per call and
          retains the same no-transition and no-mutation guarantees for present and
          absent keys

      ORDERING / CONCURRENCY
        Begin no wizard-owned lock, transaction, retry, compensation, or background work
        Suspend only while awaiting the underlying FSMContext accessor
        Concurrent calls remain independent and use the context/storage read semantics
        Completion of one invocation does not initiate or await another invocation

      RETURN context_result unchanged to the scene caller

      ON FAILURE from wizard.state.get_value, including storage read exception or
        asynchronous cancellation
        DO NOT return delegated_default, None, or any other successful result
        DO NOT catch, retry, compensate, translate, wrap, log-and-suppress, or replace
          the failure
        PROPAGATE the same failure to the scene caller
    END PROCEDURE

Owning boundary and implementation sequence
-------------------------------------------

``aiogram/fsm/scene.py`` owns ``SCENE_WIZARD_GET_VALUE`` because ``SceneWizard`` already
owns the scene-facing ``set_data``, ``get_data``, ``update_data``, and ``clear_data``
facade.  The implementation is one asynchronous method alongside those operations.  Its
body is one awaited return expression that passes the exact ``data_key`` and resolved
``default`` to ``self.state.get_value``.  It adds no constructor argument, validation
branch, lifecycle call, result transformation, or failure boundary.

``aiogram/fsm/context.py`` remains the only outgoing dependency.  Its existing
``FSMContext.get_value`` procedure forwards the complete context ``StorageKey`` and the
scene arguments to ``BaseStorage.get_value``.  ``SceneWizard`` must not call ``get_data``
or a storage object directly: either choice would duplicate value/default semantics or
bypass a conforming context/storage accessor.

The complete asynchronous call topology is:

.. code-block:: text

    scene caller
      -> SceneWizard.get_value(data_key, default)
      -> wizard.state.get_value(data_key, default)
      -> configured BaseStorage.get_value(context.key, data_key, default)
      -> backend read path
      -> unchanged result or unchanged failure through every boundary

No queue, scheduled work, transaction, schema, migration, generated boundary, retry
policy, or recovery state participates in this read.  Existing scene entry, exit,
history, and action flows remain separate and unchanged.

``tests/test_fsm/test_scene_get_value_contract.py`` owns the six named verification
obligations.  ``tests/test_fsm/scene_get_value_verification_map.json`` preserves their
bidirectional mapping to ``FSMVALUE-008``, ``FSMVALUE-009``, ``FSMVALUE-010``, and
``FSMVALUE-012``.  Implementation proceeds by adding only the transparent method to
``SceneWizard``; no storage, context, scene-construction, or configuration change is
required.

SceneWizard single-value lookup architecture record
===================================================

This record assigns every ``SCENE_WIZARD_GET_VALUE`` obligation to the existing scene,
context, and storage boundaries.  The architectural delta is one scene-facing method;
the established FSM identity, persistence, lifecycle, and backend substitution boundaries
remain unchanged.

Architecture traceability map
-----------------------------

* ``FSMVALUE-008``,
  ``test_fsmvalue_008_scene_wizard_delegates_data_key_with_omitted_none_default_and_returns_context_result``,
  and
  ``test_fsmvalue_008_scene_wizard_delegates_exact_data_key_and_supplied_default_and_returns_context_result_unchanged``
  map ``SCENE_WIZARD_GET_VALUE`` to a new concrete asynchronous
  ``SceneWizard.get_value`` method in ``aiogram/fsm/scene.py`` and its existing outgoing
  ``FSMContext.get_value`` contract in ``aiogram/fsm/context.py``.
* ``FSMVALUE-009`` and
  ``test_fsmvalue_009_scene_wizard_get_value_once_or_repeatedly_for_present_or_absent_keys_preserves_fsm_state``
  map the procedure to the read-only wizard-to-context seam.  The method has no dependency
  on scene transition methods, ``ScenesManager``, ``HistoryManager``, or the FSM state
  mutation ports.
* ``FSMVALUE-010`` and
  ``test_fsmvalue_010_scene_wizard_get_value_once_or_repeatedly_for_present_or_absent_keys_preserves_complete_data``
  map the procedure to one independent ``FSMContext.get_value`` delegation per call.  The
  wizard does not request the complete data mapping and cannot mutate storage-owned data.
* ``FSMVALUE-012``,
  ``test_fsmvalue_012_scene_wizard_get_value_propagates_storage_read_exception_to_scene_caller``,
  and
  ``test_fsmvalue_012_scene_wizard_get_value_propagates_storage_read_cancellation_to_scene_caller``
  map the procedure to an unguarded await.  ``SceneWizard`` adds no exception, cancellation,
  fallback, retry, translation, logging, or compensation boundary.

Placement and ownership
-----------------------

``aiogram/fsm/scene.py`` — scene facade owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** ``FSMVALUE-008``, ``FSMVALUE-009``, ``FSMVALUE-010``, and
  ``FSMVALUE-012``.
* **Procedure:** ``SCENE_WIZARD_GET_VALUE``.
* **Responsibility:** expose ``get_value(data_key, default=None)`` beside
  ``SceneWizard.get_data``, ``set_data``, ``update_data``, and ``clear_data``.  Its entire
  authority is to await ``self.state.get_value(data_key=data_key, default=default)`` and
  return that result unchanged.
* **Owned state:** none.  The constructor-supplied ``state`` reference identifies the FSM
  context for the active scene; the accessor neither replaces that reference nor owns the
  state and data behind it.
* **Incoming dependencies:** scene handlers and other consumers of the public
  ``SceneWizard`` API.  Callers remain insulated from storage keys and configured storage
  implementations.
* **Outgoing dependency:** only the existing ``FSMContext.get_value`` method.  Calling
  ``FSMContext.get_data`` or ``BaseStorage`` directly would duplicate value/default
  selection or bypass the context boundary.
* **Compatibility:** the method is additive.  It changes no constructor, scene protocol,
  exported symbol, lifecycle hook, action registration, configuration, or generated
  boundary.

``aiogram/fsm/context.py`` — bound identity and delegation boundary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** all four requirements after the call leaves the scene facade.
* **Procedures:** ``SCENE_WIZARD_GET_VALUE`` delegates into the existing
  ``FSM_CONTEXT_GET_VALUE`` procedure.
* **Responsibility:** retain ownership of the complete ``StorageKey`` binding and forward
  it with the exact data key and default to ``BaseStorage.get_value``.  The wizard neither
  sees nor reconstructs storage identity.
* **Incoming dependency:** ``SceneWizard`` depends on the concrete public ``FSMContext``
  API already supplied at construction.
* **Outgoing dependency:** the context continues to depend only on the abstract
  ``BaseStorage.get_value`` contract, preserving custom-storage substitution.
* **Crossing contract:** the exact data key and default enter from the wizard; the context
  adds its complete key; the storage result or failure returns through the same awaited
  call chain without transformation.

``aiogram/fsm/storage/base.py`` and concrete storages — data and read-semantics owners
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** ``FSMVALUE-009`` and ``FSMVALUE-010`` bind the read-only behavior;
  ``FSMVALUE-008`` binds value/default selection; ``FSMVALUE-012`` binds failure
  observability through the downstream seam.
* **Procedures:** downstream ``FSM_CONTEXT_GET_VALUE``, ``DISPATCH_GET_VALUE``, and
  ``BASE_STORAGE_GET_VALUE`` behavior; ``SceneWizard`` owns none of these procedures.
* **Responsibility:** ``BaseStorage.get_value`` owns polymorphic single-value lookup and
  default selection.  Memory, Redis, Mongo, and custom storages retain record ownership,
  consistency, identity encoding, serialization, backend I/O, and connection lifecycle.
* **Dependency direction:** neither ``BaseStorage`` nor any concrete backend depends on
  ``FSMContext``, ``SceneWizard``, scene management, handlers, or verification artifacts.
* **Mutation and failure authority:** no mutation port participates.  Backend read,
  serialization, and cancellation failures propagate upward under existing storage
  semantics; the scene facade does not reinterpret them.

``ScenesManager`` and ``HistoryManager`` — construction and lifecycle non-participants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Requirements:** ``FSMVALUE-009`` and ``FSMVALUE-010`` establish their exclusion from
  the lookup execution path.
* **Procedure:** constructor precondition supply for ``SCENE_WIZARD_GET_VALUE`` only.
* **Responsibility:** ``ScenesManager`` continues to construct ``SceneWizard`` with its
  already-bound ``FSMContext``.  Scene entry, exit, actions, history snapshots, rollback,
  and state transitions retain their existing owners and are not invoked by lookup.
* **Structural delta:** none.  There is no additional collaborator, lifecycle state,
  history record, event, queue, job, or configuration value.

Boundaries, flow, and failure ownership
---------------------------------------

The public contract added at the scene boundary is
``async SceneWizard.get_value(data_key: str, default: Optional[Any] = None) -> Optional[Any]``.
It mirrors ``FSMContext.get_value`` so callers do not need a new type, adapter, schema, or
protocol.  The synchronous dependency relationship contains asynchronous awaits:

.. code-block:: text

    scene caller
      -> SceneWizard.get_value(data_key, default)
      -> FSMContext.get_value(data_key, default)
      -> BaseStorage.get_value(context.key, data_key, default)
      -> configured inherited or overridden backend read
      -> unchanged result, exception, or cancellation

The caller owns invocation and cancellation.  ``SceneWizard`` owns completion only while
awaiting its context.  ``FSMContext`` owns identity binding, and storage owns the data and
read consistency.  No layer introduced by this change owns a transaction, lock, cache,
retry, timeout, compensation, recovery state, publication, subscription, or observability
event.  Existing event-isolation locking may surround the handler lifecycle in middleware,
but the accessor neither acquires nor releases that lock.

Validation seam and implementation sequence
-------------------------------------------

``tests/test_fsm/test_scene_get_value_contract.py`` owns all six focused scene-boundary
verification obligations.  Its delegation collaborator observes exact argument and result
identity; its storage-backed cases observe state and complete-data snapshots; its failing
collaborators observe unchanged exception and cancellation propagation.
``tests/test_fsm/scene_get_value_verification_map.json`` remains the bidirectional
requirement-to-verification authority.  Production modules do not depend on either test
artifact.

Implementation follows the existing dependency graph:

1. Add the one-expression asynchronous ``SceneWizard.get_value`` method beside
   ``get_data``; do not change context, storage, scene construction, or lifecycle code.
2. Replace the six focused placeholders with executable delegation, immutability, and
   failure-propagation cases, reusing existing ``FSMContext`` and ``MemoryStorage`` seams
   where persistence behavior is required.
3. Run the focused scene contract plus formatting, typing, and documentation checks.  No
   schema migration, compatibility adapter, deployment change, or staged rollout is
   required.


Markers
-------

Markers are similar to the Router event registering mechanism,
but they are used to mark scene handlers in the Scene class.

It can be imported from :code:`from aiogram.fsm.scene import on` and should be used as decorator.

Allowed event types:

- message
- edited_message
- channel_post
- edited_channel_post
- inline_query
- chosen_inline_result
- callback_query
- shipping_query
- pre_checkout_query
- poll
- poll_answer
- my_chat_member
- chat_member
- chat_join_request

Each event type can be filtered in the same way as in the Router.

Also each event type can be marked as scene entry point, exit point or leave point.

If you want to mark the scene can be entered from message or inline query,
you should use :code:`on.message` or :code:`on.inline_query` marker:

.. code-block:: python

    class MyScene(Scene, name="my_scene"):
        @on.message.enter()
        async def on_enter(self, message: types.Message):
            pass

        @on.callback_query.enter()
        async def on_enter(self, callback_query: types.CallbackQuery):
            pass


Scene has only three points for transitions:

- enter point - when user enters to the scene
- leave point - when user leaves the scene and the enter another scene
- exit point - when user exits from the scene
