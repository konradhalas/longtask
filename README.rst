========
longtask
========

.. image:: https://travis-ci.org/konradhalas/longtask.png
    :target: https://travis-ci.org/konradhalas/longtask

Long task runner with few nice features.

``longtask`` is a simple framework to run long tasks (eg. data migration, data processing) in console environment.
During process execution you can track changes on progress bar. If something goes wrong or you don't have time now - you
can stop task and rerun it later. ``longtask`` collects all your task stats and store it in JSON file.

How to create task?
-------------------

If you want to create task you need to implement derived class from ``longtask.Task``. You also need to override few
things:

- ``name`` - task name,
- ``get_items()`` - this method should return you items collection,
- ``process_item(item)`` - in this method you can process your item.

Simple example - resize many pictures (``resize.py``):

::

    import longtask
    import glob
    from PIL import Image


    class ResizeTask(longtask.Task):
        name = 'resize'

        def get_items(self):
            return glob.glob('*.png')

        def process_item(self, item):
            original_image = Image.open(item)
            resized_image = original_image.resize((100, 100))
            resized_image.save('output/' + item)


    if __name__ == '__main__':
        ResizeTask().run()

Now in directory with ``*.png`` images you can run:

::

    $ python resize.py
    [*] Starting task: resize [2013-03-03 18:36:29.953306]
    [*] Processed: 100% (1000/1000) errors: 10% (100/1000) |###################| Elapsed Time: 1:00:00 ETA:  0:00:00
    [*] Finished task: resize [2013-03-03 18:36:30.080421]
    [*] Stats:
      - processed: 100% (1000/1000)
      - success: 90% (900/1000)
      - errors: 10% (100/1000)
        - 100 x IOError with traceback:

    Traceback (most recent call last):
      File "/Users/konradhalas/dev/workspace/personal/longtask/longtask/task.py", line 59, in run
        self.process_item(item)
      File "resize.py", line 13, in process_item
        original_image = Image.open(item)
      File "/Users/konradhalas/dev/virtualenvs/longtask/lib/python2.7/site-packages/PIL/Image.py", line 1980, in open
        raise IOError("cannot identify image file")
    IOError: cannot identify image file

In our example we resized 1000 files - 100 of them have corrupted data (``IOError``). This task took 1h.

You can always stop task with ``Ctrl+C`` and rerun it later with flag ``-c``. If some errors occured durring execution
you can rerun it with flag ``-e`` (it works only with flag ``-c``).

License
-------

Copyright [2013] [Konrad Hałas]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
