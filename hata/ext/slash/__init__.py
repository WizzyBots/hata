"""
Hata extensions for supporting interactions.
"""
from .application_command import *
from .components import *
from .component_command import *
from .converters import *
from .custom_id_based_command import *
from .event_handlers import *
from .exceptions import *
from .expression_parser import *
from .form_submit_command import *
from .helpers import *
from .responding import *
from .response_modifier import *
from .slasher import *
from .utils import *
from .waiters import *
from .wrappers import *

__all__ = (
    'P',
    'configure_parameter',
    'set_permission',
    'setup_ext_slash',
    *application_command.__all__,
    *components.__all__,
    *component_command.__all__,
    *converters.__all__,
    *custom_id_based_command.__all__,
    *event_handlers.__all__,
    *exceptions.__all__,
    *expression_parser.__all__,
    *form_submit_command.__all__,
    *helpers.__all__,
    *responding.__all__,
    *response_modifier.__all__,
    *slasher.__all__,
    *utils.__all__,
    *waiters.__all__,
    *wrappers.__all__,
)

from .. import register_library_extension, add_library_extension_hook, register_setup_function

from .event_handlers import _do_initial_sync, _application_command_create_watcher, \
    _application_command_delete_watcher, _application_command_permission_update_watcher
from .client_wrapper_extension import *

set_permission = SlasherApplicationCommandPermissionOverwriteWrapper
configure_parameter = SlasherApplicationCommandParameterConfigurerWrapper
P = SlashParameter


def setup_ext_slash(client, **kwargs):
    """
    Setups the slash extension on client.
    
    Note, that this function can be called on a client only once.
    
    Parameters
    ----------
    client : ``Client``
        The client to setup the extension on.
    **kwargs : Keyword parameters
        Additional keyword parameter to be passed to the created ``Slasher``.
    
    Other Parameters
    ----------------
    delete_commands_on_unload: `bool`, Optional
        Whether commands should be deleted when unloaded.
    use_default_exception_handler : `bool`, Optional
        Whether the default slash exception handler should be added as an exception handler.
    random_error_message_getter : `None`, `FunctionType` = `None`, Optional
        Random error message getter used by the default exception handler.
    translation_table : `None`, `str`, `dict` of ((``Locale``, `str`),
            (`None`, `dict` of (`str`, (`None`, `str`)) items)) items, Optional
        Translation table for the commands of the slasher.
    
    Returns
    -------
    slasher : ``Slasher``
        Slash command processor.
    
    Raises
    ------
    RuntimeError
        If the client has an attribute set what the slasher would use.
    FileNotFoundError
        - If `translation_table` is a string, but not a file.
    TypeError
        - If `client` was not given as ``Client`` instance.
        - If `delete_commands_on_unload` was not given as `bool` instance.
        - If `use_default_exception_handler` was not given as `bool` instance.
        - If `translation_table`'s structure is incorrect.
    """
    for attr_name in ('slasher', 'interactions'):
        if hasattr(client, attr_name):
            raise RuntimeError(f'The client already has an attribute named as `{attr_name}`.')
    
    slasher = Slasher(client, **kwargs)
    
    client.events(slasher)
    client.slasher = slasher
    client.interactions = slasher.shortcut
    client.events(_do_initial_sync, name='launch')
    client.events(_application_command_create_watcher, name='application_command_create')
    client.events(_application_command_delete_watcher, name='application_command_delete')
    client.events(_application_command_permission_update_watcher, name='application_command_permission_update')
    
    return slasher


def snapshot_hook():
    from . import snapshot


register_library_extension('HuyaneMatsu.slash')
add_library_extension_hook(snapshot_hook, ['HuyaneMatsu.extension_loader'])

register_setup_function(
    'HuyaneMatsu.slash',
    setup_ext_slash,
    None,
    (
        'delete_commands_on_unload',
        'use_default_exception_handler',
        'random_error_message_getter',
        'translation_table',
    ),
)
