__all__ = ()

from ...backend.utils import WeakReferer, copy_docs

TYPE_IDENTIFIER_STR = 1
TYPE_IDENTIFIER_INT = 2
TYPE_IDENTIFIER_FLOAT = 3

TYPE_TYPE_STR = str
TYPE_TYPE_INT = int
TYPE_TYPE_FLOAT = float

TYPE_NAME_STR = 'str'
TYPE_NAME_INT = 'int'
TYPE_NAME_FLOAT = 'float'

TYPE_TYPE_TO_IDENTIFIER = {
    TYPE_TYPE_STR: TYPE_IDENTIFIER_STR,
    TYPE_TYPE_INT: TYPE_IDENTIFIER_INT,
    TYPE_TYPE_FLOAT: TYPE_IDENTIFIER_FLOAT,
}

TYPE_NAME_TO_IDENTIFIER = {
    TYPE_NAME_STR: TYPE_IDENTIFIER_STR,
    TYPE_NAME_INT: TYPE_IDENTIFIER_INT,
    TYPE_NAME_FLOAT: TYPE_IDENTIFIER_FLOAT,
}

# revert the relation
TYPE_IDENTIFIER_TO_NAME = {identifier: name for identifier, name in TYPE_NAME_TO_IDENTIFIER.items()}


def converter_parameter_to_str(value):
    """
    Converts the given value to string.
    
    Parameters
    ----------
    value : `str`
        The value to convert to string.
    
    Returns
    -------
    value : `None` or `str`
        Returns `None` if conversion failed.
    """
    return value


def converter_parameter_to_int(value):
    """
    Converts the given value to string.
    
    Parameters
    ----------
    value : `str`
        The value to convert to string.
    
    Returns
    -------
    value : `None` or `int`
        Returns `None` if conversion failed.
    """
    try:
        value = int(value)
    except ValueError:
        value = None
    
    return value


def converter_parameter_to_float(value):
    """
    Converts the given value to string.
    
    Parameters
    ----------
    value : `str`
        The value to convert to string.
    
    Returns
    -------
    value : `None` or `float`
        Returns `None` if conversion failed.
    """
    try:
        value = float(value)
    except ValueError:
        value = None
    
    return value

TYPE_IDENTIFIER_TO_CONVERTER = {
    TYPE_IDENTIFIER_STR: converter_parameter_to_str,
    TYPE_IDENTIFIER_INT: converter_parameter_to_int,
    TYPE_IDENTIFIER_FLOAT: converter_parameter_to_float,
}


def validate_command_line_parameter_expected_type_identifier(expected_type):
    """
    Validates ``CommandLineParameter``'s `expected_type` parameter.
    
    Parameters
    ----------
    expected_type : `None`, `str`, `type`
        Expected type by a command line parameter.
    
    Returns
    -------
    expected_type_identifier : `int`
        The type's identifier.
    
    Raises
    ------
    TypeError
        If `expected_type` is neither `None`, `str`, neither `type` instance.
    ValueError
        If `expected_type` is correct type, but it's value is incorrect and cannot identifier converter for it.
    """
    if expected_type is None:
        expected_type_identifier = TYPE_IDENTIFIER_STR
    
    elif isinstance(expected_type, str):
        try:
            expected_type_identifier = TYPE_NAME_TO_IDENTIFIER[expected_type]
        except KeyError:
            raise ValueError(f'`expected_type` value has no converter, got: {expected_type!r}.') from None
    
    elif isinstance(expected_type, type):
        try:
            expected_type_identifier = TYPE_TYPE_TO_IDENTIFIER[expected_type]
        except KeyError:
            raise ValueError(f'`expected_type` value has no converter, got: {expected_type!r}.') from None
    
    else:
        raise TypeError(f'`expected_type` can be either `None`, `str` or `type` instance, got '
            f'{expected_type.__class__.__name__}.')
    
    return expected_type_identifier


