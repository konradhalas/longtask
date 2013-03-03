import unittest
from longtask import storage, task


class MockStorage(storage.Storage):

    def load(self):
        return {}

    def save(self, data):
        self.saved = True


class MockTask(task.Task):
    name = 'mock'
    storage_class = MockStorage

    def __init__(self, exception=None, raise_condition=lambda i: True, items=None, **kwargs):
        self.exception = exception
        self.items = items or range(10)
        self.raise_condition = raise_condition
        self.processed_items = []
        super(MockTask, self).__init__(quiet=True, **kwargs)

    def process_item(self, item):
        if self.exception and self.raise_condition(item):
            raise self.exception
        self.processed_items.append(item)

    def get_items(self):
        return self.items

    def get_item_id(self, item):
        return item


class TaskTest(unittest.TestCase):

    def test_run(self):
        task = MockTask()

        task.run()

        self.assertEqual(task.processed, task.get_items_len())

    def test_keyboard_interrupt(self):
        task = MockTask(exception=KeyboardInterrupt)

        task.run()

        self.assertFalse(task.processed)
        self.assertFalse(task.errors)

    def test_exception(self):
        task = MockTask(exception=Exception)

        task.run()

        self.assertEqual(task.processed, task.get_items_len())
        self.assertTrue(task.errors)

    def test_store_error(self):
        task = MockTask(exception=Exception)

        task.run()

        self.assertTrue(task.errors)

    def test_continue(self):
        task = MockTask(continue_task=True)
        first_run = task.get_items_len() / 2
        task.processed = first_run

        task.run()

        self.assertEqual(len(task.processed_items), task.get_items_len() - first_run)
