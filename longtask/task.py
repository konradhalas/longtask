import progressbar
import argparse
import traceback
from longtask import storage, widgets, utils
from datetime import datetime


class Task(object):
    storage_class = storage.JSONStorage

    def __init__(self, commandline=False, **kwargs):
        parser = self.get_parser()
        self.options = parser.parse_args(args=None if commandline else [], namespace=argparse.Namespace(**kwargs))
        self.storage = self.storage_class(self)
        data = {}
        if self.options.continue_task:
            data = self.storage.load()
        self.set_internal_data(data)

    def set_internal_data(self, data=None):
        data = data or {}
        self.processed = data.get('processed', 0)
        self.items_len = data.get('items_len', self.get_items_len())
        self.errors = data.get('errors', {})
        self.errored_items = []
        for error_name in self.errors:
            for traceback in self.errors[error_name]:
                self.errored_items += self.errors[error_name][traceback]

    def get_internal_data(self):
        return {
            'processed': self.processed,
            'items_len': self.items_len,
            'errors': self.errors
        }

    def get_parser(self):
        parser = argparse.ArgumentParser(description='{0} task runner.'.format(self.get_name()))
        parser.add_argument('--quiet', '-q', action='store_true', help='quiet mode')
        parser.add_argument('--continue', '-c', dest='continue_task', action='store_true', help='continue task')
        parser.add_argument('--verbose', '-v', dest='verbose', action='store_true', help='print errors during execution')
        return parser

    def run(self):
        with utils.OutputManager(disable=self.options.quiet) as output:
            if self.is_finished():
                self.set_internal_data()
            self.print_start_message()

            progress = self.get_progress_bar(output)
            progress.start()

            for index, item in enumerate(self.get_items(), start=1):
                if self.should_process_item(index, item):
                    try:
                        self.process_item(item)
                    except KeyboardInterrupt:
                        break
                    except Exception as error:
                        self.handle_error(item, error)
                    self.processed += 1
                progress.update(index)

            self.print_finish_message()
            self.storage.save(self.get_internal_data())

    def get_progress_bar(self, output):
        return progressbar.ProgressBar(
            widgets=self.get_progress_bar_widgets(),
            maxval=self.get_items_len(),
            fd=output.stderr
        )

    def get_progress_bar_widgets(self):
        return [
            '[*] Processed: ', progressbar.Percentage(), ' (', progressbar.Counter(), '/',
            str(self.get_items_len()), ') errors: ', widgets.ErrorsPercentage(self), ' (', widgets.ErrorsCounter(self), '/',
            str(self.get_items_len()), ') ', progressbar.Bar(), ' ', progressbar.Timer(), ' ', progressbar.ETA()]

    def print_error(self, item, error):
        print('\n\nException {0} for item {1}:\n'.format(repr(error), item))
        print(traceback.format_exc())
        print

    def handle_error(self, item, error):
        if self.options.verbose:
            self.print_error(item, error)
        tb = traceback.format_exc()
        error_name = error.__class__.__name__
        if error_name not in self.errors:
            self.errors[error_name] = {}
        if tb not in self.errors[error_name]:
            self.errors[error_name][tb] = []
        self.errors[error_name][tb].append(self.get_item_id(item))
        self.errored_items.append(self.get_item_id(item))

    def print_start_message(self):
        print('[*] Starting task: {0} [{1}]'.format(self.get_name(), datetime.now()))
        if self.options.continue_task:
            print('[*] Previous run stats:')
            self.print_stats()

    def print_finish_message(self):
        print('\n[*] Finished task: {0} [{1}]'.format(self.get_name(), datetime.now()))
        print('[*] Stats:')
        self.print_stats()

    def print_stats(self):
        print(' - processed: {0}'.format(utils.as_percent(self.processed, self.items_len)))
        print(' - success: {0}'.format(utils.as_percent(self.processed - len(self.errored_items), self.items_len)))
        print(' - errors: {0}'.format(utils.as_percent(len(self.errored_items), self.items_len)))
        for error_name in self.errors:
            for tb in self.errors[error_name]:
                print('   - {0} x {1}\n'.format(len(self.errors[error_name][tb]), error_name))
                print(tb)

    def get_name(self):
        return self.name

    def get_items_len(self):
        return len(self.get_items())

    def get_item_name(self, item):
        return repr(item)

    def get_item_id(self, item):
        return item

    def should_process_item(self, index, item):
        return not (self.options.continue_task and index <= self.processed < self.items_len)

    def is_finished(self):
        return self.processed == self.items_len

    def get_items(self):
        raise NotImplementedError()

    def process_item(self, item):
        raise NotImplementedError()
