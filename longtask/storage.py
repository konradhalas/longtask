import json


class Storage(object):

    def __init__(self, task):
        self.task = task

    def save(self, data):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError


class JSONStorage(Storage):

    def save(self, data):
        with open(self.get_file_name(), 'w') as f:
            json.dump(data, f, indent=4)

    def load(self):
        data = {}
        try:
            with open(self.get_file_name(), 'r') as f:
                data = json.load(f)
        except IOError:
            pass
        return data

    def get_file_name(self):
        task_name = self.task.get_name().lower().replace(' ', '_')
        return '.{0}.task'.format(task_name)
