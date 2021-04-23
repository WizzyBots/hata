# -*- coding: utf-8 -*-
__all__ = ('Slasher', )

from threading import current_thread

from ...backend.futures import Task, WaitTillAll
from ...backend.event_loop import EventThread
from ...backend.utils import WeakReferer

from ...discord.client_core import KOKORO
from ...discord.parsers import EventHandlerBase, InteractionEvent, Router, EventWaitforBase, asynclist
from ...discord.exceptions import DiscordException, ERROR_CODES
from ...discord.client import Client
from ...discord.preinstanced import InteractionType
from ...discord.interaction import ApplicationCommand, InteractionResponseTypes

from .utils import UNLOADING_BEHAVIOUR_DELETE, UNLOADING_BEHAVIOUR_KEEP, SYNC_ID_GLOBAL, SYNC_ID_MAIN, \
    SYNC_ID_NON_GLOBAL, RUNTIME_SYNC_HOOKS
from .command import SlashCommand

INTERACTION_TYPE_APPLICATION_COMMAND = InteractionType.application_command
INTERACTION_TYPE_MESSAGE_COMPONENT = InteractionType.message_component

def match_application_commands_to_commands(application_commands, commands, match_schema):
    """
    Matches the given application commands to slash commands.
    
    Parameters
    ----------
    application_commands : `list` of ``ApplicationCommand``
        Received application commands.
    commands : `None` or `list` of ``SlashCommand``
        A list of slash commands if any.
    match_schema : `bool`
        Whether schema or just name should be matched.
    
    Returns
    -------
    commands : `None` or `list` of ``SlashCommand``
        The remaining matched commands.
    matched : `None` or `list` of `tuple` (``ApplicationCommand``, ``SlashCommand`)
        The matched commands in pairs.
    """
    matched = None
    
    if (commands is not None):
        for application_command_index in reversed(range(len(application_commands))):
            application_command = application_commands[application_command_index]
            application_command_name = application_command.name
            
            for command_index in reversed(range(len(commands))):
                command = commands[command_index]
                
                if command.name != application_command_name:
                    continue
                
                if match_schema:
                    if (command.get_schema() != application_command):
                        continue
                
                del application_commands[application_command_index]
                del commands[command_index]
                
                if matched is None:
                    matched = []
                
                matched.append((application_command, command))
        
        if not commands:
            commands = None
    
    return commands, matched


COMMAND_STATE_IDENTIFIER_NONE = 0
COMMAND_STATE_IDENTIFIER_ADDED = 1
COMMAND_STATE_IDENTIFIER_REMOVED = 2
COMMAND_STATE_IDENTIFIER_ACTIVE = 3
COMMAND_STATE_IDENTIFIER_KEPT = 4
COMMAND_STATE_IDENTIFIER_NON_GLOBAL = 5

class CommandChange:
    """
    Represents an added or removed command inside of ``CommandState._changes``
    
    Attributes
    ----------
    added : `bool`
        Whether the command was added.
    command : ``SlashCommand``
        The command itself.
    """
    __slots__ = ('added', 'command')
    def __init__(self, added, command):
        """
        Creates a new command change instance.
        
        Parameters
        ----------
        added : `bool`
            Whether the command was added.
        command : ``SlashCommand``
            The command itself.
        """
        self.added = added
        self.command = command
    
    def __repr__(self):
        """returns the command change's representation."""
        return f'{self.__class__.__name__}(added={self.added!r}, command={self.command!r})'
    
    def __iter__(self):
        """Unpacks the command change."""
        yield self.added
        yield self.command
    
    def __len__(self):
        """Helper for unpacking."""
        return 2

