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