def validate_command_line_parameter_name(name):
    """
    Validates ``CommandLineParameter``'s `name` parameter.
    
    Parameters
    ----------
    name : `str`
        Name parameter to validate.
    
    Returns
    -------
    name : `str`
        The validated name parameter.
    
    Raises
    ------
    TypeError
        If `name` is not `str` instance.
    """
    if type(name) is str:
        pass
    elif isinstance(name, str):
        name = str(name)
    else:
        raise TypeError(f'`name` can be `str` instance, got {name.__class__.__name__}.')
    
    return name


def validate_command_line_parameter_keyword(keyword):
    """
    Validates ``CommandLineParameter``'s `keyword` parameter.
    
    Parameters
    ----------
    keyword : `None` or `str`
        Keyword parameter to validate.
    
    Returns
    -------
    keyword : `None` or `str`
        The validated keyword parameter.
    
    Raises
    ------
    TypeError
        If `keyword` is neither `None` nor `str` instance.
    """
    if keyword is None:
        pass
    elif type(keyword) is str:
        pass
    elif isinstance(keyword, str):
        keyword = str(keyword)
    else:
        raise TypeError(f'`keyword` can be given as `None` or `str` instance, got {keyword.__class__.__name__}.')
    
    return keyword


def validate_command_line_parameter_multi(multi):
    """
    Validates ``CommandLineParameter``'s `multi` parameter.
    
    Parameters
    ----------
    multi : `bool`
        Multi parameters to validate.
    
    Returns
    -------
    multi : `bool`
        Validated multi parameter.
    
    Raises
    ------
    TypeError
        If `multi` is not `bool` instance.
    """
    if type(multi) is bool:
        pass
    elif isinstance(multi, bool):
        multi = bool(multi)
    else:
        raise TypeError(f'`multi` can be `bool` instance, got {multi.__class__.__name__}.')
    
    return multi


DEFAULT_DEFAULT_VALUE = ...

def validate_command_line_parameter_default_value(default):
    """
    Validates ``CommandLineParameter``'s `default` parameter.
    
    Parameters
    ----------
    default : `Any`
        Default value.
    
    Returns
    -------
    has_default : `bool`
        Whether default value is given.
    default_value : `None` or `Any`
        Default value.
    """
    if default is DEFAULT_DEFAULT_VALUE:
        has_default = False
        default_value = None
    else:
        has_default = True
        default_value = default
    
    return has_default, default_value
    

def validate_command_line_parameter_modifier(modifier):
    """
    Validates ``CommandLineParameter``'s `modifier` parameter.
    
    Parameters
    ----------
    modifier : `bool`
        Multi parameters to validate.
    
    Returns
    -------
    modifier : `bool`
        Validated multi parameter.
    
    Raises
    ------
    TypeError
        If `modifier` is not `bool` instance.
    """
    if type(modifier) is bool:
        pass
    elif isinstance(modifier, bool):
        modifier = bool(modifier)
    else:
        raise TypeError(f'`multi` can be `bool` instance, got {modifier.__class__.__name__}.')
    
    return modifier



