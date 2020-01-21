from PIL import Image, ImageDraw
import io
import time

def get(size, size_all, num_child):
  im = Image.new("RGB",(200,100),"white")
  draw = ImageDraw.Draw(im)
  color = (0, 0, 0, 255)
  draw.text((10,10), 'size     : {:,}'.format(size), fill=color)
  draw.text((10,25), 'size_all : {:,}'.format(size_all), fill=color)
  draw.text((10,40), 'num_child: {:,}'.format(num_child), fill=color)
  with io.BytesIO() as out:
    im.save(out, format="jpeg")
    contents = out.getvalue()
  return contents

def test():
  start = time.time()
  for i in range(1000):
    data = get(100, 1000, 10)
  elapsed_time = time.time() - start
  print ("elapsed_time:{0}".format(elapsed_time) + "[sec]")
  with open('test.jpg', 'wb') as fout:
    fout.write(data)

if __name__ == '__main__':
  test()