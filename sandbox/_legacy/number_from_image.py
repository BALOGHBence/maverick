import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.stats import mstats
import scipy
from matplotlib import gridspec
from PIL import Image
import pytesseract

image = Image.open("E:\\SMOqL.png")
f = image.convert('I')

# grayscale
gray = np.array(f)
gray[gray < 200] = 0
gray[gray >= 200] = 255
gray = gray[~np.all(gray == 255, axis=1)]
gray = gray[:,~np.all(gray == 255, axis=0)]
gray = gray[~np.all(gray == 0, axis=1)]
plt.imshow(gray, cmap='gray')

# detect letters
x_sum = np.sum(gray, axis = 0)
check = ((x_sum)/np.max(x_sum) * 10)
plt.plot((check < 8).astype(int))
plt.show()

plt.matshow(gray)
plt.show()

for idx, i in enumerate((check<8).astype(int)):
    if i < 1:
        gray[:,idx] = 255

plt.matshow(gray)
plt.show()

words =  np.hsplit(gray, np.where(np.all(gray >= 200, axis=0))[0])

gs = gridspec.GridSpec(1,len(words))
fig = plt.figure(figsize=(len(words),1))

i = 0
for word in words:
    word = word[:,~np.all(word >= 230, axis=0)]
    if(word.size):
        ax = fig.add_subplot(gs[i])
        print(word.shape)
        i = i + 1
        ax.matshow(word, aspect = 'auto')
plt.show()

img = Image.open("E:\\pokerpng1.png")
string = pytesseract.image_to_string(img, config='--psm 6').split("\n")
r = [string[i] for i in range(len(string)-1)]
print(r)

img = Image.open("E:\\pokerpng2.png")
string = pytesseract.image_to_string(img, config='--psm 6').split("\n")
r = [string[i] for i in range(len(string)-1)]
print(r)

img = Image.open("E:\\pokerpng3.png")
string = pytesseract.image_to_string(img, config='--psm 6').split("\n")
r = [string[i] for i in range(len(string)-1)]
print(r)

img = Image.open("E:\\pokerpng4.png")
string = pytesseract.image_to_string(img, config='--psm 6').split("\n")
r = [string[i] for i in range(len(string)-1)]
print(r)
