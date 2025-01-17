__all__ = ('ApplicationCommand',)


from ...bases import DiscordEntity
from ...core import APPLICATION_COMMANDS, GUILDS
from ...localizations.helpers import localized_dictionary_builder
from ...localizations.utils import build_locale_dictionary, destroy_locale_dictionary
from ...permission import Permission
from ...preconverters import preconvert_preinstanced_type
from ...utils import DATETIME_FORMAT_CODE, id_to_datetime, is_valid_application_command_name

from .application_command_option import ApplicationCommandOption
from .constants import (
    APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX, APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN,
    APPLICATION_COMMAND_NAME_LENGTH_MAX, APPLICATION_COMMAND_NAME_LENGTH_MIN, APPLICATION_COMMAND_OPTIONS_MAX
)
from .helpers import apply_translation_into
from .preinstanced import APPLICATION_COMMAND_CONTEXT_TARGET_TYPES, ApplicationCommandTargetType



def _debug_application_command_description(description):
    """
    Runs debug only checks on application command description.
    
    Parameters
    ----------
    description : `None, `str`
        The description to run checks on.
    
    Raises
    ------
    AssertionError
        Any checks failed.
    """
    if (description is not None):
        if not isinstance(description, str):
            raise AssertionError(
                f'`description` can be `None`, `str`, got {description.__class__.__name__}; {description!r}.'
            )
        
        description_length = len(description)
        if (
            description_length < APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN or
            description_length > APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX
        ):
            raise AssertionError(
                f'`description` length can be in range '
                f'[{APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN}:{APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX}], '
                f'got {description_length!r}; {description!r}.'
            )


