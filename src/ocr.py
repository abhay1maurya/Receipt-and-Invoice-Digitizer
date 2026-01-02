from PIL import Image
import pytesseract

img = Image.open("data/raw/2.jpeg")

text = pytesseract.image_to_string(
    img,
    lang="eng",
    config="--oem 1 --psm 6"
)

print(text)
