__all__ = ()

import sys

from ...discord.activity import ActivityRich
from ...discord.channel import CHANNEL_TYPES, ChannelGuildUndefined

from .dispatch_handling import DISPATCH_EVENT_HANDLERS
from .constants import PAYLOAD_KEY_EVENT, PAYLOAD_KEY_DATA, PAYLOAD_KEY_NONCE, PAYLOAD_COMMAND_DISPATCH, \
    PAYLOAD_COMMAND_CERTIFIED_DEVICES_SET, PAYLOAD_COMMAND_ACTIVITY_SET, PAYLOAD_COMMAND_VOICE_SETTINGS_SET, \
    PAYLOAD_COMMAND_VOICE_SETTINGS_GET, PAYLOAD_COMMAND_CHANNEL_TEXT_SELECT, PAYLOAD_COMMAND_CHANNEL_VOICE_GET
from .voice_settings import VoiceSettings



def handle_command_dispatch(self, data):
    dispatch_event_name = data[PAYLOAD_KEY_EVENT]
    try:
        dispatch_event_handler = DISPATCH_EVENT_HANDLERS[dispatch_event_name]
    except KeyError:
        sys.stderr.write(
            f'{self!r} cannot handle dispatch event {dispatch_event_name!r}.\n'
            f'Received data: {data!r}\n'
        )
        return
    
    dispatch_event_handler(self, data[PAYLOAD_KEY_DATA])


def handle_command_certified_devices_set(self, data):
    try:
        nonce = data[PAYLOAD_KEY_NONCE]
    except KeyError:
        pass
    else:
        try:
            waiter = self._response_waiters[nonce]
        except KeyError:
            pass
        else:
            waiter.set_result_if_pending(None)


def handle_command_activity_get(self, data):
    nonce = data.get(PAYLOAD_KEY_NONCE)
    if (nonce is None):
        return
    
    try:
        response_waiter = self._response_waiters[nonce]
    except KeyError:
        return
    
    activity = ActivityRich.from_data(data[PAYLOAD_KEY_DATA])
    response_waiter.set_result_if_pending(activity)


def handle_command_voice_settings_set_and_get(self, data):
    nonce = data.get(PAYLOAD_KEY_NONCE)
    if (nonce is None):
        return
    
    try:
        response_waiter = self._response_waiters[nonce]
    except KeyError:
        return
    
    voice_settings = VoiceSettings.from_data(data[PAYLOAD_KEY_DATA])
    response_waiter.set_result_if_pending(voice_settings)


def handle_command_channel_select_and_get(self, data):
    nonce = data.get(PAYLOAD_KEY_NONCE)
    if (nonce is None):
        return
    
    try:
        response_waiter = self._response_waiters[nonce]
    except KeyError:
        return
    
    channel_data = data.get(PAYLOAD_KEY_DATA, None)
    if (channel_data is None):
        channel = None
    else:
        channel = CHANNEL_TYPES.get(channel_data['type'], ChannelGuildUndefined)(channel_data, self)
    
    response_waiter.set_result_if_pending(channel)


COMMAND_HANDLERS = {
    PAYLOAD_COMMAND_DISPATCH: handle_command_dispatch,
    PAYLOAD_COMMAND_CERTIFIED_DEVICES_SET: handle_command_certified_devices_set,
    PAYLOAD_COMMAND_ACTIVITY_SET: handle_command_activity_get,
    PAYLOAD_COMMAND_VOICE_SETTINGS_SET: handle_command_voice_settings_set_and_get,
    PAYLOAD_COMMAND_VOICE_SETTINGS_GET: handle_command_voice_settings_set_and_get,
    PAYLOAD_COMMAND_CHANNEL_TEXT_SELECT: handle_command_channel_select_and_get,
    PAYLOAD_COMMAND_CHANNEL_VOICE_GET: handle_command_channel_select_and_get,
}

del handle_command_dispatch
del handle_command_certified_devices_set
del handle_command_activity_get
del handle_command_voice_settings_set_and_get
del handle_command_channel_select_and_get
