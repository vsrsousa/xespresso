class SchedulerBase:
    def __init__(self, calc, command, queue):
        self.calc = calc
        self.command = command
        self.queue = queue

    def generate_script(self):
        raise NotImplementedError

    def get_submission_command(self):
        raise NotImplementedError

