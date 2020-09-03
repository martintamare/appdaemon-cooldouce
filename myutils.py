import time

current_time = lambda: int(round(time.time() * 1000))

class SwitchButton():
    def __init__(self, delay, log):
        self.log = log
        self.state = 0
        self.last_short_press = None
        self.last_long_press = None
        self.delay = delay

    def debug(self, message):
        self.log(message, level='DEBUG')

    def short_press(self):
        press_time = current_time()
        if self.last_short_press is None:
            self.state += 1
            self.debug('+state {0}'.format(self.state))
        else:
            delay = press_time - self.last_short_press
            self.debug('delay since last press {0}'.format(delay))
            if delay > self.delay:
                self.state = 1
                self.debug('=state {0}'.format(self.state))
            else:
                self.state += 1
                self.debug('+state {0}'.format(self.state))
        self.last_short_press = press_time

    def long_press(self):
        self.log('long_press', level='DEBUG')

