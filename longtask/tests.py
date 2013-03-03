import unittest
import longtask

class MockStorage(longtask.PickleStorage):

    def load(self):
        return {}

    def save(self):
        self.saved = True


class MockTask(longtask.Task):
    name = 'mock'
    storage_class = MockStorage

    def __init__(self, exception=None, raise_condition=lambda i: True, items=range(10), **kwargs):
        super(MockTask, self).__init__(quiet=True, **kwargs)
        self.exception = exception
        self.items = items
        self.raise_condition = raise_condition

    def process_item(self, item):
        if self.exception and self.raise_condition(item):
            raise self.exception

    def get_items(self):
        return self.items

    def get_item_id(self, item):
        return item


class TaskTest(unittest.TestCase):

    def test_run(self):
        task = MockTask()

        task.run()

        self.assertEqual(task.processed, task.get_items_len())
        self.assertEqual(task.successes, task.get_items_len())
        self.assertFalse(task.errors)

    def test_keyboard_interrupt(self):
        task = MockTask(exception=KeyboardInterrupt)

        task.run()

        self.assertFalse(task.processed)
        self.assertFalse(task.successes)
        self.assertFalse(task.errors)

    def test_exception(self):
        task = MockTask(exception=Exception)

        task.run()

        self.assertEqual(task.processed, task.get_items_len())
        self.assertFalse(task.successes)
        self.assertEqual(task.errors, task.get_items_len())

    def test_store_error(self):
        task = MockTask(exception=Exception)

        task.run()

        item = task.get_items()[0]
        error = task.storage.data['errors'][item]
        self.assertEqual(error['name'], repr(item))
        self.assertEqual(error['class'], task.exception.__class__)
        self.assertEqual(error['traceback'], '')
        self.assertTrue(task.storage.saved)

    def test_store_stats(self):
        task = MockTask()

        task.run()

        self.assertEqual(task.storage.data['processed'], task.processed)

    def test_continue(self):
        task = MockTask(continue_task=True)
        first_run = task.get_items_len() / 2
        task.storage.data['processed'] = first_run

        task.run()

        self.assertEqual(task.processed_run, task.get_items_len() - first_run)

    def test_rerun_errors(self):
        self.fail()

    def test_merge_errors(self):
        self.fail()

    def test_task_stop_exception(self):
        self.fail()

