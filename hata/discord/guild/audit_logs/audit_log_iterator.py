__all__ = ('AuditLogIterator', )

from ...bases import maybe_snowflake
from ...user import ClientUserBase
from ...utils import now_as_id

from ..guild import Guild
from ..utils import create_partial_guild_from_id

from .audit_log import AuditLog
from .audit_log_entry import AuditLogEntry
from .preinstanced import AuditLogEvent


class AuditLogIterator(AuditLog):
    """
    An async iterator over a guild's audit logs.
    
    Attributes
    ----------
    _self_reference : `None` or ``WeakReferer`` to ``AuditLog``
        Weak reference to the audit log itself.
    entries : `list` of ``AuditLogEntry``
        A list of audit log entries, what the audit log contains.
    guild : ``Guild``
        The audit logs' respective guild.
    integrations : `dict` of (`int`, ``Integration``) items
        A dictionary what contains the mentioned integrations by the audit log's entries. The keys are the `id`-s of
        the integrations, meanwhile the values are the integrations themselves.
    scheduled_events : `dict` of (`int`, ``ScheduledEvent``) items
        A dictionary containing the scheduled events mentioned inside of the audit logs.
    threads : `dict` of (`int`, ``Channel``) items
        A dictionary containing the mentioned threads inside of the audit logs.
    users : `dict` of (`int`, ``ClientUserBase``) items
        A dictionary, what contains the mentioned users by the audit log's entries. The keys are the `id`-s of the
        users, meanwhile the values are the users themselves.
    webhooks : `dict` of (`int`, ``Webhook``) items
        A dictionary what contains the mentioned webhook by the audit log's entries. The keys are the `id`-s of the
        webhooks, meanwhile the values are the values themselves.
    
    _data : `dict` of (`str`, `Any`) items
        Data to be sent to Discord when requesting an another audit log chunk. Contains some information, which are not
        stored by any attributes of the audit log iterator, these are the filtering `user` and `event` options.
    _index : `int`
        The next audit log entries index to yield.
    client : ``Client``
        The client, who will execute the api requests.
    """
    __slots__ = ('_data', '_index', 'client',)
    
    async def __new__(cls, client, guild, user=None, event=None):
        """
        Creates an audit log iterator with the given parameters.
        
        This method is a coroutine.
        
        Parameters
        ----------
        client : ``Client``
            The client, who will execute the api requests.
        guild : ``Guild``, `int`
            The guild, what's audit logs will be requested.
        user : `None`, ``ClientUserBase``, `int` = `None`, Optional
            Whether the audit logs should be filtered only to those, which were created by the given user.
        event : `None`, ``AuditLogEvent``, `int` = `None`, Optional
            Whether the audit logs should be filtered only on the given event.
        
        Raises
        ------
        TypeError
            - If `guild` was not given neither as ``Guild``, nor as `int`.
            - If `user` was not given neither as `None`, ``ClientUserBase`` nor as `int`.
            - If `event` as not not given neither as `None`, ``AuditLogEvent`` nor as `int`.
        ConnectionError
            No internet connection.
        DiscordException
            If any exception was received from the Discord API.
        """
        data = {
            'limit': 100,
            'before': now_as_id(),
        }
        
        if isinstance(guild, Guild):
            guild_id = guild.id
        else:
            guild_id = maybe_snowflake(guild)
            if guild_id is None:
                raise TypeError(
                    f'`guild_or_discovery` can be `{Guild.__name__}`, `int`, got '
                    f'{guild.__class__.__name__}; {guild!r}.'
                )
            
            guild = None
        
        if (user is not None):
            if isinstance(user, ClientUserBase):
                user_id = user.id
            
            else:
                user_id = maybe_snowflake(user)
                if user_id is None:
                    raise TypeError(
                        f'`user` can be `{ClientUserBase.__name__}`, `int`, got'
                        f'{user.__class__.__name__}; {user!r}.'
                    )
            
            data['user_id'] = user_id
        
        if (event is not None):
            if isinstance(event, AuditLogEvent):
                event_value = event.value
            elif isinstance(event, int):
                event_value = event
            else:
                raise TypeError(
                    f'`event` can be `None`, `{AuditLogEvent.__name__}`, `int`, got '
                    f'{event.__class__.__name__}; {event!r}.'
                )
            
            data['action_type'] = event_value
        
        if guild is None:
            log_data = await client.http.audit_log_get_chunk(guild_id, data)
            if guild is None:
                guild = create_partial_guild_from_id(guild_id)
        else:
            log_data = None
        
        self = AuditLog.__new__(cls, data, guild)
        self._data = data
        self._index = 0
        self.client = client
        
        if (log_data is not None):
            self._populate(log_data)
        
        return self
    
    
    async def load_all(self):
        """
        Loads all not yet loaded audit logs of the audit log iterator's guild.
        
        This method is a coroutine.
        """
        entries = self.entries
        client = self.client
        http = client.http
        data = self._data
        
        while True:
            if entries:
                data['before'] = entries[-1].id
            
            log_data = await http.audit_log_get_chunk(self.guild.id, data)
            
            if not self._populate(log_data):
                return
            
            if len(entries) % 100:
                return
    
    
    def transform(self):
        """
        Converts the audit log iterator to an audit log object.
        
        Returns
        -------
        audit_log : ``AuditLog``
        """
        audit_log = object.__new__(AuditLog)
        audit_log.entries = self.entries
        audit_log.guild = self.guild
        audit_log.integrations = self.integrations
        audit_log.scheduled_events = self.scheduled_events
        audit_log.threads = self.threads
        audit_log.users = self.users
        audit_log.webhooks = self.webhooks
        return audit_log
    
    
    def __aiter__(self):
        """Returns self and resets the `.index`."""
        self._index = 0
        return self
    
    
    async def __anext__(self):
        """
        Yields the next entry of the audit log iterator.
        
        This method is a coroutine.
        """
        ln = len(self.entries)
        index = self._index
        
        if index < ln:
            self._index += 1
            return self.entries[index]
        
        if index % 100:
            raise StopAsyncIteration
        
        data = self._data
        if ln:
            data['before'] = self.entries[ln - 1].id
        
        log_data = await self.client.http.audit_log_get_chunk(self.guild.id, data)
        
        
        if not self._populate(log_data):
            raise StopAsyncIteration
        
        self._index += 1
        return self.entries[index]
