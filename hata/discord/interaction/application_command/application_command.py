__all__ = ('ApplicationCommand',)


from ...bases import DiscordEntity
from ...core import APPLICATION_COMMANDS
from ...preconverters import preconvert_preinstanced_type
from ...utils import DATETIME_FORMAT_CODE, id_to_datetime, is_valid_application_command_name

from .application_command_option import ApplicationCommandOption
from .constants import (
    APPLICATION_COMMAND_DESCRIPTION_LENGTH_MAX, APPLICATION_COMMAND_DESCRIPTION_LENGTH_MIN,
    APPLICATION_COMMAND_NAME_LENGTH_MAX, APPLICATION_COMMAND_NAME_LENGTH_MIN, APPLICATION_COMMAND_OPTIONS_MAX
)
from .preinstanced import APPLICATION_COMMAND_CONTEXT_TARGET_TYPES, ApplicationCommandTargetType


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
    description : `str`
        The command's description. It's length can be in range [2:100].
    name : `str`
        The name of the command. It's length can be in range [1:32].
    options : `None`, `list` of ``ApplicationCommandOption``
        The parameters of the command. It's length can be in range [0:25]. If would be set as empty list, instead is
        set as `None`.
    target_type : ``ApplicationCommandTargetType``
        The application command target's type describing where it shows up.
    version : `int`
        The time when the command was last edited in snowflake.
    
    Notes
    -----
    ``ApplicationCommand``s are weakreferable.
    """
    __slots__ = ('allow_by_default', 'application_id', 'description', 'name', 'options', 'target_type', 'version')
    
    def __new__(cls, name, description=None, *, allow_by_default=True, options=None, target_type=None):
        """
        Creates a new ``ApplicationCommand`` with the given parameters.
        
        Parameters
        ----------
        name : `str`
            The name of the command. It's length can be in range [1:32].
        
        description : `None`, `str` = `None`, Optional
            The command's description. It's length can be in range [2:100].
        
        allow_by_default : `bool` = `True`, Optional (Keyword only)
            Whether the command is enabled by default for everyone who has `use_application_commands` permission.
            
            Defaults to `True`.
        
        options : `None`, (`list`, `tuple`) of ``ApplicationCommandOption`` = `None`, Optional (Keyword only)
            The parameters of the command. It's length can be in range [0:25].
        
        target_type : `None`, `int`, ``ApplicationCommandTargetType`` = `None`, Optional (Keyword only)
            The application command's target type.
            
            Defaults to `ApplicationCommandTargetType.chat`.
        
        Raises
        ------
        TypeError
            If `target_type` is neither `int`, nor ``ApplicationCommandTargetType``.
        ValueError
            `description` cannot be `None` for application commands with non-context target.
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
        if __debug__:
            if not isinstance(allow_by_default, bool):
                raise AssertionError(
                    f'`allow_by_default` can be `bool`, got {allow_by_default.__class__.__name__}; '
                    f'{allow_by_default!r}.'
                )
        
        # description
        if __debug__:
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
        
        # target_type
        if target_type is None:
            target_type = ApplicationCommandTargetType.chat
        else:
            target_type = preconvert_preinstanced_type(target_type, 'target_type', ApplicationCommandTargetType)
        
        
        # Post checks
        if (target_type in APPLICATION_COMMAND_CONTEXT_TARGET_TYPES):
            # Context commands cannot have description and options, so we clear them.
            description = None
            options_processed = None
        
        else:
            # For non context commands description is required.
            if (description is None):
                raise ValueError(
                    f'`description` cannot be `None` for application commands with non-context target.'
                )
        
        
        self = object.__new__(cls)
        
        self.id = 0
        self.application_id = 0
        self.name = name
        self.description = description
        self.allow_by_default = allow_by_default
        self.options = options_processed
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
            if self.id != 0:
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
        self.name = ''
        self.options = None
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
        
        # name
        try:
            name = data['name']
        except KeyError:
            pass
        else:
            self.name = name
        
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
            
            +-----------------------+---------------------------------------------------+
            | Keys                  | Values                                            |
            +=======================+===================================================+
            | description           | `None`, `str`                                     |
            +-----------------------+---------------------------------------------------+
            | allow_by_default      | `bool`                                            |
            +-----------------------+---------------------------------------------------+
            | name                  | `str`                                             |
            +-----------------------+---------------------------------------------------+
            | options               | `None`, `list` of ``ApplicationCommandOption``    |
            +-----------------------+---------------------------------------------------+
            | target_type           | ``ApplicationCommandTargetType``                  |
            +-----------------------+---------------------------------------------------+
            | version               | `int`                                             |
            +-----------------------+---------------------------------------------------+
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
        
        # name
        try:
            name = data['name']
        except KeyError:
            pass
        else:
            if self.name != name:
                old_attributes['name'] = self.name
                self.name = name
        
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
        
        # name
        data['name'] = self.name
        
        # options
        options = self.options
        if (options is None):
            option_datas = []
        else:
            option_datas = [option.to_data() for option in options]
        data['options'] = option_datas
        
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
            repr_parts.append(' id=')
            repr_parts.append(repr(self.id))
            repr_parts.append(', application_id=')
            repr_parts.append(repr(self.application_id))
        
        # Required fields are `.name` and `.type`
        
        repr_parts.append(', name=')
        repr_parts.append(repr(self.name))
        
        target_type = self.target_type
        if (target_type is not ApplicationCommandTargetType.none):
            repr_parts.append(', target_type=')
            repr_parts.append(target_type.name)
            repr_parts.append(' (')
            repr_parts.append(repr(target_type.value))
            repr_parts.append(')')
        
        # Optional fields `.description`, `.options`, `.allow_by_default`
        description = self.description
        if (description is not None):
            repr_parts.append(', description=')
            repr_parts.append(repr(self.description))
        
        if not self.allow_by_default:
            repr_parts.append(', allow_by_default=False')
        
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
        
        repr_parts.append('>')
        
        # Ignore extra fields: `.version`
        
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
        
        # name
        new.name = self.name
        
        # options
        options = self.options
        if (options is not None):
            options = [option.copy() for option in options]
        new.options = options
        
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
        
        # name
        if self.name != other.name:
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
        
        # name
        if self.name != other.name:
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
        length = len(self.name) + len(self.description)
        
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
