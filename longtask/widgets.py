import progressbar


class TaskWidget(progressbar.Widget):

    def __init__(self, task):
        self.task = task


class ErrorsCounter(TaskWidget):

    def update(self, _):
        return str(len(self.task.errored_items))


class ErrorsPercentage(TaskWidget):

    def update(self, _):
        return '{0:3}%'.format(100 * len(self.task.errored_items) / self.task.items_len)
