import appdaemon.plugins.hass.hassapi as hass
import logging
import pprint

from myutils import SwitchButton

#
# App that allow flexible configuration of the hue dimmer as well as multiple button press
#
# Args:
#
#  delay_for_modes: 1500
#
#  light_ids:
#    - light.some_light
#
#  button_on_short_press_actions:
#    - service: light/turn_on
#      args:
#        color_name: blue
#    - service: light/turn_on
#      args:
#        color_name: orange
#    - service: light/turn_on
#      args:
#        color_name: green
#    - service: light/turn_on
#      args:
#        color_name: red
#    - service: light/turn_on
#      args:
#        color_name: yellow
#    
#  button_off_short_press_actions:
#    - service: light/turn_off
#    - service: light/turn_off
#      args:
#        entity_id: all
#
#  dim_up_short_press_actions:
#    - service: light/turn_on
#      args:
#        transition: 1
#        brightness_delta: 25
#  dim_up_long_press_actions:
#    - service: light/turn_on
#      args:
#        transition: 1
#        brightness_delta: 25
#
#  dim_down_short_press_actions:
#    - service: light/turn_on
#      args:
#        transition: 1
#        brightness_delta: -25
#  dim_down_long_press_actions:
#    - service: light/turn_on
#      args:
#        transition: 1
#        brightness_delta: -25

SHORT_PRESS_START = 0
LONG_PRESS_START = 1
SHORT_PRESS_STOP = 2
LONG_PRESS_STOP = 3


class DeconzSwitch(hass.Hass):

    def initialize(self):
        self.LOGLEVEL = 'DEBUG'

        # Args parsing
        self.log_name = self.args.get('log', None)
        self.id = self.args['id']
        self.delay_for_modes = self.args.get('delay_for_modes', 1500)
        self.buttons_actions = self.args.get('buttons_actions', [])

        self.log(f'Hello from DeconzSwitch {self.id}')

        self.button = []
        self.button.append(SwitchButton(delay=self.delay_for_modes, log=self.log))
        self.button.append(SwitchButton(delay=self.delay_for_modes, log=self.log))
        self.button.append(SwitchButton(delay=self.delay_for_modes, log=self.log))
        self.button.append(SwitchButton(delay=self.delay_for_modes, log=self.log))

        self.listen_event(self.deconz_event, 'deconz_event', id=self.id)

    def deconz_event(self, event_id, payload_event, *args):
        """Called on every event received from the switch."""
        # Get the event
        event = payload_event['event']

        # Extract button and code
        # Code
        # 0 : short_press_start : unsed
        # 1 : long_press_start
        # 2 : short_press_stop
        # 3 : long_press_stop : unsed
        button_index = int(str(event)[0]) - 1
        code = int(str(event)[1:4])

        # Handle the press to compute state of the button
        if code == SHORT_PRESS_STOP:
            self.log(f'{self.id} short_press button {button_index}')
            self.button[button_index].short_press()
        elif code == LONG_PRESS_START:
            self.log(f'{self.id} long_press button {button_index}')
            self.button[button_index].long_press()

        # We only handle action on press
        if code not in [SHORT_PRESS_STOP, LONG_PRESS_START]:
            return

        service = None
        args = None

        if button_index + 1 > len(self.buttons_actions):
            self.log('I got nothing to do :/')
            return
        actions = self.buttons_actions[button_index]

        action = None
        if code == SHORT_PRESS_STOP:
            if 'short_press' not in actions:
                self.log(f'Button {button_index} has nothing to do in short_press')
                return
            action = actions['short_press']
        elif code == LONG_PRESS_START:
            if 'long_press' not in actions:
                self.log(f'Button {button_index} has nothing to do in long_Press')
                return
            action = actions['long_press']

        if action is None:
            return

        if 'service' not in action:
            self.warning('weird stuff no service')
            return
        service = action['service']
        args = action['args']

        self.log(f'triggering service {service} with args {args}')
        self.call_service(service, **args)

        return