class CommandLineParameter:
    """
    Command line parameter.
    
    Attributes
    ----------
    default_value : `None` or `Any`
        Default value to give if parameter was not passed.
    expected_type_identifier : `int`
        Identifier of the accepted type of the parameter.
    has_default : `bool`
        Whether the parameter has default value.
    modifier : `bool`
        Whether the parameter is a modifier.
    keyword : `None` or `bool`
        Keyword to pass the parameter.
    multi : `bool`
        Whether the parameter accepts multiple values.
    name : `str`
        The parameter's name.
    """
    __slots__ = ('default_value', 'expected_type_identifier', 'has_default', 'modifier', 'keyword', 'keyword_only',
        'multi', 'name')
    
    def __new__(cls, name, *, default=DEFAULT_DEFAULT_VALUE, keyword=None, multi=False, expected_type=None, modifier=False):
        """
        Creates a new ``CommandLineParameter`` instance from the given parameters.
        
        Parameters
        ----------
        name : `str`
            The parameter's name.
        default : `Any`, Optional (Keyword only)
            Default value if the parameter is not present.
        keyword : `str`, Optional (Keyword only)
            Keyword to pass the parameter after if applicable.
        multi : `bool`
            Whether multiple parameters are accepted.
        expected_type : `None` or `str`, `type`, Optional (Keyword only)
            The expected type by the parameter. Defaults to `bool`.
        
        Raises
        ------
        TypeError
            - If `expected_type` is neither `None`, `str`, neither `type` instance.
            - If `name` is not `str` instance.
            - If `keyword` is neither `None` nor `str` instance.
            - If `multi` is not `bool` instance.
            - If `modifier` is not `bool` instance.
            - `default` and `modifier` parameters are mutually exclusive.
            - Keyword parameters must have either `default` or `multi` parameters defined.
        ValueError
            If `expected_type` is correct type, but it's value is incorrect and cannot identifier converter for it.
        """
        name = validate_command_line_parameter_name(name)
        has_default, default_value = validate_command_line_parameter_multi(default)
        keyword = validate_command_line_parameter_keyword(keyword)
        multi = validate_command_line_parameter_multi(multi)
        expected_type_identifier = validate_command_line_parameter_expected_type_identifier(expected_type)
        modifier = validate_command_line_parameter_modifier(modifier)
        
        if modifier:
            if has_default:
                raise TypeError(f'`default` and `modifier` parameters are mutually exclusive.')
            
        else:
            if (not has_default) and (not multi):
                raise TypeError(f'Keyword parameters must have either `default` or `multi` parameters defined.')
    
        
        self = object.__new__(cls)
        self.name = name
        self.default_value = default_value
        self.keyword = keyword
        self.multi = multi
        self.expected_type_identifier = expected_type_identifier
        self.has_default = has_default
        self.modifier = modifier
        return self
    
    
    def __repr__(self):
        """Returns the command line parameter's representation."""
        repr_parts = ['<', self.__class__.__name__]
        
        repr_parts.append(' name=')
        repr_parts.append(repr(self.name))
        
        expected_type_name = TYPE_IDENTIFIER_TO_NAME[self.expected_type_identifier]
        repr_parts.append(', expected_type=')
        repr_parts.append(expected_type_name)
        
        if self.has_default:
            repr_parts.append(', default=')
            repr_parts.append(repr(self.default_value))
        
        keyword = self.keyword
        if (keyword is not None):
            repr_parts.append(', keyword=')
            repr_parts.append(repr(keyword))
        
        if self.multi:
            repr_parts.append(', multi=True')
        
        if self.modifier:
            repr_parts.append(', modifier=True')
        
        repr_parts.append('>')
        return ''.join(repr_parts)
    
    
    def is_positional_only(self):
        """
        Returns whether the command line parameter is a positional only parameter.
        
        Returns
        -------
        is_positional_only : `bool`
        """
        if self.modifier:
            is_positional_only = False
        else:
            if self.keyword is None:
                is_positional_only = True
            else:
                is_positional_only = False
        
        return is_positional_only
    
    
    def is_keyword_only(self):
        """
        Returns whether the parameter is keyword only.
        
        Returns
        -------
        is_keyword_only : `bool`
        """
        if self.modifier:
            is_keyword_only = False
        else:
            if self.keyword is None:
                is_keyword_only = False
            else:
                is_keyword_only = True
        
        return is_keyword_only
    
    
    def is_modifier(self):
        """
        Returns whether the command line parameter is a modifier parameter.
        
        Returns
        -------
        is_modifier : `bool`
        """
        return self.modifier
    
    
    def convert(self, value):
        """
        Calls the parameter's converter on the given value.
        
        Parameters
        ----------
        value : `str`
            The value to convert.
        
        Returns
        -------
        value : `Any`
            The converted value.
        """
        return TYPE_IDENTIFIER_TO_CONVERTER[self.expected_type_identifier](value)


def normalize_command_name(command_name):
    """
    Normalises the given command name.
    
    Parameters
    ----------
    command_name : `str`
        The command name to normalize.
        
    """
    return command_name.lower().replace('_', '-')


