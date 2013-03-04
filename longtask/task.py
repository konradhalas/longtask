import progressbar
import argparse
import traceback
from longtask import storage, widgets, utils
from datetime import datetime


class Task(object):
    storage_class = storage.JSONStorage

    def __init__(self, commandline=True, **kwargs):
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
        self.errored_items = set()
        for error_name in self.errors:
            for traceback in self.errors[error_name]:
                self.errored_items.update(self.errors[error_name][traceback])
        if self.options.rerun_errors:
            self.errors = {}

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
        parser.add_argument('--verbose', '-v', dest='verbose', action='store_true', help='print errors')
        parser.add_argument('--errors', '-e', dest='rerun_errors', action='store_true', help='rerun errors')
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
                        item_id = self.get_item_id(item)
                        try:
                            self.errored_items.remove(item_id)
                        except KeyError:
                            pass
                    except KeyboardInterrupt:
                        break
                    except Exception as error:
                        self.handle_error(item, error)
                    if index > self.processed:
                        self.processed += 1
                progress.update(index)

            self.print_finish_message()
            self.storage.save(self.get_internal_data())

    def get_progress_bar(self, output):
        return progressbar.ProgressBar(
            widgets=self.get_progress_bar_widgets(),
            maxval=self.items_len,
            fd=output.stderr
        )

    def get_progress_bar_widgets(self):
        return [
            '[*] Processed: ', progressbar.Percentage(), ' (', progressbar.Counter(), '/',
            str(self.items_len), ') errors: ', widgets.ErrorsPercentage(self), ' (', widgets.ErrorsCounter(self), '/',
            str(self.items_len), ') ', progressbar.Bar(), ' ', progressbar.Timer(), ' ', progressbar.ETA()]

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
        self.errored_items.add(self.get_item_id(item))

    def print_error(self, item, error):
        print('\n\nException {0} for item {1}:\n'.format(repr(error), item))
        print(traceback.format_exc())
        print

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
        as_percent = lambda x, y: '{0}% ({1}/{2})'.format((100 * x / y) if y else 0, x, y)
        print(' - processed: {0}'.format(as_percent(self.processed, self.items_len)))
        print(' - success: {0}'.format(as_percent(self.processed - len(self.errored_items), self.items_len)))
        print(' - errors: {0}'.format(as_percent(len(self.errored_items), self.items_len)))
        for error_name in self.errors:
            for tb in self.errors[error_name]:
                print('   - {0} x {1} with traceback:\n'.format(len(self.errors[error_name][tb]), error_name))
                print(tb)

    def should_process_item(self, index, item):
        if self.options.rerun_errors and self.get_item_id(item) in self.errored_items:
            return True
        if self.options.continue_task and index <= self.processed:
            return False
        return True

    def is_finished(self):
        processed_all_items = self.processed == self.items_len
        if self.options.rerun_errors and self.options.continue_task:
            return processed_all_items and not self.errored_items
        return processed_all_items

    def get_name(self):
        return self.name

    def get_item_id(self, item):
        return item

    def get_items_len(self):
        return len(self.get_items())

    def get_items(self):
        raise NotImplementedError()

    def process_item(self, item):
        raise NotImplementedError()