class CommandState:
    """
    Represents command's state inside of a guild.
    
    Attributes
    ----------
    _active : `None` or `list` of ``SlashCommand``
        Active slash commands, which were added.
    _changes : `None` or `list` of ``CommandChange``
        Newly added or removed commands in order.
    _is_non_global : `bool`
        Whether the command state is a command state of non global commands.
    _kept : `None` or `list` of ``SlashCommand``
        Slash commands, which are removed, but should not be deleted.
    """
    __slots__ = ('_active', '_changes', '_is_non_global', '_kept', )
    def __init__(self, is_non_global):
        """
        Creates a new ``CommandState`` instance.
        """
        self._changes = None
        self._active = None
        self._kept = None
        self._is_non_global = is_non_global
    
    def __repr__(self):
        """Returns the command state's representation."""
        result = ['<', self.__class__.__name__]
        if self._is_non_global:
            result.append(' (non global)')
        
        active = self._active
        if (active is not None) and active:
            result.append(' active=[')
            
            for command in active:
                result.append(command.name)
                result.append(', ')
            
            result[-1] = ']'
            
            should_add_comma = True
        else:
            should_add_comma = False
            
        kept = self._kept
        if (kept is not None) and kept:
            if should_add_comma:
                result.append(',')
            else:
                should_add_comma = True
            
            result.append(' kept=[')
            
            for command in kept:
                result.append(command.name)
                result.append(', ')
            
            result[-1] = ']'
        
        changes = self._changes
        if (changes is not None):
            if should_add_comma:
                result.append(',')
            
            result.append(' changes=')
            result.append(repr(changes))
        
        result.append('>')
        
        return ''.join(result)
    
    def get_should_add_commands(self):
        """
        Returns the commands, which should be added.
        
        Returns
        -------
        commands : `list` of ``SlashCommand``
        """
        commands = []
        active = self._active
        if (active is not None):
            commands.extend(active)
        
        changes = self._changes
        if (changes is not None):
            for added, command in changes:
                command_name = command.name
                
                for index in range(len(commands)):
                    if commands[index].name != command_name:
                        continue
                    
                    if added:
                        commands[index] = command
                    else:
                        del commands[index]
                    
                    break
                
                else:
                    if added:
                        commands.append(command)
        
        return commands
    
    def get_should_keep_commands(self):
        """
        Returns the commands, which should be kept.
        
        Returns
        -------
        commands : `list` of ``SlashCommand``
        """
        commands = []
        kept = self._kept
        if (kept is not None):
            commands.extend(kept)
        
        changes = self._changes
        if (changes is not None):
            for command_change_state in changes:
                command_name = command_change_state.command.name
                
                for index in range(len(commands)):
                    if commands[index].name != command_name:
                        continue
                    
                    del commands[index]
                    break
        
        return commands
    
    def get_should_remove_commands(self):
        """
        Returns the commands, which should be removed.
        
        Returns
        -------
        commands : `list` of ``SlashCommand``
        """
        commands = []
        
        changes = self._changes
        if (changes is not None):
            for added, command in changes:
                command_name = command.name
                
                for index in range(len(commands)):
                    if commands[index].name != command_name:
                        continue
                
                    if added:
                        del commands[index]
                    else:
                        commands[index] = command
                    
                    break
                else:
                    if not added:
                        commands.append(command)
        
        return commands
    
    def _try_purge_from_changes(self, name):
        """
        Purges the commands with the given names from the changed ones.
        
        Parameters
        ----------
        name : `str`
            The command's name.
        
        Returns
        -------
        command : `None` or ``SlashCommand``
            The purged command if any.
        purged_from_identifier : `int`
            From which internal container was the command purged from.
            
            Can be any of the following values:
            
            +-----------------------------------+-------+
            | Respective name                   | Value |
            +===================================+=======+
            | COMMAND_STATE_IDENTIFIER_NONE     | 0     |
            +-----------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_ADDED    | 1     |
            +-----------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_REMOVED  | 2     |
            +-----------------------------------+-------+
        """
        changes = self._changes
        if (changes is not None):
            for index in range(len(changes)):
                command_change_state = changes[index]
                command = command_change_state.command
                if command.name != name:
                    continue
                
                del changes[index]
                if not changes:
                    self._changes = None
                
                if command_change_state.added:
                    purged_from_identifier = COMMAND_STATE_IDENTIFIER_ADDED
                else:
                    purged_from_identifier = COMMAND_STATE_IDENTIFIER_REMOVED
                
                return purged_from_identifier, command
        
        return None, COMMAND_STATE_IDENTIFIER_NONE
    
    def _try_purge(self, name):
        """
        Tries to purge the commands from the given name from the command state.
        
        Parameters
        ----------
        name : `str`
            The respective command's name.
        
        Returns
        -------
        command : `None` or ``SlashCommand``
            The purged command if any.
        purged_from_identifier : `int`
            From which internal container was the command purged from.
            
            Can be any of the following values:
            
            +-----------------------------------+-------+
            | Respective name                   | Value |
            +===================================+=======+
            | COMMAND_STATE_IDENTIFIER_NONE     | 0     |
            +-----------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_ADDED    | 1     |
            +-----------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_REMOVED  | 2     |
            +-----------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_ACTIVE   | 3     |
            +-----------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_KEPT     | 4     |
            +-----------------------------------+-------+
        """
        from_changes_result = self._try_purge_from_changes(name)
        
        active = self._active
        if (active is not None):
            for index in range(len(active)):
                command = active[index]
                if command.name == name:
                    del active[index]
                    if not active:
                        self._active = None
                    
                    return command, COMMAND_STATE_IDENTIFIER_ACTIVE
        
        kept = self._kept
        if (kept is not None):
            for index in range(len(kept)):
                command = kept[index]
                if command.name == name:
                    del kept[index]
                    if not kept:
                        self._kept = None
                    
                    return command, COMMAND_STATE_IDENTIFIER_KEPT
        
        return from_changes_result
    
    def activate(self, command):
        """
        Adds the command to the ``CommandState`` as active.
        
        Parameters
        ----------
        command : ``SlashCommand``
            The slash command.
        """
        if self._is_non_global:
            return
        
        self._try_purge(command.name)
        active = self._active
        if active is None:
            self._active = active = []
        
        active.append(command)
    
    def keep(self, command):
        """
        Marks the command, as it should be kept.
        
        Parameters
        ----------
        command : ``SlashCommand``
            The slash command.
        """
        if self._is_non_global:
            return
        
        self._try_purge(command.name)
        kept = self._kept
        if kept is None:
            self._kept = kept = []
        
        kept.append(command)
    
    def delete(self, command):
        """
        Deletes the command from the command state.
        
        Parameters
        ----------
        command : ``SlashCommand``
            The slash command.
        """
        if self._is_non_global:
            return
        
        self._try_purge(command.name)
    
    def add(self, command):
        """
        Adds a command to the ``CommandState``.
        
        Parameters
        ----------
        command : ``SlashCommand``
            The command to add.
        
        Returns
        -------
        command : ``SlashCommand``
            The existing command or the given one.
        
        action_identifier : `int`
            The action what took place.
            
            It's value can be any of the following:
            
            +---------------------------------------+-------+
            | Respective name                       | Value |
            +=======================================+=======+
            | COMMAND_STATE_IDENTIFIER_ADDED        | 1     |
            +---------------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_ACTIVE       | 3     |
            +---------------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_KEPT         | 4     |
            +---------------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_NON_GLOBAL   | 5     |
            +---------------------------------------+-------+
        """
        if self._is_non_global:
            existing_command, purge_identifier = self._try_purge(command.name)
            active = self._active
            if active is None:
                self._active = active = []
            
            active.append(command)
            return existing_command, COMMAND_STATE_IDENTIFIER_NON_GLOBAL
        
        kept = self._kept
        if (kept is not None):
            command_name = command.name
            
            for index in range(len(kept)):
                kept_command = kept[index]
                if kept_command.name != command_name:
                    continue
                
                if kept_command != command:
                    continue
                
                del kept[index]
                if not kept:
                    self._kept = None
                
                self._try_purge_from_changes(command_name)
                return kept_command, COMMAND_STATE_IDENTIFIER_KEPT
        
        active = self._active
        if (active is not None):
            command_name = command.name
            
            for index in range(len(active)):
                active_command = active[index]
                if active_command.name != command_name:
                    continue
                
                if active_command != command:
                    continue
                
                del active[index]
                if not active:
                    self._active = None
                
                self._try_purge_from_changes(command_name)
                return active_command, COMMAND_STATE_IDENTIFIER_ACTIVE
        
        changes = self._changes
        if changes is None:
            self._changes = changes = []
        
        change = CommandChange(True, command)
        changes.append(change)
        return command, COMMAND_STATE_IDENTIFIER_ADDED
    
    def remove(self, command, slasher_unloading_behaviour):
        """
        Removes the command from the ``CommandState``.
        
        Parameters
        ----------
        command : ``SlashCommand``
            The command to add.
        slasher_unloading_behaviour : `int`
            The parent slasher's unload behaviour.
            
            Can be any of the following:
            
            +-------------------------------+-------+
            | Respective name               | Value |
            +-------------------------------+-------+
            | UNLOADING_BEHAVIOUR_DELETE    | 0     |
            +-------------------------------+-------+
            | UNLOADING_BEHAVIOUR_KEEP      | 1     |
            +-------------------------------+-------+
        
        Returns
        -------
        command : ``SlashCommand``
            The existing command or the given one.
        action_identifier : `int`
            The action what took place.
            
            It's value can be any of the following:
            
            +---------------------------------------+-------+
            | Respective name                       | Value |
            +=======================================+=======+
            | COMMAND_STATE_IDENTIFIER_REMOVED      | 2     |
            +---------------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_ACTIVE       | 3     |
            +---------------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_KEPT         | 4     |
            +---------------------------------------+-------+
            | COMMAND_STATE_IDENTIFIER_NON_GLOBAL   | 5     |
            +---------------------------------------+-------+
        """
        unloading_behaviour = command._unloading_behaviour
        if unloading_behaviour == UNLOADING_BEHAVIOUR_DELETE:
            should_keep = False
        elif unloading_behaviour == UNLOADING_BEHAVIOUR_KEEP:
            should_keep = True
        else: # if unloading_behaviour == UNLOADING_BEHAVIOUR_INHERIT:
            if slasher_unloading_behaviour == UNLOADING_BEHAVIOUR_DELETE:
                should_keep = False
            else: # if slasher_unloading_behaviour == UNLOADING_BEHAVIOUR_KEEP:
                should_keep = True
        
        if self._is_non_global:
            existing_command, purge_identifier = self._try_purge(command.name)
            if should_keep:
                kept = self._kept
                if kept is None:
                    self._kept = kept = []
                
                kept.append(command)
            
            return existing_command, COMMAND_STATE_IDENTIFIER_NON_GLOBAL
        
        if should_keep:
            self._try_purge_from_changes(command.name)
            
            kept = self._kept
            if (kept is not None):
                command_name = command.name
                
                for index in range(len(kept)):
                    kept_command = kept[index]
                    if kept_command.name != command_name:
                        continue
                    
                    if kept_command != command:
                        continue
                    
                    return kept_command, COMMAND_STATE_IDENTIFIER_KEPT
            
            active = self._active
            if (active is not None):
                command_name = command.name
                
                for index in range(len(active)):
                    active_command = active[index]
                    if active_command.name != command_name:
                        continue
                    
                    if active_command != command:
                        continue
                    
                    del active[index]
                    if not active:
                        self._active = None
                    
                    kept = self._kept
                    if kept is None:
                        self._kept = kept = []
                    
                    kept.append(active_command)
                    return active_command, COMMAND_STATE_IDENTIFIER_ACTIVE
            
            kept = self._kept
            if kept is None:
                self._kept = kept = []
            
            kept.append(command)
            return command, COMMAND_STATE_IDENTIFIER_KEPT
        
        # We do not purge active
        kept = self._kept
        if (kept is not None):
            command_name = command.name
            
            for index in range(len(kept)):
                kept_command = kept[index]
                if kept_command.name != command_name:
                    continue
                
                if kept_command != command:
                    continue
                
                del kept[index]
                break
        
        changes = self._changes
        if changes is None:
            self._changes = changes = []
        
        change = CommandChange(False, command)
        changes.append(change)
        return command, COMMAND_STATE_IDENTIFIER_REMOVED


