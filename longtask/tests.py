import unittest
from mock import Mock
from longtask import task, storage


class TaskTest(unittest.TestCase):

    def setUp(self):
        self.MockTask = task.Task
        self.MockTask.process_item = Mock()
        self.MockTask.name = 'mock'
        self.MockTask.get_items = Mock(return_value=range(10))
        self.MockStorage = storage.Storage
        self.MockStorage.save = Mock()
        self.MockStorage.load = Mock(return_value={})
        self.MockTask.storage_class = self.MockStorage
        self.mock_task = self.MockTask(commandline=False, quiet=True)

    def test_run(self):
        self.mock_task.run()

        self.assertTrue(self.mock_task.is_finished())

    def test_keyboard_interrupt(self):
        self.mock_task.process_item = Mock(side_effect=KeyboardInterrupt)

        self.mock_task.run()

        self.assertFalse(self.mock_task.is_finished())

    def test_exception(self):
        self.mock_task.process_item = Mock(side_effect=Exception)

        self.mock_task.run()

        self.assertTrue(self.mock_task.is_finished())
        self.assertTrue('Exception' in self.mock_task.errors)
        self.assertTrue(1 in self.mock_task.errors['Exception'].values()[0])

    def test_continue(self):
        self.mock_task = self.MockTask(commandline=False, quiet=True, continue_task=True)
        first_run = self.mock_task.get_items_len() / 2
        self.mock_task.processed = first_run

        self.mock_task.run()

        self.assertTrue(self.mock_task.is_finished())
        self.assertEqual(self.mock_task.process_item.call_count, self.mock_task.get_items_len() - first_run)

    def test_load_task(self):
        self.MockStorage.load = Mock(return_value={
            'processed': 1,
            'items_len': 1,
            'errors': {'Exception': {'tb': [1]}}
        })

        self.mock_task = self.MockTask(commandline=False, quiet=True, continue_task=True)

        self.assertEqual(self.mock_task.processed, 1)
        self.assertEqual(self.mock_task.items_len, 1)
        self.assertEqual(self.mock_task.errors, {'Exception': {'tb': [1]}})

    def test_save_task(self):
        self.mock_task.run()

        self.mock_task.storage.save.assert_called_once_with({
            'processed': self.mock_task.get_items_len(),
            'items_len': self.mock_task.get_items_len(),
            'errors': {}
        })

    def test_rerun_errors(self):
        self.mock_task = self.MockTask(commandline=False, quiet=True, continue_task=True, rerun_errors=True)
        self.mock_task.errored_items = set([0])
        self.mock_task.processed = self.mock_task.get_items_len()

        self.mock_task.run()

        self.mock_task.process_item.assert_called_once_with(0)
