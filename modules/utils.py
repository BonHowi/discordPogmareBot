from PIL import Image
import requests
from io import BytesIO


# Get dominant color from image
def get_dominant_color(url):
    response = requests.get(url)
    pil_img = Image.open(BytesIO(response.content))
    img = pil_img.copy()
    img.convert("RGB")
    img.resize((1, 1), resample=0)
    dominant_color = img.getpixel((0, 0))
    return int('%02x%02x%02x' % (dominant_color[0], dominant_color[1], dominant_color[2]), 16)