class CommandLineCommand:
    """
    Attributes
    ----------
    _command_category : `None` or ``CommandLineCommandCategory``
        Command category of the command.
    _self_reference : `None` or ``WeakReferer``
        Reference to itself.
    help : `str`
        Command help message.
    name : `str`
        The command's name.
    """
    __slots__ = ('__weakref__', '_command_category', '_self_reference', 'help', 'name')
    
    def __new__(cls, name, help_):
        """
        Creates a new command line command.
        
        Parameters
        ----------
        name : `str`
            The command's name.
        help : `str`
            The command's help message.
        """
        name = normalize_command_name(name)
        
        self = object.__new__(cls)
        self._command_category = None
        self.name = name
        self.help = None
        self._self_reference = None
        
        self._self_reference = WeakReferer(self)
        self._command_category = CommandLineCommandCategory(self, '')
        
        return self
    
    
    def register_command_category(self, name):
        """
        Registers a sub command to the command.
        
        Parameters
        ----------
        name : `str`
            The name of the sub-command.
        
        Returns
        -------
        sub_command : ``CommandLineCommandCategory``
        """
        return self._command_category.register_command_category(self, name)
    
    
    def register_command_function(self, function):
        """
        Parameters
        ----------
        function : `callable`
            The function to call when the command is used.
        
        Returns
        -------
        command_function : ``CommandLineCommandFunction``
        """
        return self._command_category.register_command_function(self, function)
    
    
    def __call__(self, parameters, index):
        """
        Calls the command line command.
        
        Parameters
        ----------
        parameters : `list` of `str`
            Command line parameters.
        index : `int`
            The index of the first parameter trying to process.
        """
        command_category = self._command_category
        if (command_category is not None):
            self._command_category(parameters, index)
    
    
    def _trace_back_name(self):
        """
        Traces back to the source name of the command.
        
        This method is an iterable coroutine.
        
        Yields
        ------
        name : `str`
        """
        yield self.name


class CommandLineCommandCategory:
    """
    Command line command category.
    
    Attributes
    ----------
    _command_categories : `None` or `dict` of (`str`, ``CommandLineCommandCategory``) items
        Sub commands of the command.
    _command_function : `None` or ``CommandLineCommandFunction``
        Command to call, if sub command could not be detected.
    _parent_reference : `None` or ``WeakReferer``
        Weakreference to the command category's parent.
    _self_reference : `None` or ``WeakReferer``
        Weakreference to the category itself.
    name : `None` or `str`
        The sub command category's name.
    """
    __slots__ = ('__weakref__', '_command_categories', '_command_function', '_parent_reference', '_self_reference',
        'name')
    
    def __new__(cls, parent, name):
        """
        Creates a new command line command category.
        
        Parameters
        ----------
        parent : ``CommandLineCommand`` or ``CommandLineCommandCategory``
            The parent command or command category.
        name : `None` or `str`
            The command category's name.
        """
        if (name is not None):
            name = normalize_command_name(name)
        
        self = object.__new__(cls)
        self.name = name
        self._command_function = None
        self._command_categories = None
        self._self_reference = None
        self._parent_reference = parent._self_reference
        
        self._self_reference = WeakReferer(self)
        
        return self
    
    
    def register_command_category(self, name):
        """
        Registers a sub command to the command.
        
        Parameters
        ----------
        name : `str`
            The name of the sub-command.
        
        Returns
        -------
        sub_command : ``CommandLineCommandCategory``
        """
        sub_command = CommandLineCommandCategory(self, name)
        sub_commands = self._command_categories
        if (sub_commands is None):
            sub_commands = {}
            self._command_categories = sub_commands
        
        sub_commands[sub_command.name] = sub_command
        return sub_command
    
    
    def register_command_function(self, function):
        """
        Parameters
        ----------
        function : `callable`
            The function to call when the command is used.
        
        Returns
        -------
        command_function : CommandLineCommandFunction
        """
        command_function = CommandLineCommandFunction(self, function)
        self._command_function = command_function
        return command_function
    
    
    @copy_docs(CommandLineCommand._trace_back_name)
    def _trace_back_name(self):
        parent_reference = self._parent_reference
        if (parent_reference is not None):
            parent = parent_reference()
            if (parent is not None):
                yield from parent._trace_back_name()
        
        name = self.name
        if (name is not None):
            yield name
    
    
    def __call__(self, parameters, index):
        """
        Calls the command line command category.
        
        Parameters
        ----------
        parameters : `list` of `str`
            Command line parameters.
        index : `int`
            The index of the first parameter trying to process.
        """
        while True:
            if index >= len(parameters):
                break
            
            command_categories = self._command_categories
            if (command_categories is None):
                break
            
            command_name = parameters[index]
            command_name = normalize_command_name(command_name)
            
            try:
                command_category = command_categories[command_name]
            except KeyError:
                break
            
            command_category(parameters, index+1)
            return
        
        command_function = self._command_function
        if (command_function is not None):
            command_function(parameters, index)