class Slasher(EventWaitforBase):
    """
    Slash command processor.
    
    Attributes
    ----------
    _call_later : `None` or `list` of `tuple` (`bool`, `Any`)
        Slash command changes to apply later if syncing is in progress.
    _client_reference : ``WeakReferer`` to ``Client``
        Weak reference to the parent client.
    _command_states : `dict` of (`int`, ``CommandState``) items
        The slasher's commands's states.
    
    _command_unloading_behaviour : `int`
        Behaviour to describe what should happen when a command is unloaded.
        
        Can be any of the following:
        
        +-------------------------------+-------+
        | Respective name               | Value |
        +-------------------------------+-------+
        | UNLOADING_BEHAVIOUR_DELETE    | 0     |
        +-------------------------------+-------+
        | UNLOADING_BEHAVIOUR_KEEP      | 1     |
        +-------------------------------+-------+
    
    _sync_done : `set` of `int`
        A set of guild id-s which are synced.
    _sync_permission_tasks : `dict` of (`int`, ``Task``) items
        A dictionary of `guild-id` - `permission getter` tasks.
    _sync_should : `set` of `int`
        A set of guild id-s which should be synced.
    _sync_tasks : `dict` of (`int, ``Task``) items
        A dictionary of guilds, which are in sync at the moment.
    _synced_permissions : `dict` of (`int`, `dict` of (`int`, ``ApplicationCommandPermission``) items) items
        A nested dictionary, which contains application command permission overwrites per guild_id and per command_id.
    command_id_to_command : `dict` of (`int`, ``SlashCommand``) items
        A dictionary where the keys are application command id-s and the keys are their respective command.
    waitfors : `WeakValueDictionary` of (``DiscordEntity``, `async-callable`) items
        An auto-added container to store `entity` - `async-callable` pairs.
    
    Class Attributes
    ----------------
    __event_name__ : `str` = 'interaction_create'
        Tells for the ``EventDescriptor`` that ``Slasher`` is a `interaction_create` event handler.
    SUPPORTED_TYPES : `tuple` (``SlashCommand``, )
        Tells to ``eventlist`` what exact types the ``Slasher`` accepts.
    
    Notes
    -----
    ``Slasher`` instances are weakreferable.
    """
    __slots__ = ('__weakref__', '_call_later', '_client_reference', '_command_states', '_command_unloading_behaviour',
        '_sync_done', '_sync_permission_tasks', '_sync_should', '_sync_tasks', '_synced_permissions',
        'command_id_to_command', )
    
    __event_name__ = 'interaction_create'
    
    SUPPORTED_TYPES = (SlashCommand, )
    
    def __new__(cls, client, delete_commands_on_unload=False):
        """
        Creates a new slash command processer.
        
        Parameters
        ----------
        client : ``Client``
            The owner client instance.
        delete_commands_on_unload : `bool`, Optional
            Whether commands should be deleted when unloaded.
        
        Raises
        ------
        TypeError
            - If `delete_commands_on_unload` was not given as `bool` instance.
            - If `client` was not given as ``Client`` instance.
        """
        if not isinstance(client, Client):
            raise TypeError(f'`client` can be given as `{Client.__name__}` instance, got {client.__class__.__name__}.')
        
        client_reference = WeakReferer(client)
        
        if type(delete_commands_on_unload) is bool:
            pass
        elif isinstance(delete_commands_on_unload, bool):
            delete_commands_on_unload = bool(delete_commands_on_unload)
        else:
            raise TypeError(f'`delete_commands_on_unload` can be given as `bool` instance, got '
                f'{delete_commands_on_unload.__class__.__name__}.')
        
        if delete_commands_on_unload:
            command_unloading_behaviour = UNLOADING_BEHAVIOUR_DELETE
        else:
            command_unloading_behaviour = UNLOADING_BEHAVIOUR_KEEP
        
        
        self = object.__new__(cls)
        self._call_later = None
        self._client_reference = client_reference
        self._command_unloading_behaviour = command_unloading_behaviour
        self._command_states = {}
        self._sync_tasks = {}
        self._sync_should = set()
        self._sync_done = set()
        self._sync_permission_tasks = {}
        self._synced_permissions = {}
        
        self.command_id_to_command = {}
        
        return self
    
    async def __call__(self, client, interaction_event):
        """
        Calls the slasher, processing a received interaction event.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client who received the interaction.
        interaction_event : ``InteractionEvent``
            The received interaction event.
        """
        interaction_event_type = interaction_event.type
        if interaction_event_type is INTERACTION_TYPE_APPLICATION_COMMAND:
            try:
                command = await self._try_get_command_by_id(client, interaction_event)
            except ConnectionError:
                return
            except BaseException as err:
                await client.events.error(client, f'{self!r}.__call__', err)
                return
            
            if command is not None:
                await command(client, interaction_event)
            
            return
        
        if interaction_event_type is INTERACTION_TYPE_MESSAGE_COMPONENT:
            await self.call_waitfors(client, interaction_event)
            return
    
    async def call_waitfors(self, client, interaction_event):
        """
        Calls the waiting events on components input.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client who received the interaction.
        interaction_event : ``InteractionEvent``
            The received interaction event.
        """
        try:
            waiter = interaction_event[interaction_event.message]
        except KeyError:
            return
        
        await client.http.interaction_response_message_create(interaction_event.id, interaction_event.token, {'type': InteractionResponseTypes.pong})
        
        await waiter(client, interaction_event)
    
    _run_waitfors_for = NotImplemented
    
    def __setevent__(self, func, name, description=None, show_for_invoking_user_only=None, is_global=None, guild=None,
            is_default=None, delete_on_unload=None, allow_by_default=None):
        """
        Adds a slash command.
        
        Parameters
        ----------
        func : `async-callable`
            The function used as the command when using the respective slash command.
        name : `str`, `None`, `tuple` of (`str`, `Ellipsis`, `None`)
            The command's name if applicable. If not given or if given as `None`, the `func`'s name will be use
            instead.
        description : `None`, `Any` or `tuple` of (`None`, `Ellipsis`, `Any`), Optional
            Description to use instead of the function's docstring.
        show_for_invoking_user_only : `None`, `bool` or `tuple` of (`bool`, `Ellipsis`), Optional
            Whether the response message should only be shown for the invoking user. Defaults to `False`.
        is_global : `None`, `bool` or `tuple` of (`bool`, `Ellipsis`), Optional
            Whether the slash command is global. Defaults to `False`.
        guild : `None`, ``Guild``,  `int`, (`list`, `set`) of (`int`, ``Guild``) or \
                `tuple` of (`None`, ``Guild``,  `int`, `Ellipsis`, (`list`, `set`) of (`int`, ``Guild``)), Optional
            To which guild(s) the command is bound to.
        is_default : `None`, `bool` or `tuple` of (`bool`, `Ellipsis`), Optional
            Whether the command is the default command in it's category.
        delete_on_unload : `None`, `bool` or `tuple` of (`None`, `bool`, `Ellipsis`), Optional
            Whether the command should be deleted from Discord when removed.
        allow_by_default : `None`, `bool` or `tuple` of (`None`, `bool`, `Ellipsis`), Optional
            Whether the command is enabled by default for everyone who has `use_application_commands` permission.
        
        Returns
        -------
        func : ``SlashCommand``
             The created or added command.
        
        Raises
        ------
        TypeError
            - If `show_for_invoking_user_only` was not given as `bool` instance.
            - If `global_` was not given as `bool` instance.
            - If `guild` was not given neither as `None`, ``Guild``,  `int`, (`list`, `set`) of (`int`, ``Guild``)
            - If `func` is not async callable, neither cannot be instanced to async.
            - If `func` accepts keyword only arguments.
            - If `func` accepts `*args`.
            - If `func` accepts `**kwargs`.
            - If `func` accepts less than `2` argument.
            - If `func` accepts more than `27` argument.
            - If `func`'s 0th argument is annotated, but not as ``Client``.
            - If `func`'s 1th argument is annotated, but not as ``InteractionEvent``.
            - If `name` was not given neither as `None` or `str` instance.
            - If an argument's `annotation_value` is `list` instance, but it's elements do not match the
                `tuple` (`str`, `str` or `int`) pattern.
            - If an argument's `annotation_value` is `dict` instance, but it's items do not match the
                (`str`, `str` or `int`) pattern.
            - If an argument's `annotation_value` is unexpected.
            - If an argument's `annotation` is `tuple`, but it's 1th element is neither `None` nor `str` instance.
            - If `description` or `func.__doc__` is not given or is given as `None` or empty string.
            - If `is_global` and `guild` contradicts each other.
            - If `is_default` was not given neither as `None`, `bool` or `tuple` of (`bool`, `Ellipsis`).
            - If `delete_on_unload` was not given neither as `None`, `bool` or `tuple` of (`None`, `bool`, `Ellipsis`).
            - If `allow_by_default` was not given neither as `None`, `bool` or `tuple` of (`None`, `bool`,
                `Ellipsis`).
        ValueError
            - If `guild` is or contains an integer out of uint64 value range.
            - If an argument's `annotation` is a `tuple`, but it's length is out of the expected range [0:2].
            - If an argument's `annotation_value` is `str` instance, but not any of the expected ones.
            - If an argument's `annotation_value` is `type` instance, but not any of the expected ones.
            - If an argument's `choice` amount is out of the expected range [1:25].
            - If an argument's `choice` name is duped.
            - If an argument's `choice` values are mixed types.
            - If `description` length is out of range [2:100].
            - If `guild` is given as an empty container.
            - If `name` length is out of the expected range [1:32].
        """
        if isinstance(func, Router):
            func = func[0]
        
        if isinstance(func, SlashCommand):
            self._add_command(func)
            return func
        
        command = SlashCommand(func, name, description, show_for_invoking_user_only, is_global, guild, is_default,
            delete_on_unload, allow_by_default)
        if isinstance(command, Router):
            command = command[0]
        
        self._add_command(command)
        return command
    
    def __setevent_from_class__(self, klass):
        """
        Breaks down the given class to it's class attributes and tries to add it as a slash command.
        
        Parameters
        ----------
        klass : `type`
            The class, from what's attributes the command will be created.
            
            The expected attributes of the given `klass` are the following:
            
            - description : `None`, `Any` or `tuple` of (`None`, `Ellipsis`, `Any`)
                Description of the command.
            - command : `async-callable`
                If no description was provided, then the class's `.__doc__` will be picked up.
            - guild : `None`, ``Guild``,  `int`, (`list`, `set`) of (`int`, ``Guild``) or \
                    `tuple` of (`None`, ``Guild``,  `int`, `Ellipsis`, (`list`, `set`) of (`int`, ``Guild``))
                To which guild(s) the command is bound to.
            - is_global : `None`, `bool` or `tuple` of (`bool`, `Ellipsis`)
                Whether the slash command is global. Defaults to `False`.
            - name : `str`, `None`, `tuple` of (`str`, `Ellipsis`, `None`)
                If was not defined, or was defined as `None`, the class's name will be used.
            - show_for_invoking_user_only : `None`, `bool` or `tuple` of (`bool`, `Ellipsis`)
                Whether the response message should only be shown for the invoking user. Defaults to `False`.
            - is_default : `None`, `bool` or `tuple` of (`bool`, `Ellipsis`)
                Whether the command is the default command in it's category.
            - delete_on_unload : `None`, `bool` or `tuple` of (`None`, `bool`, `Ellipsis`)
                Whether the command should be deleted from Discord when removed.
            - allow_by_default : `None`, `bool` or `tuple` of (`None`, `bool`, `Ellipsis`)
                Whether the command is enabled by default for everyone who has `use_application_commands` permission.
        
        Returns
        -------
        func : ``SlashCommand``
             The created or added command.
         
        Raises
        ------
        TypeError
            - If `klass` was not given as `type` instance.
            - If `kwargs` was not given as `None` and not all of it's items were used up.
            - If a value is routed but to a bad count amount.
            - If `show_for_invoking_user_only` was not given as `bool` instance.
            - If `global_` was not given as `bool` instance.
            - If `guild` was not given neither as `None`, ``Guild``,  `int`, (`list`, `set`) of (`int`, ``Guild``)
            - If `func` is not async callable, neither cannot be instanced to async.
            - If `func` accepts keyword only arguments.
            - If `func` accepts `*args`.
            - If `func` accepts `**kwargs`.
            - If `func` accepts less than `2` arguments.
            - If `func` accepts more than `27` arguments.
            - If `func`'s 0th argument is annotated, but not as ``Client``.
            - If `func`'s 1th argument is annotated, but not as ``InteractionEvent``.
            - If `name` was not given neither as `None` or `str` instance.
            - If an argument's `annotation_value` is `list` instance, but it's elements do not match the
                `tuple` (`str`, `str` or `int`) pattern.
            - If an argument's `annotation_value` is `dict` instance, but it's items do not match the
                (`str`, `str` or `int`) pattern.
            - If an argument's `annotation_value` is unexpected.
            - If an argument's `annotation` is `tuple`, but it's 1th element is neither `None` nor `str` instance.
            - If `description` or `func.__doc__` is not given or is given as `None` or empty string.
            - If `is_global` and `guild` contradicts each other.
            - If `is_default` was not given neither as `None`, `bool` or `tuple` of (`bool`, `Ellipsis`).
            - If `delete_on_unload` was not given neither as `None`, `bool` or `tuple` of (`None`, `bool`, `Ellipsis`).
            - If `allow_by_default` was not given neither as `None`, `bool` or `tuple` of (`None`, `bool`,
                `Ellipsis`).
        ValueError
            - If `guild` is or contains an integer out of uint64 value range.
            - If an argument's `annotation` is a `tuple`, but it's length is out of the expected range [0:2].
            - If an argument's `annotation_value` is `str` instance, but not any of the expected ones.
            - If an argument's `annotation_value` is `type` instance, but not any of the expected ones.
            - If an argument's `choice` amount is out of the expected range [1:25].
            - If an argument's `choice` name is duped.
            - If an argument's `choice` values are mixed types.
            - If `description` length is out of range [2:100].
            - If `guild` is given as an empty container.
            - If `name` length is out of the expected range [1:32].
        """
        command = SlashCommand.from_class(klass)
        if isinstance(command, Router):
            command = command[0]
        
        self._add_command(command)
        return command
    
    
    def _add_command(self, command):
        """
        Adds a slash command to the ``Slasher`` if applicable.
        
        Parameters
        ---------
        command : ``SlashCommand``
            The command to add.
        """
        if self._check_late_register(command, True):
            return
        
        self._register_slash_command(command)
        
        self._maybe_sync()
    
    def _register_slash_command(self, command):
        """
        Registers the given slash command.
        
        Parameters
        ---------
        command : ``SlashCommand``
            The command to add.
        """
        for sync_id in command._iter_sync_ids():
            if sync_id == SYNC_ID_NON_GLOBAL:
                is_non_global = True
            else:
                is_non_global = False
            
            try:
                command_state = self._command_states[sync_id]
            except KeyError:
                command_state = self._command_states[sync_id] = CommandState(is_non_global)
            
            command, change_identifier = command_state.add(command)
            if change_identifier == COMMAND_STATE_IDENTIFIER_ADDED:
                self._sync_done.discard(sync_id)
                self._sync_should.add(sync_id)
                continue
            
            if change_identifier == COMMAND_STATE_IDENTIFIER_ACTIVE:
                continue
            
            if change_identifier == COMMAND_STATE_IDENTIFIER_KEPT:
                for application_command_id in command._iter_application_command_ids():
                    self.command_id_to_command[application_command_id] = command
                continue
            
            if change_identifier == COMMAND_STATE_IDENTIFIER_NON_GLOBAL:
                continue
    
    def _remove_command(self, command):
        """
        Tries to remove the given command from the ``Slasher``.
        
        Parameters
        ----------
        command : ``Command``
            The command to remove.
        """
        if self._check_late_register(command, False):
            return
        
        self._unregister_slash_command(command)
        
        self._maybe_sync()
    
    def _unregister_slash_command(self, command):
        """
        Unregisters the given slash command.
        
        Parameters
        ----------
        command : ``Command``
            The command to remove.
        """
        for sync_id in command._iter_sync_ids():
            
            if sync_id == SYNC_ID_NON_GLOBAL:
                is_non_global = True
            else:
                is_non_global = False
            
            try:
                command_state = self._command_states[sync_id]
            except KeyError:
                command_state = self._command_states[sync_id] = CommandState(is_non_global)
            
            removed_command, change_identifier = command_state.remove(command, self._command_unloading_behaviour)
            
            if change_identifier == COMMAND_STATE_IDENTIFIER_REMOVED:
                if sync_id == SYNC_ID_NON_GLOBAL:
                    for guild_id in removed_command._iter_guild_ids():
                        self._sync_should.add(sync_id)
                        self._sync_done.discard(sync_id)
                else:
                    self._sync_should.add(sync_id)
                    self._sync_done.discard(sync_id)
                
                continue
            
            if change_identifier == COMMAND_STATE_IDENTIFIER_ACTIVE:
                for application_command_id in removed_command._iter_application_command_ids():
                    try:
                        del self.command_id_to_command[application_command_id]
                    except KeyError:
                        pass
                continue
            
            if change_identifier == COMMAND_STATE_IDENTIFIER_KEPT:
                continue
            
            if change_identifier == COMMAND_STATE_IDENTIFIER_NON_GLOBAL:
                if (removed_command is not None):
                    for guild_id in removed_command._iter_guild_ids():
                        self._sync_done.discard(guild_id)
                        self._sync_should.add(guild_id)
                continue
    
    def _check_late_register(self, command, add):
        """
        Checks whether the given command should be registered only later.
        
        command : ``Command``
            The command to register or unregister later.
        add : `bool`
            Whether the command should be registered or unregistered.
        
        Returns
        -------
        later : `bool`
            Whether the command should be registered only later
        """
        if SYNC_ID_MAIN in self._sync_tasks:
            call_later = self._call_later
            if call_later is None:
                call_later = self._call_later = []
            
            call_later.append((add, command))
            
            later = True
        else:
            later = False
        
        return later
    
    def _late_register(self):
        """
        Register late-registered commands.
        
        Returns
        -------
        registered_any : `bool`
            Whether any command was registered or unregistered.
        """
        call_later = self._call_later
        if call_later is None:
            registered_any = False
        else:
            while call_later:
                add, command = call_later.pop()
                if add:
                    self._register_slash_command(command)
                else:
                    self._unregister_slash_command(command)
            
            self._call_later = None
            registered_any = True
        
        return registered_any
    
    def __delevent__(self, func, name, **kwargs):
        """
        A method to remove a command by itself, or by it's function and name combination if defined.
        
        Parameters
        ----------
        func : ``SlashCommand``, ``Router`` of ``SlashCommand``
            The command to remove.
        name : `None` or `str`
            The command's name to remove.
        **kwargs : Keyword Arguments
            Other keyword only arguments are ignored.
        
        Raises
        ------
        TypeError
            If `func` was not given neither as ``SlashCommand`` not as ``Router`` of ``SlashCommand``.
        """
        if isinstance(func, Router):
            for sub_func in func:
                if not isinstance(sub_func, SlashCommand):
                    raise TypeError(f'`func` was not given neither as `{SlashCommand.__name__}`, or '
                        f'`{Router.__name__}` of `{SlashCommand.__name__}` instances, got {func!r}.')
            
            for sub_func in func:
                self._remove_command(sub_func)
                
        elif isinstance(func, SlashCommand):
            self._remove_command(func)
        else:
            raise TypeError(f'`func` was not given neither as `{SlashCommand.__name__}`, or `{Router.__name__}` of '
                f'`{SlashCommand.__name__}` instances, got {func!r}.')
    
    async def _try_get_command_by_id(self, client, interaction_event):
        """
        Tries to get the command by id. If found it, returns it, if not, returns `None`.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The client instance, who received the interaction event.
        interaction_event : ``InteractionEvent``
            The invoked interaction.
        """
        interaction_id = interaction_event.interaction.id
        try:
            command = self.command_id_to_command[interaction_id]
        except KeyError:
            pass
        else:
            return command
        
        # First request guild commands
        guild = interaction_event.guild
        if (guild is not None):
            guild_id = guild.id
            if not await self._sync_guild(client, guild_id):
                return None
            
            try:
                command = self.command_id_to_command[interaction_id]
            except KeyError:
                pass
            else:
                return command
        
        if not await self._sync_global(client):
            return None
        
        try:
            command = self.command_id_to_command[interaction_id]
        except KeyError:
            pass
        else:
            return command
    
    async def _sync_guild(self, client, guild_id):
        """
        Syncs the respective guild's commands if not yet synced.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        guild_id : `int`
            The guild's id to sync.
        
        Returns
        -------
        success : `bool`
            Whether syncing was successful.
        """
        if guild_id in self._sync_done:
            return True
        
        try:
            task = self._sync_tasks[guild_id]
        except KeyError:
            task = self._sync_tasks[guild_id] = Task(self._sync_guild_task(client, guild_id), KOKORO)
        
        return await task
    
    async def _sync_global(self, client):
        """
        Syncs the not yet synced global commands.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        
        Returns
        -------
        success : `bool`
            Whether syncing was successful.
        """
        if SYNC_ID_GLOBAL in self._sync_done:
            return True
        
        try:
            task = self._sync_tasks[SYNC_ID_GLOBAL]
        except KeyError:
            task = self._sync_tasks[SYNC_ID_GLOBAL] = Task(self._sync_global_task(client), KOKORO)
        
        return await task
    
    def _unregister_helper(self, command, command_state, guild_id):
        """
        Unregisters all the call relations of the given command.
        
        Parameters
        ----------
        command : `None` or ``SlashCommand``
            The slash command to unregister.
        command_state : `None` or ``CommandState``
            The command's respective state instance.
        guild_id : `int`
            The respective guild's id.
        """
        if (command is not None):
            command_id = command._pop_command_id_for(guild_id)
            if command_id:
                try:
                    del self.command_id_to_command[command_id]
                except KeyError:
                    pass
            
            if (command_state is not None):
                command_state.delete(command)
    
    def _register_helper(self, command, command_state, guild_id, application_command_id):
        """
        Registers the given command, guild id, application command relationship.
        
        Parameters
        ----------
        command : `None` or ``SlashCommand``
            The slash command to register.
        command_state : `None` or ``CommandState``
            The command's respective state instance.
        guild_id : `int`
            The respective guild's id.
        application_command_id : `int`
            The respective command's identifier.
        """
        if (command is not None):
            self.command_id_to_command[application_command_id] = command
            command._register_guild_and_application_command_id(guild_id, application_command_id)
            if (command_state is not None):
                command_state.activate(command)
    
    def _keep_helper(self, command, command_state, guild_id):
        """
        Marks the given command to be kept at the given guild.
        
        Parameters
        ----------
        command : `None` or ``SlashCommand``
            The slash command to register.
        command_state : `None` or ``CommandState``
            The command's respective state instance.
        guild_id : `int`
            The respective guild's id.
        """
        if (command is not None):
            command_id = command._pop_command_id_for(guild_id)
            if command_id:
                try:
                    del self.command_id_to_command[command_id]
                except KeyError:
                    pass
            
            if (command_state is not None):
                command_state.keep(command)
    
    async def _sync_guild_task(self, client, guild_id):
        """
        Syncs the respective guild's commands.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        guild_id : `int`
            The guild's id to sync.
        
        Returns
        -------
        success : `bool`
            Whether syncing was successful.
        """
        success = False
        
        try:
            application_commands = await client.application_command_guild_get_all(guild_id)
        except BaseException as err:
            # No internet connection
            if not isinstance(err, ConnectionError):
                await client.events.error(client, f'{self!r}._sync_guild_task', err)
        else:
            guild_command_state = self._command_states.get(guild_id, None)
            if guild_command_state is None:
                guild_added_commands = None
                guild_keep_commands = None
                guild_removed_commands = None
            else:
                guild_added_commands = guild_command_state.get_should_add_commands()
                if not guild_added_commands:
                    guild_added_commands = None
                
                guild_keep_commands = guild_command_state.get_should_keep_commands()
                if not guild_keep_commands:
                    guild_keep_commands = None
                
                guild_removed_commands = guild_command_state.get_should_remove_commands()
                if not guild_removed_commands:
                    guild_removed_commands = None
            
            non_global_command_state = self._command_states.get(SYNC_ID_NON_GLOBAL, None)
            if non_global_command_state is None:
                non_global_added_commands = None
                non_global_keep_commands = None
            else:
                non_global_added_commands = non_global_command_state.get_should_add_commands()
                if not non_global_added_commands:
                    non_global_added_commands = None
                
                non_global_keep_commands = non_global_command_state.get_should_keep_commands()
                if not non_global_keep_commands:
                    non_global_keep_commands = None
            
            command_create_callbacks = None
            command_edit_callbacks = None
            command_delete_callbacks = None
            command_register_callbacks = None
            
            guild_added_commands, matched = match_application_commands_to_commands(application_commands,
                guild_added_commands, True)
            if (matched is not None):
                for application_command, command in matched:
                    callback = (type(self)._register_command, self, client, command, guild_command_state, guild_id,
                        application_command)
                    
                    if command_register_callbacks is None:
                        command_register_callbacks = []
                    command_register_callbacks.append(callback)
            
            non_global_added_commands, matched = match_application_commands_to_commands(application_commands,
                non_global_added_commands, True)
            if (matched is not None):
                for application_command, command in matched:
                    callback = (type(self)._register_command, self, client, command, non_global_command_state, guild_id,
                        application_command)
                    
                    if command_register_callbacks is None:
                        command_register_callbacks = []
                    command_register_callbacks.append(callback)
            
            guild_added_commands, matched = match_application_commands_to_commands(application_commands,
                guild_added_commands, False)
            if (matched is not None):
                for application_command, command in matched:
                    callback = (type(self)._edit_command, self, client, command, guild_command_state, guild_id,
                        application_command,)
                    
                    if command_edit_callbacks is None:
                        command_edit_callbacks = []
                    command_edit_callbacks.append(callback)
            
            non_global_added_commands, matched = match_application_commands_to_commands(application_commands,
                non_global_added_commands, False)
            if (matched is not None):
                for application_command, command in matched:
                    callback = (type(self)._edit_guild_command_to_non_global, self, client, command,
                        non_global_command_state, guild_id, application_command)
                    if command_edit_callbacks is None:
                        command_edit_callbacks = []
                    command_edit_callbacks.append(callback)
            
            guild_keep_commands, matched = match_application_commands_to_commands(application_commands,
                guild_keep_commands, True)
            if (matched is not None):
                for application_command, command in matched:
                    self._keep_helper(command, guild_command_state, guild_id)
            
            non_global_keep_commands, matched = match_application_commands_to_commands(application_commands,
                non_global_keep_commands, True)
            if (matched is not None):
                for application_command, command in matched:
                    self._keep_helper(command, non_global_command_state, guild_id)
            
            guild_removed_commands, matched = match_application_commands_to_commands(application_commands,
                guild_removed_commands, True)
            if (matched is not None):
                for application_command, command in matched:
                    callback = (type(self)._delete_command, self, client, command, guild_command_state, guild_id,
                        application_command)
                    if command_delete_callbacks is None:
                        command_delete_callbacks = []
                    command_delete_callbacks.append(callback)
            
            if (guild_added_commands is not None):
                while guild_added_commands:
                    command = guild_added_commands.pop()
                    
                    callback = (type(self)._create_command, self, client, command, guild_command_state, guild_id)
                    if command_create_callbacks is None:
                        command_create_callbacks = []
                    command_create_callbacks.append(callback)
                    continue
            
            while application_commands:
                application_command = application_commands.pop()
                
                callback = (type(self)._delete_command, self, client, None, None, guild_id, application_command)
                if command_delete_callbacks is None:
                    command_delete_callbacks = []
                command_delete_callbacks.append(callback)
            
            success = True
            for callbacks in (command_register_callbacks, command_delete_callbacks, command_edit_callbacks, \
                    command_create_callbacks):
                if (callbacks is not None):
                    done, pending = await WaitTillAll(
                        [Task(callback[0](*callback[1:]), KOKORO) for callback in callbacks],
                        KOKORO)
                    
                    for future in done:
                        if not future.result():
                            success = False
        
        finally:
            try:
                del self._sync_tasks[guild_id]
            except KeyError:
                pass
        
        if success:
            self._sync_should.discard(guild_id)
            self._sync_done.add(guild_id)
        
        return success
    
    async def _sync_global_task(self, client):
        """
        Syncs the global commands off the ``Slasher``.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        
        Returns
        -------
        success : `bool`
            Whether the commands where synced with success.
        """
        success = False
        try:
            application_commands = await client.application_command_global_get_all()
        except BaseException as err:
            # No internet connection
            if not isinstance(err, ConnectionError):
                await client.events.error(client, f'{self!r}._sync_global_commands', err)
            
        else:
            global_command_state = self._command_states.get(SYNC_ID_GLOBAL, None)
            if global_command_state is None:
                global_added_commands = None
                global_keep_commands = None
                global_removed_commands = None
            else:
                global_added_commands = global_command_state.get_should_add_commands()
                if not global_added_commands:
                    global_added_commands = None
                
                global_keep_commands = global_command_state.get_should_keep_commands()
                if not global_keep_commands:
                    global_keep_commands = None
                
                global_removed_commands = global_command_state.get_should_remove_commands()
                if not global_removed_commands:
                    global_removed_commands = None
            
            command_create_callbacks = None
            command_edit_callbacks = None
            command_delete_callbacks = None
            command_register_callbacks = None
            
            global_added_commands, matched = match_application_commands_to_commands(application_commands,
                global_added_commands, True)
            if (matched is not None):
                for application_command, command in matched:
                    callback = (type(self)._register_command, self, client, command, global_command_state,
                        SYNC_ID_GLOBAL, application_command)
                    
                    if command_register_callbacks is None:
                        command_register_callbacks = []
                    command_register_callbacks.append(callback)
            
            global_keep_commands, matched = match_application_commands_to_commands(application_commands,
                global_keep_commands, True)
            if (matched is not None):
                for application_command, command in matched:
                    self._keep_helper(command, global_command_state, SYNC_ID_GLOBAL)
            
            global_removed_commands, matched = match_application_commands_to_commands(application_commands,
                global_removed_commands, True)
            if (matched is not None):
                for application_command, command in matched:
                    callback = (type(self)._delete_command, self, client, command, global_command_state, SYNC_ID_GLOBAL,
                        application_command)
                    if command_delete_callbacks is None:
                        command_delete_callbacks = []
                    command_delete_callbacks.append(callback)
            
            if (global_added_commands is not None):
                while global_added_commands:
                    command = global_added_commands.pop()
                    
                    callback = (type(self)._create_command, self, client, command, global_command_state, SYNC_ID_GLOBAL)
                    if command_create_callbacks is None:
                        command_create_callbacks = []
                    command_create_callbacks.append(callback)
            
            while application_commands:
                application_command = application_commands.pop()
                
                callback = (type(self)._delete_command, self, client, None, None, SYNC_ID_GLOBAL, application_command)
                if command_delete_callbacks is None:
                    command_delete_callbacks = []
                command_delete_callbacks.append(callback)
            
            success = True
            for callbacks in (command_register_callbacks, command_delete_callbacks, command_edit_callbacks,
                    command_create_callbacks):
                if (callbacks is not None):
                    done, pending = await WaitTillAll(
                        [Task(callback[0](*callback[1:]), KOKORO) for callback in callbacks],
                        KOKORO)
                    
                    for future in done:
                        if not future.result():
                            success = False
        
        finally:
            try:
                del self._sync_tasks[SYNC_ID_GLOBAL]
            except KeyError:
                pass
        
        if success:
            self._sync_should.discard(SYNC_ID_GLOBAL)
            self._sync_done.add(SYNC_ID_GLOBAL)
        
        return success
    
    async def _register_command(self, client, command, command_state, guild_id, application_command):
        """
        Finishes registering the command.
        
        This method is a coroutine.
        
        Attributes
        ----------
        client : ``Client``
            The respective client.
        command : ``SlashCommand``
            The non_global command what replaced the slash command.
        command_state : ``CommandState``
            The command's command state.
        guild_id : `int`
            The respective guild's identifier where the command is.
        application_command : ``ApplicationCommand``
            The respective application command.
        
        Returns
        -------
        success : `bool`
            Whether the command was registered successfully.
        """
        if guild_id == SYNC_ID_GLOBAL:
            tasks = []
            for permission_guild_id in command._get_sync_permission_ids():
                task = Task(self._register_command_task(client, command, permission_guild_id, application_command),
                    KOKORO)
                task.append(task)
            
            if tasks:
                await WaitTillAll(tasks, KOKORO)
                
                success = True
                for future in tasks:
                    if not future.result():
                        success = False
                
                if not success:
                    return False
        else:
            await self._register_command_task(client, command, guild_id, application_command)
        
        self._register_helper(command, command_state, guild_id, application_command.id)
        return True
    
    async def _register_command_task(self, client, command, guild_id, application_command):
        """
        Syncs a command's permissions inside of a guild.
        
        This method is a coroutine.
        
        Attributes
        ----------
        client : ``Client``
            The respective client.
        command : ``SlashCommand``
            The non_global command what replaced the slash command.
        guild_id : `int`
            The respective guild's identifier where the command is.
        application_command : ``ApplicationCommand``
            The respective application command.
        
        Returns
        -------
        success : `bool`
            Whether the command was registered successfully.
        """
        success, permission = await self._get_permission_for(client, guild_id, application_command.id)
        if not success:
            return False
        
        overwrites = command.get_overwrites_for(guild_id)
        
        if permission is None:
            current_overwrites = None
        else:
            current_overwrites = permission.overwrites
        
        if overwrites != current_overwrites:
            try:
                permission = await client.application_command_permission_edit(guild_id, application_command, overwrites)
            except BaseException as err:
                if not isinstance(err, ConnectionError):
                    await client.events.error(client, f'{self!r}._register_command', err)
                return False
            
            try:
                per_guild = self._synced_permissions[guild_id]
            except KeyError:
                per_guild = self._synced_permissions[guild_id] = {}
            
            per_guild[permission.application_command_id] = permission
        
        return True
    
    async def _edit_guild_command_to_non_global(self, client, command, command_state, guild_id, application_command):
        """
        Edits the given guild command ot a non local one.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        command : ``SlashCommand``
            The non_global command what replaced the slash command.
        command_state : ``CommandState``
            The command's command state.
        guild_id : `int`
            The respective guild's identifier where the command is.
        application_command : ``ApplicationCommand``
            The respective application command.
        
        Returns
        -------
        success : `bool`
            Whether the command was updated successfully.
        """
        try:
            application_command = await client.application_command_guild_edit(guild_id, application_command,
                command.get_schema())
        except BaseException as err:
            if isinstance(err, ConnectionError):
                return False
            
            if isinstance(err, DiscordException) and (err.code == ERROR_CODES.unknown_application_command):
                # no command, no problem, lol
                return True
            
            await client.events.error(client, f'{self!r}._edit_guild_command_to_non_global', err)
            return False
        
        return await self._register_command(client, command, command_state, guild_id, application_command)
    
    async def _edit_command(self, client, command, command_state, guild_id, application_command):
        """
        Updates the given guild bound application command.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        command : ``SlashCommand``
            The slash command to update the application command to.
        command_state : ``CommandState``
            The command's command state.
        guild_id : `int`
            The respective guild's identifier where the command is.
        application_command : ``ApplicationCommand``
            The respective application command.
        
        Returns
        -------
        success : `bool`
            Whether the command was updated successfully.
        """
        try:
            schema = command.get_schema()
            if guild_id == SYNC_ID_GLOBAL:
                coroutine = client.application_command_global_edit(application_command, schema)
            else:
                coroutine = client.application_command_guild_edit(guild_id, application_command, schema)
            await coroutine
        except BaseException as err:
            if isinstance(err, ConnectionError):
                # No internet connection
                return False
            
            if isinstance(err, DiscordException) and err.code == ERROR_CODES.unknown_application_command:
                # Already deleted, lul, add it back!
                self._unregister_helper(command, command_state, guild_id)
                return await self._create_command(client, command, command_state, guild_id)
            
            await client.events.error(client, f'{self!r}._edit_command', err)
            return False
        
        return await self._register_command(client, command, command_state, guild_id, application_command)
    
    async def _delete_command(self, client, command, command_state, guild_id, application_command):
        """
        Deletes the given guild bound command.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        command : `None` or ``SlashCommand``
            The slash command to delete.
        command_state : ``CommandState``
            The command's command state.
        guild_id : `int`
            The respective guild's identifier where the command is.
        application_command : ``ApplicationCommand``
            The respective application command.
        
        Returns
        -------
        success : `bool`
            Whether the command was deleted successfully.
        """
        try:
            if guild_id == SYNC_ID_GLOBAL:
                coroutine = client.application_command_global_delete(application_command)
            else:
                coroutine = client.application_command_guild_delete(guild_id, application_command)
            await coroutine
        except BaseException as err:
            if isinstance(err, ConnectionError):
                # No internet connection
                return False
            
            if isinstance(err, DiscordException) and err.code == ERROR_CODES.unknown_application_command:
                # Already deleted, lul, ok, I guess.
                pass
            else:
                await client.events.error(client, f'{self!r}._delete_command', err)
                return False
        
        self._unregister_helper(command, command_state, guild_id)
        return True
    
    async def _create_command(self, client, command, command_state, guild_id):
        """
        Creates a given guild bound command.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        command : `None` or ``SlashCommand``
            The slash command to create.
        command_state : ``CommandState``
            The command's command state.
        guild_id : `int`
            The respective guild's identifier where the command is.
        
        Returns
        -------
        success : `bool`
            Whether the command was created successfully.
        """
        try:
            schema = command.get_schema()
            if guild_id == SYNC_ID_GLOBAL:
                coroutine = client.application_command_global_create(schema)
            else:
                coroutine = client.application_command_guild_create(guild_id, schema)
            application_command = await coroutine
        except BaseException as err:
            if isinstance(err, ConnectionError):
                # No internet connection
                return False
            
            await client.events.error(client, f'{self!r}._create_command', err)
            return False
        
        return await self._register_command(client, command, command_state, guild_id, application_command)
    
    def sync(self):
        """
        Syncs the slash commands with the client.
        
        The return of the method depends on the thread, from which it was called from.
        
        Returns
        -------
        task : `bool`, ``Task`` or ``FutureAsyncWrapper``
            - If the method was called from the client's thread (KOKORO), then returns a ``Task``. The task will return
                `True`, if syncing was successful.
            - If the method was called from an ``EventThread``, but not from the client's, then returns a
                ``FutureAsyncWrapper``. The task will return `True`, if syncing was successful.
            - If the method was called from any other thread, then waits for the syncing task to finish and returns
                `True`, if it was successful.
        
        Raises
        ------
        RuntimeError
            The slasher's client was already garbage collected.
        """
        client = self._client_reference()
        if client is None:
            raise RuntimeError('The slasher\'s client was already garbage collected.')
        
        task = Task(self._do_main_sync(client), KOKORO)
        
        thread = current_thread()
        if thread is KOKORO:
            return task
        
        if isinstance(thread, EventThread):
            # `.async_wrap` wakes up KOKORO
            return task.async_wrap(thread)
        
        KOKORO.wake_up()
        return task.sync_wrap().wait()
    
    async def _do_main_sync(self, client):
        """
        Syncs the slash commands with the client. This method is the internal method of ``.sync``.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        
        Returns
        -------
        success : `bool`
            Whether the sync was successful.
        """
        if not self._sync_should:
            return True
        
        try:
            task = self._sync_tasks[SYNC_ID_MAIN]
        except KeyError:
            task = self._sync_tasks[SYNC_ID_MAIN] = Task(self._do_main_sync_task(client), KOKORO)
        
        return await task
    
    
    async def _do_main_sync_task(self, client):
        """
        Syncs the slash commands with the client. This method is the internal coroutine of the ``._do_main_sync``
        method.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        
        Returns
        -------
        success : `bool`
            Whether the sync was successful.
        """
        try:
            while True:
                try:
                    tasks = []
                    for guild_id in self._sync_should:
                        if guild_id == SYNC_ID_GLOBAL:
                            coro = self._sync_global(client)
                        else:
                            coro = self._sync_guild(client, guild_id)
                        
                        task = Task(coro, KOKORO)
                        tasks.append(task)
                    
                    if tasks:
                        done, pending = await WaitTillAll(tasks, KOKORO)
                        
                        success = True
                        for future in done:
                            if not future.result():
                                success = False
                    else:
                        success = True
                except:
                    self._late_register()
                    raise
                else:
                    if self._late_register(): # Make sure this is called
                        if success:
                            continue
                    
                    return success
        
        finally:
            try:
                del self._sync_tasks[SYNC_ID_MAIN]
            except KeyError:
                pass
    
    def _maybe_register_guild_command(self, application_command, guild_id):
        """
        Tries to register the given non-global application command to the slasher.
        
        Parameters
        ----------
        application_command : ``ApplicationCommand``
            A just added application command.
        guild_id : `int`
            The respective guild's identifier.
        """
        try:
            non_global_command_state = self._command_states[SYNC_ID_NON_GLOBAL]
        except KeyError:
            return
        
        for command in non_global_command_state.get_should_add_commands():
            if command.get_schema() == application_command:
                self._register_helper(command, non_global_command_state, guild_id, application_command.id)
                break
    
    def _maybe_unregister_guild_command(self, application_command, guild_id):
        """
        Tries to unregister the given non-global application command from the slasher.
        
        Parameters
        ----------
        application_command : ``ApplicationCommand``
            A just deleted application command.
        guild_id : `int`
            The respective guild's identifier.
        """
        try:
            non_global_command_state = self._command_states[SYNC_ID_NON_GLOBAL]
        except KeyError:
            return
        
        for command in non_global_command_state.get_should_add_commands():
            if command.get_schema() == application_command:
                self._unregister_helper(command, non_global_command_state, guild_id)
                break
    
    def __repr__(self):
        """Returns the slasher's representation."""
        return f'<{self.__class__.__name__} sync_should={len(self._sync_should)}, sync_done={len(self._sync_done)}>'
    
    @property
    def delete_commands_on_unload(self):
        """
        A get-set property for changing the slasher's command unloading behaviour.
        
        Accepts and returns any `bool` instance.
        """
        command_unloading_behaviour = self._command_unloading_behaviour
        if command_unloading_behaviour == UNLOADING_BEHAVIOUR_DELETE:
            delete_commands_on_unload = True
        else:
            delete_commands_on_unload = False
        
        return delete_commands_on_unload
    
    @delete_commands_on_unload.setter
    def delete_commands_on_unload(self, delete_commands_on_unload):
        if type(delete_commands_on_unload) is bool:
            pass
        elif isinstance(delete_commands_on_unload, bool):
            delete_commands_on_unload = bool(delete_commands_on_unload)
        else:
            raise TypeError(f'`delete_commands_on_unload` can be given as `bool` instance, got '
                f'{delete_commands_on_unload.__class__.__name__}.')
        
        if delete_commands_on_unload:
            command_unloading_behaviour = UNLOADING_BEHAVIOUR_DELETE
        else:
            command_unloading_behaviour = UNLOADING_BEHAVIOUR_KEEP
        
        self._command_unloading_behaviour = command_unloading_behaviour
    
    
    def _maybe_store_application_command_permission(self, permission):
        """
        Stores an application command's new permissions if needed.
        
        Parameters
        ----------
        permission : ``ApplicationCommandPermission``
            The updated application command's permissions.
        """
        try:
            tracked_guild = self._synced_permissions[permission.guild_id]
        except KeyError:
            return
        
        tracked_guild[permission.application_command_id] = permission
    
    async def _get_permission_for(self, client, guild_id, application_command_id):
        """
        Gets the permissions for the given application command in the the respective guild.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        guild_id : `int`
            The respective guild's identifier where the command is.
        application_command_id : `int`
            The respective application command's identifier.
        """
        try:
            per_guild = self._synced_permissions[guild_id]
        except KeyError:
            pass
        else:
            return True, per_guild.get(application_command_id, None)
        
        try:
            sync_permission_task = self._sync_permission_tasks[guild_id]
        except KeyError:
            sync_permission_task = Task(self._sync_permission_task(client, guild_id), KOKORO)
            self._sync_permission_tasks[guild_id] = sync_permission_task
        
        success, per_guild = await sync_permission_task
        if success:
            permission = per_guild.get(application_command_id, None)
        else:
            permission = None
        
        return success, permission
    
    async def _sync_permission_task(self, client, guild_id):
        """
        Syncs the respective guild's permissions.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The respective client.
        guild_id : `int`
            The guild's id to sync.
        
        Returns
        -------
        success : `bool`
            Whether syncing was successful.
        per_guild : `None` or `dict` of (`int`, ``ApplicationCommandPermission``) items
            The application command permission for the respective guild. If `success` is `False, this value is
            returned as `None`.
        """
        try:
            try:
                permissions = await client.application_command_permission_get_all_guild(guild_id)
            except BaseException as err:
                if not isinstance(err, ConnectionError):
                    await client.events.error(client, f'{self!r}._sync_permission_task', err)
                
                return False, None
            else:
                try:
                    per_guild = self._synced_permissions[guild_id]
                except KeyError:
                    per_guild = self._synced_permissions[guild_id] = {}
                
                for permission in permissions:
                    per_guild[permission.application_command_id] = permission
                
                return True, per_guild
        finally:
            try:
                del self._sync_permission_tasks[guild_id]
            except KeyError:
                pass
    
    def _maybe_sync(self):
        """
        Syncs the slasher runtime if required.
        """
        client = self._client_reference()
        if client is None:
            raise RuntimeError('The slasher\'s client was already garbage collected.')
        
        for sync_hook in RUNTIME_SYNC_HOOKS:
            if not sync_hook(client):
                return
        
        Task(self._do_main_sync(client), KOKORO)
