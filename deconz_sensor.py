import appdaemon.plugins.hass.hassapi as hass
import datetime


class DeconzSensor(hass.Hass):
    """Hacs class."""

    def initialize(self):
        """Initialize the HACS app."""
        self.id = self.args['id']
        self.log(f'Hello for DeconzSensor {self.id}')

        self.default_actions = self.args.get('default_actions', {'on': None, 'off': None})

        # Build intervals based actions
        actions = self.args.get('actions', [])
        self.intervals = []
        for action in actions:
            key_to_check = ['start', 'end']
            for key in key_to_check:
                if key not in action:
                    self.log(f'You should have key {key} in your action config {action}', level='WARNING')
                    return

            start = action['start']
            end = action['end']

            start_hour = start.get('hour', 0)
            start_minute = start.get('minute', 0)
            start_second = start.get('second', 0)

            end_hour = end.get('hour', 0)
            end_minute = end.get('minute', 0)
            end_second = end.get('second', 0)

            start_time = datetime.time(start_hour, start_minute, start_second)
            end_time = datetime.time(end_hour, end_minute, end_second)

            is_overlapping = False
            for interval in self.intervals:
                test_start = interval['start']
                test_end = interval['end']
                if start_time > test_start and start_time < test_end:
                    self.log(f'Overlapping {start_time} between {test_start} and {test_end}')
                    is_overlapping = True
                    break
                elif end_time > test_start and end_time < test_end:
                    self.log(f'Overlapping {end_time} between {test_start} and {test_end}')
                    is_overlapping = True
                    break
                elif test_start > start_time and test_start < end_time:
                    self.log(f'Existing overlapping {test_start} between {start_time} and {end_time}')
                    is_overlapping = True
                elif test_end > start_time and test_end < end_time:
                    self.log(f'Existing overlapping {test_end} between {start_time} and {end_time}')
                    is_overlapping = True
            if is_overlapping:
                self.log('Skipping this interval because overlapping')
                continue

            new_interval = {
                'start': start_time,
                'end': end_time,
            }
            if 'on' in action:
                new_interval['on'] = action['on']
            if 'off' in action:
                new_interval['off'] = action['off']
            self.intervals.append(new_interval)

        self.listen_state(self.motion, self.id)

    def motion(self, entity, attribute, old, new, kwargs):
        now = datetime.datetime.now().time()

        wanted_interval = None
        for interval in self.intervals:
            if now > interval['start'] and now < interval['end']:
                wanted_interval = interval
                break

        if not wanted_interval:
            self.log(f'No interval for {now}, going default')
            wanted_interval = self.default_actions
        elif new not in wanted_interval:
            self.log(f'No "{new}" action in wanted_interval {wanted_interval}, going default')
            wanted_interval = self.default_actions

        if new not in wanted_interval:
            self.log(f'No actions associated with state {new}')
            return

        action = wanted_interval.get(new)
        service = action.get('service', None)
        args = action.get('args', {})
        if not service:
            self.log('No service in action {action}')
            return

        self.log(f'triggering service {service} with args {args}')
        self.call_service(service, **args)
        return