class ApplicationCommand(DiscordEntity, immortal=True):
    """
    Represents a Discord slash command.
    
    Attributes
    ----------
    id : `int`
        The application command's id.
    
    allow_by_default : `bool`
        Whether the command is enabled by default for everyone who has `use_application_commands` permission.
    
    application_id : `int`
        The application command's application's id.
    
    description : `None`, `str`
        The command's description. It's length can be in range [2:100].
        
        Set as `None` for context commands.
    
    description_localizations : `None`, `dict` of (``Locale``, `str`) items
        Localized descriptions of the application command.
        
        Set as `None` for context commands.
    
    guild_id : `int`
        The guild's identifier to which the command is bound to.
        
        Set as `0` if the command is global.
    
    name : `str`
        The name of the command. It's length can be in range [1:32].
    
    name_localizations : `None`, `dict` of (``Locale``, `str`) items
        Localized names of the application command.
    
    options : `None`, `list` of ``ApplicationCommandOption``
        The parameters of the command. It's length can be in range [0:25]. If would be set as empty list, instead is
        set as `None`.
    
    required_permissions : `None`, ``Permission``
        The required permissions to use the application command inside of a guild.
    
    target_type : ``ApplicationCommandTargetType``
        The application command target's type describing where it shows up.
    
    version : `int`
        The time when the command was last edited in snowflake.
    
    Notes
    -----
    ``ApplicationCommand``s are weakreferable.
    """
    __slots__ = (
        'allow_by_default', 'application_id', 'description', 'description_localizations', 'guild_id', 'name',
        'name_localizations', 'options', 'required_permissions', 'target_type', 'version'
    )
    
    def __new__(cls, name, description=None, *, allow_by_default=True, description_localizations=None,
            name_localizations=None, options=None, required_permissions=None, target_type=None):
        """
        Creates a new ``ApplicationCommand`` with the given parameters.
        
        Parameters
        ----------
        name : `str`
            The name of the command. It's length can be in range [1:32].
        
        description : `None`, `str` = `None`, Optional
            The command's description. It's length can be in range [2:100].
            
            Defaults to the `name` parameter if not given.
        
        allow_by_default : `None`, `bool` = `None`, Optional (Keyword only)
            Whether the command is enabled by default for everyone who has `use_application_commands` permission.
            
            Defaults to `True`.
        
        description_localizations : `None`, `dict` of ((`str`, ``Locale``), `str`) items,
                (`list`, `set`, `tuple`) of `tuple` ((`str`, ``Locale``), `str`) = `None`, Optional (Keyword only)
            Localized descriptions of the application command.
        
        name_localizations : `None`, `dict` of ((`str`, ``Locale``), `str`) items,
                (`list`, `set`, `tuple`) of `tuple` ((`str`, ``Locale``), `str`) = `None`, Optional (Keyword only)
            Localized names of the application command.
        
        options : `None`, (`list`, `tuple`) of ``ApplicationCommandOption`` = `None`, Optional (Keyword only)
            The parameters of the command. It's length can be in range [0:25].
        
        required_permissions : `None`, ``Permission``, `int` = `None`, Optional (Keyword only)
            The required permissions to use the application command inside of a guild.
            
            If given as non-null value, turns off `allow_by_default` to `False` by default.
        
        target_type : `None`, `int`, ``ApplicationCommandTargetType`` = `None`, Optional (Keyword only)
            The application command's target type.
            
            Defaults to `ApplicationCommandTargetType.chat`.
        
        Raises
        ------
        TypeError
            - If `target_type` is neither `int`, nor ``ApplicationCommandTargetType``.
            - If `name_localizations`'s or any of it's item's type is incorrect.
            - If `description_localizations`'s or any of it's item's type is incorrect.
        ValueError
            - If `name_localizations` has an item with incorrect structure.
            - If `description_localizations` has an item with incorrect structure.
        AssertionError
            - If `name` was not given as `str`.
            - If `name` length is out of range [1:32].
            - If `name` contains unexpected character.
            - If `description` was not given as `None` nor `str`.
            - If `description` length is out of range [1:100].
            - If `options` was not given neither as `None` nor as (`list`, `tuple`) of ``ApplicationCommandOption``
                instances.
            - If `options`'s length is out of range [0:25].
            - If `allow_by_default` was not given as `bool`.
        """
        # id
        # Internal attribute
        
        # allow_by_default
        if (allow_by_default is None):
            allow_by_default = True
        
        else:
            if __debug__:
                if not isinstance(allow_by_default, bool):
                    raise AssertionError(
                        f'`allow_by_default` can be `bool`, got {allow_by_default.__class__.__name__}; '
                        f'{allow_by_default!r}.'
                    )
        
        # description
        if __debug__:
            _debug_application_command_description(description)
        
        # description_localizations
        description_localizations = localized_dictionary_builder(description_localizations, 'description_localizations')
        
        # name
        if __debug__:
            if not isinstance(name, str):
                raise AssertionError(
                    f'`name` can be `str`, got {name.__class__.__name__}; {name!r}.'
                )
            
            name_length = len(name)
            if (
                name_length < APPLICATION_COMMAND_NAME_LENGTH_MIN or
                name_length > APPLICATION_COMMAND_NAME_LENGTH_MAX
            ):
                raise AssertionError(
                    f'`name` length can be in range '
                    f'[{APPLICATION_COMMAND_NAME_LENGTH_MIN}:{APPLICATION_COMMAND_NAME_LENGTH_MAX}], got '
                    f'{name_length!r}; {name!r}.'
                )
            
            if not is_valid_application_command_name(name):
                raise AssertionError(
                    f'`name` contains an unexpected character, got {name!r}.'
                )
        
        # name_localizations
        name_localizations = localized_dictionary_builder(name_localizations, 'name_localizations')
        
        # options
        if options is None:
            options_processed = None
        else:
            if __debug__:
                if not isinstance(options, (tuple, list)):
                    raise AssertionError(
                        f'`options` can be `None`, (`list`, `tuple`) of `{ApplicationCommandOption.__name__}`, '
                        f'got {options.__class__.__name__}; {options!r}.')
            
            # Copy it
            options_processed = list(options)
            if options_processed:
                if __debug__:
                    if len(options_processed) > APPLICATION_COMMAND_OPTIONS_MAX:
                        raise AssertionError(
                            f'`options` length can be in range '
                            f'[0:{APPLICATION_COMMAND_OPTIONS_MAX}], got {len(options_processed)!r}; {options!r}'
                        )
                    
                    for index, option in enumerate(options_processed):
                        if not isinstance(option, ApplicationCommandOption):
                            raise AssertionError(
                                f'`options[{index!r}]` is not `{ApplicationCommandOption.__name__}`, got '
                                f'{option.__class__.__name__}; {option!r}; options={options!r}.'
                            )
            
            else:
                options_processed = None
        
        # required_permissions
        if (required_permissions is None):
            pass
        elif isinstance(required_permissions, int):
            required_permissions = Permission(required_permissions)
        
        else:
            raise TypeError(
                f'`required_permissions` can be `None`, `{Permission.__name__}`, `int`, got '
                f'{required_permissions.__class__.__name__}; {required_permissions!r}.'
            )
        
        # target_type
        if target_type is None:
            target_type = ApplicationCommandTargetType.chat
        else:
            target_type = preconvert_preinstanced_type(target_type, 'target_type', ApplicationCommandTargetType)
        
        
        # Post checks
        if (target_type in APPLICATION_COMMAND_CONTEXT_TARGET_TYPES):
            # Context commands cannot have description and options, so we clear them.
            description = None
            description_localizations = None
            options_processed = None
        
        else:
            # For non context commands description is required.
            if (description is None):
                description = name
                if __debug__:
                    _debug_application_command_description(description)
        
        
        self = object.__new__(cls)
        
        self.id = 0
        self.application_id = 0
        self.name = name
        self.name_localizations = name_localizations
        self.description = description
        self.description_localizations = description_localizations
        self.guild_id = 0
        self.allow_by_default = allow_by_default
        self.options = options_processed
        self.required_permissions = required_permissions
        self.target_type = target_type
        self.version = 0
        
        return self
    
    
    def add_option(self, option):
        """
        Adds a new option to the application command.
        
        Parameters
        ----------
        option : ``ApplicationCommandOption``
            The option to add.
        
        Returns
        -------
        self : ``ApplicationCommand``
        
        Raises
        ------
        AssertionError
            - If the entity is not partial.
            - If `option` is not ``ApplicationCommandOption``.
            - If the ``ApplicationCommand`` has already `25` options.
        """
        if __debug__:
            if not self.partial:
                raise AssertionError(
                    f'{self.__class__.__name__}.add_option` can be only called on partial '
                    f'`{self.__class__.__name__}`-s, but was called on {self!r}.'
                )
            
            if not isinstance(option, ApplicationCommandOption):
                raise AssertionError(
                    f'`option` can be `{ApplicationCommandOption.__name__}`, got '
                    f'{option.__class__.__name__}; {option!r}.'
                )
        
        options = self.options
        if options is None:
            self.options = options = []
        else:
            if __debug__:
                if len(options) >= APPLICATION_COMMAND_OPTIONS_MAX:
                    raise AssertionError(
                        f'`option` cannot be added if the `{ApplicationCommandOption.__name__}` has '
                        f'already `{APPLICATION_COMMAND_OPTIONS_MAX}` options.'
                    )
        
        options.append(option)
        return self
    
    
    @classmethod
    def _create_empty(cls, application_command_id, application_id):
        """
        Creates an empty application command with the default attributes set.
        
        Parameters
        ----------
        application_command_id : `int`
            The application command's identifier.
        application_id : `int`
            The application command's owner application's identifier.
        
        Returns
        -------
        self : ``ApplicationCommand``
        """
        self = object.__new__(cls)
        self.id = application_command_id
        self.allow_by_default = True
        self.application_id = application_id
        self.description = None
        self.description_localizations = None
        self.guild_id = 0
        self.name = ''
        self.name_localizations = None
        self.options = None
        self.required_permissions = None
        self.target_type = ApplicationCommandTargetType.none
        self.version = 0
        return self
    
    
    @classmethod
    def from_data(cls, data):
        """
        Creates a new ``ApplicationCommand`` from requested data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Received application command data.
        
        Returns
        -------
        self : ``ApplicationCommand``
            The created application command instance.
        """
        application_command_id = int(data['id'])
        try:
            self = APPLICATION_COMMANDS[application_command_id]
        except KeyError:
            self = cls._create_empty(application_command_id, int(data['application_id']))
            
            # guild_id
            guild_id = data.get('guild_id', None)
            if (guild_id is not None):
                self.guild_id = int(guild_id)
            
            APPLICATION_COMMANDS[application_command_id] = self
            
        self._update_attributes(data)
        return self
    
    
    def _update_attributes(self, data):
        """
        Updates the application command with the given data.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Received application command data.
        """
        # id
        # Do not update, cannot be changed
        
        # allow_by_default
        try:
            allow_by_default = data['default_permission']
        except KeyError:
            pass
        else:
            self.allow_by_default = allow_by_default
        
        # application_id
        # Do not update, cannot be changed
        
        # description
        try:
            description = data['description']
        except KeyError:
            pass
        else:
            if (description is not None) and (not description):
                description = None
            self.description = description
        
        # description_localizations
        try:
            description_localizations = data['description_localizations']
        except KeyError:
            pass
        else:
            self.description_localizations = build_locale_dictionary(description_localizations)
        
        # name
        try:
            name = data['name']
        except KeyError:
            pass
        else:
            self.name = name
        
        # name_localizations
        try:
            name_localizations = data['name_localizations']
        except KeyError:
            pass
        else:
            self.name_localizations = build_locale_dictionary(name_localizations)
        
        # options
        try:
            option_datas = data['options']
        except KeyError:
            pass
        else:
            if (option_datas is None) or (not option_datas):
                options = None
            else:
                options = [ApplicationCommandOption.from_data(option_data) for option_data in option_datas]
            self.options = options
        
        # required_permissions
        try:
            required_permissions = data['default_member_permissions']
        except KeyError:
            pass
        else:
            if (required_permissions is not None):
                required_permissions = Permission(required_permissions)
            self.required_permissions = required_permissions
        
        # target_type
        try:
            target_type = data['type']
        except KeyError:
            pass
        else:
            self.target_type = ApplicationCommandTargetType.get(target_type)
        
        # version
        try:
            version = data['version']
        except KeyError:
            pass
        else:
            if version is None:
                version = 0
            else:
                version = int(version)
            self.version = version
    
    
    def _difference_update_attributes(self, data):
        """
        Updates the application command with the given data and returns the updated attributes in a dictionary with the
        attribute names as the keys and their old value as the values.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Received application command data.
        
        Returns
        -------
        old_attributes : `dict` of (`str`, `Any`) items
            The updated attributes.
            
            Every item in the returned dict is optional and can contain the following ones:
            
            +---------------------------+---------------------------------------------------+
            | Keys                      | Values                                            |
            +===========================+===================================================+
            | description               | `None`, `str`                                     |
            +---------------------------+---------------------------------------------------+
            | description_localizations | `None`, `dict` of (``Locale``, `str`) items       |
            +---------------------------+---------------------------------------------------+
            | allow_by_default          | `bool`                                            |
            +---------------------------+---------------------------------------------------+
            | name                      | `str`                                             |
            +---------------------------+---------------------------------------------------+
            | name_localizations        | `None`, `dict` of (``Locale``, `str`) items       |
            +---------------------------+---------------------------------------------------+
            | options                   | `None`, `list` of ``ApplicationCommandOption``    |
            +---------------------------+---------------------------------------------------+
            | required_permissions      | `None`, ``Permission``                            |
            +---------------------------+---------------------------------------------------+
            | target_type               | ``ApplicationCommandTargetType``                  |
            +---------------------------+---------------------------------------------------+
            | version                   | `int`                                             |
            +---------------------------+---------------------------------------------------+
        """
        old_attributes = {}
        
        # id
        # Do not update, cannot be changed
        
        # allow_by_default
        try:
            allow_by_default = data['default_permission']
        except KeyError:
            pass
        else:
            if self.allow_by_default != self.allow_by_default:
                old_attributes['allow_by_default'] = allow_by_default
                self.allow_by_default = allow_by_default
        
        # application_id
        # Do not update, cannot be changed
        
        # description
        try:
            description = data['description']
        except KeyError:
            pass
        else:
            if (description is not None) and (not description):
                description = None
            if self.description != description:
                old_attributes['description'] = self.description
                self.description = description
        
        # description_localizations
        try:
            description_localizations = data['description_localizations']
        except KeyError:
            pass
        else:
            description_localizations = build_locale_dictionary(description_localizations)
            if self.description_localizations != description_localizations:
                old_attributes['description_localizations'] = self.description_localizations
                self.description_localizations = description_localizations
        
        # name
        try:
            name = data['name']
        except KeyError:
            pass
        else:
            if self.name != name:
                old_attributes['name'] = self.name
                self.name = name
        
        # name_localizations
        try:
            name_localizations = data['name_localizations']
        except KeyError:
            pass
        else:
            name_localizations = build_locale_dictionary(name_localizations)
            if self.name_localizations != name_localizations:
                old_attributes['name_localizations'] = self.name_localizations
                self.name_localizations = name_localizations
        
        # options
        try:
            option_datas = data['options']
        except KeyError:
            pass
        else:
            if (option_datas is None) or (not option_datas):
                options = None
            else:
                options = [ApplicationCommandOption.from_data(option_data) for option_data in option_datas]
            
            if self.options != options:
                old_attributes['options'] = self.options
                self.options = options
        
        # required_permissions
        try:
            required_permissions = data['default_member_permissions']
        except KeyError:
            pass
        else:
            if (required_permissions is not None):
                required_permissions = Permission(required_permissions)
            
            if self.required_permissions != required_permissions:
                old_attributes['required_permissions'] = self.required_permissions
                self.required_permissions = required_permissions
        
        # target_type
        try:
            target_type = data['type']
        except KeyError:
            pass
        else:
            target_type = ApplicationCommandTargetType.get(target_type)
            if (self.target_type is not target_type):
                old_attributes['target_type'] = self.target_type
                self.target_type = target_type
        
        # version
        try:
            version = data['version']
        except KeyError:
            pass
        else:
            if version is None:
                version = 0
            else:
                version = int(version)
            
            if self.version != version:
                old_attributes['version'] = self.version
                self.version = version
        
        return old_attributes
    
    
    def to_data(self):
        """
        Converts the application command to a json serializable object.
        
        Returns
        -------
        data : `dict` of (`str`, `Any`) items
        """
        data = {}
        
        # id
        # Receive only
        
        # allow_by_default
        # Always add this to data, so if we update the command with it, will be always updated.
        data['default_permission'] = self.allow_by_default
        
        # application_id
        # Receive only
        
        # description
        description = self.description
        if (description is not None):
            data['description'] = description
        
        data['description_localizations'] = destroy_locale_dictionary(self.description_localizations)
        
        # guild_id
        # Receive only
        
        # name
        data['name'] = self.name
        
        # name_localizations
        data['name_localizations'] = destroy_locale_dictionary(self.name_localizations)
        
        # options
        options = self.options
        if (options is None):
            option_datas = []
        else:
            option_datas = [option.to_data() for option in options]
        data['options'] = option_datas
        
        # required_permissions
        data['default_member_permissions'] = self.required_permissions
        
        # target_type
        data['type'] = self.target_type.value
        
        # version
        # Receive only
        return data
    
    
    def __repr__(self):
        """Returns the application command's representation."""
        repr_parts = ['<', self.__class__.__name__]
        
        # if the application command is partial, mention that, else add  `.id` and `.application_id` fields.
        if self.partial:
            repr_parts.append(' (partial)')
        
        else:
            # id
            repr_parts.append(' id=')
            repr_parts.append(repr(self.id))
            
            # application_id
            repr_parts.append(', application_id=')
            repr_parts.append(repr(self.application_id))
            
            # guild_id
            guild_id = self.guild_id
            if guild_id:
                repr_parts.append(', guild_id=')
                repr_parts.append(repr(guild_id))
        
        # Required fields are `.name` and `.type`
        
        # name
        repr_parts.append(', name=')
        repr_parts.append(repr(self.name))
        
        # target_type
        target_type = self.target_type
        if (target_type is not ApplicationCommandTargetType.none):
            repr_parts.append(', target_type=')
            repr_parts.append(target_type.name)
            repr_parts.append(' (')
            repr_parts.append(repr(target_type.value))
            repr_parts.append(')')
        
        # Extra fields: `.description`, `.options`, `.allow_by_default`, `.required_permissions`,
        #    `.name_localizations`, `.description_localizations`
        
        # description
        description = self.description
        if (description is not None):
            repr_parts.append(', description=')
            repr_parts.append(repr(self.description))
        
        # allow_by_default
        if not self.allow_by_default:
            repr_parts.append(', allow_by_default=False')
        
        required_permissions = self.required_permissions
        if (required_permissions is not None):
            repr_parts.append(', required_permissions=')
            repr_parts.append(required_permissions.__format__('d'))
        
        # options
        options = self.options
        if (options is not None):
            repr_parts.append(', options=[')
            
            index = 0
            limit = len(options)
            
            while True:
                option = options[index]
                index += 1
                repr_parts.append(repr(option))
                
                if index == limit:
                    break
                
                repr_parts.append(', ')
                continue
            
            repr_parts.append(']')
        
        # name_localizations
        name_localizations = self.name_localizations
        if (name_localizations is not None):
            repr_parts.append(', name_localizations=')
            repr_parts.append(repr(name_localizations))
        
        # description_localizations
        description_localizations = self.description_localizations
        if (description_localizations is not None):
            repr_parts.append(', description_localizations=')
            repr_parts.append(repr(description_localizations))
        
        # Ignore extra fields: `.version`
        
        repr_parts.append('>')
        return ''.join(repr_parts)
    
    
    @property
    def partial(self):
        """
        Returns whether the application command is partial.
        
        Returns
        -------
        partial : `bool`
        """
        if self.id == 0:
            return True
        
        return False
    
    
    def __hash__(self):
        """Returns the application's hash value."""
        id_ = self.id
        if id_:
            return id_
        
        raise TypeError(f'Cannot hash partial {self.__class__.__name__} object.')
    
    
    @classmethod
    def _from_edit_data(cls, data, application_command_id, application_id):
        """
        Creates an application command with the given parameters after an application command edition took place.
        
        Parameters
        ----------
        data : `dict` of (`str`, `Any`) items
            Application command data returned by it's ``.to_data`` method.
        application_command_id : `int`
            The unique identifier number of the newly created application command.
        application_id : `int`
            The new application identifier number of the newly created application command.
        
        Returns
        -------
        self : ``ApplicationCommand``
            The newly created or updated application command.
        """
        try:
            self = APPLICATION_COMMANDS[application_command_id]
        except KeyError:
            self = cls._create_empty(application_command_id, application_id)
            APPLICATION_COMMANDS[application_command_id] = self
        
        self._update_attributes(data)
        
        return self
    
    
    def copy(self):
        """
        Copies the ``ApplicationCommand``.
        
        The copy is always a partial application command.
        
        Returns
        -------
        new : ``ApplicationCommand``
        """
        new = object.__new__(type(self))
        
        # id
        new.id = 0
        
        # allow_by_default
        new.allow_by_default = self.allow_by_default
        
        # application_id
        new.application_id = 0
        
        # description
        new.description = self.description
        

        # description_localizations
        description_localizations = self.description_localizations
        if (description_localizations is not None):
            description_localizations = description_localizations.copy()
        new.description_localizations = description_localizations
        
        
        # guild_id
        new.guild_id = self.guild_id
        
        
        # name
        new.name = self.name
        

        # name_localizations
        name_localizations = self.name_localizations
        if (name_localizations is not None):
            name_localizations = name_localizations.copy()
        new.name_localizations = name_localizations
        
        # options
        options = self.options
        if (options is not None):
            options = [option.copy() for option in options]
        new.options = options
        
        # required_permissions
        new.required_permissions = self.required_permissions
        
        # target_type
        new.target_type = self.target_type
        
        # version
        new.version = 0
        
        return new
    
    
    def __eq__(self, other):
        """Returns whether the two application commands are equal."""
        if type(self) is not type(other):
            return NotImplemented
        
        # If both entity is not partial, leave instantly by comparing id.
        self_id = self.id
        other_id = other.id
        if self_id and other_id:
            if self_id == other_id:
                return True
            
            return False
        
        # allow_by_default
        if self.allow_by_default != other.allow_by_default:
            return False
        
        # description
        if self.description != other.description:
            return False
        
        # description_localizations
        if self.description_localizations != other.description_localizations:
            return False
        
        # name
        if self.name != other.name:
            return False
        
        # name_localizations
        if self.name_localizations != other.name_localizations:
            return False
        
        # required_permissions
        if self.required_permissions != other.required_permissions:
            return False
        
        # options
        if self.options != other.options:
            return False
        
        # target_type
        if (self.target_type is not other.target_type):
            return False
        
        return True
    
    
    def __ne__(self, other):
        """Returns whether the two application commands are different."""
        if type(self) is not type(other):
            return NotImplemented
        
        self_id = self.id
        other_id = other.id
        if self_id and other_id:
            if self_id == other_id:
                return False
            
            return True
        
        # allow_by_default
        if self.allow_by_default != other.allow_by_default:
            return True
        
        # description
        if self.description != other.description:
            return True
        
        # description_localizations
        if self.description_localizations != other.description_localizations:
            return True
        
        # name
        if self.name != other.name:
            return True
        
        # name_localizations
        if self.name_localizations != other.name_localizations:
            return True
        
        # required_permissions
        if self.required_permissions != other.required_permissions:
            return True
        
        # options
        if self.options != other.options:
            return True
        
        # target_type
        if (self.target_type is not other.target_type):
            return True
        
        return False
    
    
    @property
    def mention(self):
        """
        Returns the application command's mention.
        
        Returns
        -------
        mention : `str`
        """
        return f'</{self.name}:{self.id}>'
    
    
    @property
    def display_name(self):
        """
        Returns the application command's display name.
        
        Returns
        -------
        display_name : `str`
        """
        return self.name.lower().replace('_', '-')
    
    
    @property
    def edited_at(self):
        """
        Returns when the command was last edited / modified. If the command was not edited yet, returns `None`.
        
        Returns
        -------
        edited_at : `None`, `edited_at`
        """
        version = self.version
        if version:
            return id_to_datetime(version)
    
    
    def __format__(self, code):
        """
        Formats the application command in a format string.
        
        Parameters
        ----------
        code : `str`
            The option on based the result will be formatted.
        
        Returns
        -------
        application_command : `str`
        
        Raises
        ------
        ValueError
            Unknown format code.
        
        Examples
        --------
        ```py
        >>> from hata import ApplicationCommand
        >>> application_command = ApplicationCommand('cake-lover', 'Sends a random cake recipe OwO')
        >>> application_command
        <ApplicationCommand partial name='cake-lover', description='Sends a random cake recipe OwO'>
        >>> # no code stands for `application_command.name`.
        >>> f'{application_command}'
        'CakeLover'
        >>> # 'd' stands for display name.
        >>> f'{application_command:d}'
        'cake-lover'
        >>> # 'm' stands for mention.
        >>> f'{application_command:m}'
        '</cake-lover:0>'
        >>> # 'c' stands for created at.
        >>> f'{application_command:c}'
        '2021-01-03 20:17:36'
        >>> # 'e' stands for edited at.
        >>> f'{application_command:e}'
        'never'
        ```
        """
        if not code:
            return self.name
        
        if code == 'm':
            return self.mention
        
        if code == 'd':
            return self.display_name
        
        if code == 'c':
            return self.created_at.__format__(DATETIME_FORMAT_CODE)
        
        if code == 'e':
            edited_at = self.edited_at
            if edited_at is None:
                edited_at = 'never'
            else:
                edited_at = edited_at.__format__(DATETIME_FORMAT_CODE)
            return edited_at
        
        raise ValueError(f'Unknown format code {code!r} for object of type {self.__class__.__name__!r}')
    
    
    def __len__(self):
        """Returns the application command's length."""
        length = 0
        
        # description
        length += len(self.description)
        
        # description_localizations
        description_localizations = self.description_localizations
        if (description_localizations is not None):
            for value in description_localizations.values():
                length += len(value)
        
        # name
        length += len(self.name)
        
        # name_localizations
        name_localizations = self.name_localizations
        if (name_localizations is not None):
            for value in name_localizations.values():
                length += len(value)
        
        # options
        options = self.options
        if (options is not None):
            for option in options:
                length += len(option)
        
        return length
    
    
    def is_context_command(self):
        """
        Returns whether the application command is a context command.
        
        Returns
        -------
        is_context_command : `bool`
        """
        return (self.target_type in APPLICATION_COMMAND_CONTEXT_TARGET_TYPES)
    
    
    def is_slash_command(self):
        """
        Returns whether the application command is a slash command.
        
        Returns
        -------
        is_slash_command : `bool`
        """
        return (self.target_type is ApplicationCommandTargetType.chat)
    
    
    @property
    def guild(self):
        """
        Returns the application command's guild.
        
        Returns
        -------
        guild : `None`, ``Guild``
        """
        guild_id = self.guild_id
        if guild_id:
            return GUILDS[guild_id]
    
    
    def apply_translation(self, translation_table, replace=False):
        """
        Applies translation from the given nested dictionary to the application command.
        
        Parameters
        ----------
        translation_table : `None`, `dict` of ((``Locale``, `str`),
                (`None`, `dict` (`str`, (`None`, `str`)) items)) items
            Translation table to pull localizations from.
        replace : `bool` = `False`, Optional
            Whether actual translation should be replaced.
        
        Raises
        ------
        AssertionError
            If the application command is not partial.
        """
        if __debug__:
            if not self.partial:
                raise AssertionError(
                    f'{self.__class__.__name__}.add_option` can be only called on partial '
                    f'`{self.__class__.__name__}`-s, but was called on {self!r}.'
                )
        
        if translation_table is None:
            return
        
        # description
        self.description_localizations = apply_translation_into(
            self.description,
            self.description_localizations,
            translation_table,
            replace,
        )
        
        # name
        self.name_localizations = apply_translation_into(
            self.name,
            self.name_localizations,
            translation_table,
            replace,
        )
        
        # options
        options = self.options
        if (options is not None):
            for option in options:
                option.apply_translation(translation_table, replace)