class CommandLineCommandFunction:
    """
    Command line function to call.
    
    Attributes
    ----------
    _function : `callable`
        The function to call.
    _parent_reference : `None` or ``WeakReferer``
        Weakreference to the command function's parent.
    _parameters_keyword_only : `None` or `list` of ``CommandLineParameter``
        Keyword only parameters.
    _parameters_modifier : `None` or `list` of ``CommandLineParameter``
        Parameter modifiers.
    _parameters_positional_only : `None` or `list` of ``CommandLineParameter``
        Positional only parameters.
    """
    __slots__ = ('_function', '_parent_reference', '_parameters_keyword_only', '_parameters_modifier',
        '_parameters_positional_only',)
    
    def __new__(cls, parent, function):
        """
        Creates a new ``CommandLineCommandFunction`` instance.
        
        Parameters
        ----------
        function : `callable`
            The function to call when the command is used.
        """
        self = object.__new__(cls)
        self._function = function
        self._parameters_modifier = None
        self._parameters_positional_only = None
        self._parameters_keyword_only = None
        self._parent_reference = parent._self_reference
        return self
    
    
    def add_parameter(self, parameter):
        """
        Adds a parameter to the command line command.
        
        Parameters
        ----------
        parameter : ``CommandLineParameter``
            The parameter to add.
        
        Raises
        ------
        TypeError
            Bad parameter order.
        """
        if parameter.is_modifier():
            parameters_positional_only = self._parameters_positional_only
            if (parameters_positional_only is not None):
                last_parameter = parameters_positional_only[-1]
                if last_parameter.multi:
                    raise TypeError(f'Cannot add modifier after parameter positional parameter marked as multi.')
            
            parameters_modifier = self._parameters_modifier
            if parameters_modifier is None:
                parameters_modifier = []
                self._parameters_modifier = parameters_modifier
            
            parameters_modifier.append(parameter)
        
        
        elif parameter.is_positional_only():
            if parameter.multi:
                if (self._parameters_modifier is not None):
                    raise TypeError(f'Cannot add positional multi parameter after adding any modifier one.')
                
                if (self._parameters_keyword_only is not None):
                    raise TypeError(f'Cannot add positional multi parameter after adding any keyword one.')
            
            parameters_positional_only = self._parameters_positional_only
            if (parameters_positional_only is None):
                parameters_positional_only = []
                self._parameters_positional_only = parameters_positional_only
            else:
                last_parameter = parameters_positional_only[-1]
                if last_parameter.multi:
                    raise TypeError(f'Only the last positional parameter can be `multi`.')
            
            parameters_positional_only.append(parameter)
        
        elif parameter.is_keyword_only():
            parameters_positional_only = self._parameters_positional_only
            if (parameters_positional_only is not None):
                last_parameter = parameters_positional_only[-1]
                if last_parameter.multi:
                    raise TypeError(f'Cannot add modifier after parameter positional parameter marked as multi.')
            
            parameters_keyword_only = self._parameters_keyword_only
            if (parameters_keyword_only is None):
                parameters_keyword_only = []
                self._parameters_keyword_only = parameters_keyword_only
            
            parameters_keyword_only.append(parameter)
    
    
    @copy_docs(CommandLineCommand._trace_back_name)
    def _trace_back_name(self):
        parent_reference = self._parent_reference
        if (parent_reference is not None):
            parent = parent_reference()
            if (parent is not None):
                yield from parent._trace_back_name()
    
    
    def __call__(self, parameters, index):
        """
        Calls the command line command.
        
        Parameters
        ----------
        parameters : `list` of `str`
            Command line parameters.
        index : `int`
            The index of the first parameter trying to process.
        """
        parsed_parameters = {}
        parameter_count = len(parameters)
        
        parameters_positional_only = self._parameters_positional_only
        if (parameters_positional_only is not None):
            for positional_parameter in parameters_positional_only:
                if positional_parameter.multi:
                    parameter_values = []
                    while True:
                        if index == parameter_count:
                            break
                        
                        parameter_value = parameters[index]
                        index += 1
                        
                        parameter_value = positional_parameter.convert(parameter_value)
                        if parameter_value is None:
                            # TODO
                            return
                        
                        parameter_values.append(parameter_value)
                        continue
                    
                    parameter_value = parameter_values
                    
                else:
                    if (index == parameter_count):
                        if positional_parameter.has_default:
                            parameter_value = positional_parameter.default
                        else:
                            return
                            # Failure todo
                        
                    else:
                        parameter_value = parameters[index]
                        index += 1
                        
                        parameter_value = positional_parameter.convert(parameter_value)
                        if parameter_value is None:
                            # TODO
                            return
                
                parsed_parameters[positional_parameter.name] = parameter_value
                continue
        
        modifier_parameters = self._parameters_modifier
        if (modifier_parameters is not None):
            modifier_parameters = {parameter.name for parameter in modifier_parameters}
        
        
        parameters_keyword_only = self._parameters_keyword_only
        if (parameters_keyword_only is None):
            if (modifier_parameters is not None):
                while True:
                    if index == parameter_count:
                        break
                    
                    parameter_name = parameters[index]
                    index += 1
                    
                    try:
                        modifier_parameters.remove(parameter_name)
                    except KeyError:
                        # TODO
                        return
                    
                    parsed_parameters[parameter_name] = True
                    continue
        
        else:
            parameters_keyword_only = {parameter.name: parameter for parameter in parameters_keyword_only}
            
            while True:
                if index == parameter_count:
                    break
                
                parameter_name = parameters[index]
                index += 1
                
                if (modifier_parameters is not None):
                    try:
                        modifier_parameters.remove(parameter_name)
                    except KeyError:
                        pass
                    else:
                        parsed_parameters[parameter_name] = True
                        continue
                
                try:
                    keyword_parameter = parameters_keyword_only[parameter_name]
                except KeyError:
                    # TODO
                    return
                
                if index == parameter_count:
                    # TODO
                    return
                
                parameter_value = parameters[index]
                index += 1
                
                parameter_value = keyword_parameter.convert(parameter_value)
                if parameter_value is None:
                    # TODO
                    return
                
                if keyword_parameter.multi:
                    try:
                        parameter_value = parsed_parameters[parameter_name]
                    except KeyError:
                        parameter_value = []
                        parsed_parameters[parameter_name] = parameter_value
                    
                    parameter_value.append(parameter_value)
                
                else:
                    del parameters_keyword_only[parameter_name]
                    parsed_parameters[parameter_name] = parameter_value
            
            for parameter_name, parameter in parameters_keyword_only.items():
                if parameter.multi:
                    parameter_value = []
                else:
                    parameter_value = parameter.default
                
                parsed_parameters[parameter_name] = parameter_value
        
        if (modifier_parameters is not None):
            for parameter_name in modifier_parameters:
                parsed_parameters[parameter_name] = False
        
        if index != parameter_count:
            # TODO
            return
        
        self._function(parsed_parameters)