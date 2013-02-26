import progressbar
import argparse
import pickle


class ErrorsCounter(progressbar.Widget):

    def __init__(self, task):
        self.task = task

    def update(self, pbar):
        return str(self.task.errors)


class ErrorsPercentage(ErrorsCounter):

    def __init__(self, task):
        self.task = task

    def update(self, pbar):
        return '%3d%%' % (100 * self.task.errors / self.task.get_items_len())


class PickleStorage(object):

    def __init__(self, task):
        self.task = task
        self.data = {'errors': {}}

    def store_error(self, item, error):
        self.data['errors'][self.task.get_item_id(item)] = {
            'name': self.task.get_item_name(item)
        }

    def store_stats(self, processed):
        self.data['processed'] = processed

    def save(self):
        with open(self.get_file_name(), 'w') as f:
            pickle.dump(self.data, f)

    def load(self):
        try:
            with open(self.get_file_name(), 'r') as f:
                self.data.update(pickle.load(f))
        except IOError:
            pass

    def get_file_name(self):
        return '.{0}.task'.format(self.task.get_name())


class Task(object):
    storage_class = PickleStorage

    def __init__(self, commandline=False, **kwargs):
        parser = self.get_parser()
        self.options = parser.parse_args(args=None if commandline else [], namespace=argparse.Namespace(**kwargs))
        self.storage = self.storage_class(self)
        self.storage.load()

    def get_parser(self):
        parser = argparse.ArgumentParser(description='{0} task runner.'.format(self.get_name()))
        parser.add_argument('--quiet', '-q', action='store_true', help='quiet mode')
        parser.add_argument('--continue', '-c', dest='continue_task', action='store_true', help='continue task')
        return parser

    def run(self):
        self.processed = 0
        self.successes = 0
        self.errors = 0

        progress = self.get_progress_bar()

        if not self.options.quiet:
            progress.start()

        for index, item in enumerate(self.get_items()):
            try:
                if self.options.continue_task and self.storage.data.get('processed') and self.storage.data.get('processed') > index and self.storage.data.get('processed') != self.get_items_len():
                    pass
                else:
                    self.process_item(item)
                    self.successes += 1
            except KeyboardInterrupt:
                break
            except Exception as error:
                self.errors += 1
                if not self.options.quiet:
                    self.print_error(item, error)
                self.storage.store_error(item, error)
            if not self.options.quiet:
                progress.update(index)
            self.processed += 1

        if not self.options.quiet:
            self.print_stats()

        self.storage.store_stats(self.processed)
        self.storage.save()

    def get_progress_bar(self):
        return progressbar.ProgressBar(
            widgets=self.get_progress_bar_widgets() if not self.options.quiet else [],
            maxval=self.get_items_len()
        )

    def get_progress_bar_widgets(self):
        return [self.get_name(), ': ', progressbar.Percentage(), ' (', progressbar.Counter(), '/',
            str(self.get_items_len()), ') errors: ', ErrorsPercentage(self), ' (', ErrorsCounter(self), '/',
            str(self.get_items_len()), ') ', progressbar.Bar(), ' ', progressbar.Timer(), ' ', progressbar.ETA()]

    def print_error(self, item, error):
        print('\n\nERROR')
        print(item)
        print(error)

    def print_stats(self):
        print('\n\nStats:')
        print(' - processed: ' + str(self.processed))
        print(' - successes: ' + str(self.successes))
        print(' - errors: ' + str(self.errors))

    def get_name(self):
        return self.name

    def get_items_len(self):
        return len(self.get_items())

    def get_item_name(self, item):
        return repr(item)

    def get_item_id(self, item):
        return item

