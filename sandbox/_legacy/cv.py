import numpy as np
import cv2
from pyautogui import screenshot
from enum import Enum, unique, auto
from matplotlib import pyplot as plt
from poker.mpl import Rectangle
from poker.screen import Window
from poker.ocr import image_to_string
from copy import deepcopy
import os

suits = ['C', 'D', 'H', 'S']
figures = ['2', '3', '4', '5', '6', '7', '8', '9',
           '10', 'J', 'Q', 'K', 'A']


@unique
class ColorSpace(Enum):
    BGR = auto()
    RGB = auto()
    GRAY = auto()


class Image(np.ndarray):

    def __new__(cls, input_array, colorspace = ColorSpace.RGB, **kwargs):
        obj = np.asarray(input_array).view(cls)
        obj.colorspace = colorspace
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.colorspace = getattr(obj, 'colorspace', None)

    @staticmethod
    def from_screen(region = None):
        if region is not None:
            Screen = Image.from_screen()
            left, top, w, h = region
            img = Screen[top : top + h, left : left + w]
            return img
        else:
            img = np.array(screenshot().convert('RGB'))
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return Image(img, colorspace = ColorSpace.BGR)

    @staticmethod
    def from_window(window : Window = None):
        img = cv2.cvtColor(np.array(window.image()), cv2.COLOR_RGB2BGR)
        return Image(img, colorspace = ColorSpace.BGR)

    @staticmethod
    def from_path(img_path : str = None):
        if os.path.isfile(img_path):
            return Image(cv2.imread(img_path), colorspace = ColorSpace.BGR)
        else:
            return None

    def region(self, region = None, *args, **kwargs):
        """
        If 'region' is provided as an iterable in the form of
        (left, top, width, height), than the result equals to
        self[top : top + h, left : left + w]. If 'region' is not specified
        returns the region of the Image with respect to it's base image.
        """
        if region is not None:
            left, top, w, h = region
            return self[top : top + h, left : left + w]
        h, w = self.shape[:2]
        base = self.base
        if base is None:
            return 0, 0, w, h
        if isinstance(base, Image):
            top_left, _ = base.find(self, **kwargs)
        elif isinstance(base, np.ndarray):
            img = cv2.cvtColor(base, cv2.COLOR_RGB2BGR)
            cs = ColorSpace.BGR
            top_left, _ = Image(img, colorspace = cs).find(self, **kwargs)
        left, top = top_left
        return left, top, w, h

    def rect(self, ec = 'r', fc = 'none', lw = 1.0, **kwargs):
        x0, y0, w, h = self.region()
        rect_kwargs = {'facecolor' : fc, 'edgecolor' : ec, 'linewidth' : lw}
        rect_kwargs.update(kwargs)
        rect = Rectangle((x0, y0), h, w, **rect_kwargs)
        return rect

    def find(self, img, *args, threshold = 0.95, **kwargs):
        (top_left, bottom_right), confidence = \
            self.find_closest(img, *args, return_confidence = True, **kwargs)
        if confidence >= threshold:
            return top_left, bottom_right
        else:
            return None, None

    def find_closest(self, img, return_confidence = False, method = None,
                     **kwargs):
        if method is not None:
            return cv_matchTemplate(self, img, method = method,
                                    return_confidence = return_confidence,
                                    **kwargs)
        res = cv2.matchTemplate(self, img, cv2.TM_CCOEFF_NORMED)
        confidence = res.max()
        rows, cols = np.where(res >= confidence)
        h, w = self.shape[:2]
        top_left = cols[0], rows[0]
        bottom_right = (top_left[0] + w, top_left[1] + h)
        if return_confidence:
            return (top_left, bottom_right), confidence
        else:
            return top_left, bottom_right

    def show(self, *args, **kwargs):
        fig, ax = plt.subplots()
        ax.imshow(self, *args, **kwargs)
        return fig, ax

    def asGray(self):
        if self.colorspace == ColorSpace.GRAY:
            return self
        elif self.colorspace == ColorSpace.RGB:
            cvt = cv2.COLOR_RGB2GRAY
        elif self.colorspace == ColorSpace.BGR:
            cvt = cv2.COLOR_BGR2GRAY
        img = cv2.cvtColor(self, cvt)
        return Image(img, colorspace = ColorSpace.GRAY)

    def asRGB(self):
        if self.colorspace == ColorSpace.GRAY:
            return None
        elif self.colorspace == ColorSpace.RGB:
            return self
        elif self.colorspace == ColorSpace.BGR:
            img = deepcopy(self)
            img[:, :] = cv2.cvtColor(self, cv2.COLOR_BGR2RGB)
            img.colorspace = ColorSpace.RGB
            return img

    def to_string(self, *args, config = None, **kwargs):
        return image_to_string(self, *args, config = config, **kwargs)


def cv_matchTemplate(img_big, img_small, method = cv2.TM_CCOEFF_NORMED,
                     return_confidence = False, **kwargs):
    h, w = img_big.shape[:2]
    res = cv2.matchTemplate(img_big, img_small, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc

    confidence = None
    if method == cv2.TM_CCOEFF_NORMED:
        confidence = res.max()
    elif method == cv2.TM_SQDIFF_NORMED:
        confidence = 1-res.min()
    elif method == cv2.TM_CCORR_NORMED:
        confidence = res.max()

    bottom_right = (top_left[0] + w, top_left[1] + h)
    if return_confidence:
        return (top_left, bottom_right), confidence
    else:
        return top_left, bottom_right


def split_image_to_cards(img, whitelimit = 180):
    """
    Returns a list of numpy arrays representing the cards in the image.
    """
    # grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    white = whitelimit  # everything above this is white

    # clip colors
    gray[gray < white] = 0
    gray[gray >= white] = 255

    # crop
    cond = ~np.all(gray == 255, axis=1)
    gray = gray[cond]
    img = img[cond]
    cond = ~np.all(gray == 255, axis=0)
    gray = gray[:, cond]
    img = img[:, cond]
    cond = ~np.all(gray == 0, axis=1)
    gray = gray[cond]
    img = img[cond]

    # detect cards
    x_sum = np.sum(gray, axis = 0)
    x_tol = x_sum.max() / 10
    h = int(gray.shape[0] / 4)
    f = (x_sum > x_tol).astype(int) * h
    idx = np.where(f == f.max())[0]

    # get bounds of each card
    c_ = 0
    cards = []
    for i in range(len(idx)-1):
        if idx[i+1] > idx[i] + 1:
            cards.append(idx[c_ : i + 1])
            c_ = i + 1
    cards.append(idx[c_:])
    cardbounds = [(c.min(), c.max()) for c in cards]

    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    card = lambda i : img[:, cardbounds[i][0] : cardbounds[i][1] + 1]
    return [card(i) for i in range(len(cardbounds))]


def figs_of_cards(*cards, simple = True, **kwargs):
    """
    Returns a list of numpy arrays representing the figures of the cards.
    """
    return [c[4:26, 1:16] for c in cards]


def suits_of_cards(*images, **kwargs):
    """
    Returns a list of numpy arrays representing the suits of the cards.
    """
    return [c[19:38, :17] for c in images]


def suits_by_color(*cards, **kwargs):
    """
    Determines suits by the dominant color of image arrays.
        green : clubs
        black : spades
        red   : hearts
        blue  : diamonds
    """
    suits = []
    for img in cards:
        rmean = np.mean(img[:, :, 0])
        gmean = np.mean(img[:, :, 1])
        bmean = np.mean(img[:, :, 2])
        cmin = np.min([rmean, gmean, bmean])
        cmax = np.max([rmean, gmean, bmean])
        if cmax - cmin < 10:
            suits.append('S')
        else:
            if cmax == rmean:
                suits.append('H')
            elif cmax == bmean:
                suits.append('D')
            if cmax == gmean:
                suits.append('C')
    return suits


if __name__ == '__main__':
    from pyoneer.Qt.scripting.poker.ocr import images_to_strings
    from pyoneer.Qt.scripting.poker.screen import window_to_image, \
        find_window_with_title, find_image_on_screen

    fnc = lambda t : 'VLC' in t
    w, img = window_to_image(fltr = fnc, return_window = True)
    plt.matshow(img)

    # find dealer button
    img_path = "E:\\poker_dealer_btn.png"
    w = find_window_with_title(fltr = fnc)
    box, btn = find_image_on_screen(window = w, confidence = 0.5,
                                    return_image = True, relative = True,
                                    img_path = img_path)
    plt.matshow(btn)

    # -----------------------------------------
    img_path = "E:\\pokerwindow_header_right.png"
    region, btn = find_image_on_screen(window = w, img_path = img_path,
                                       confidence = 0.9, return_image =True,
                                       relative = True)
    plt.matshow(btn)

    img_path = "E:\\pokerwindow_footer_left.png"
    region, btn = find_image_on_screen(window = w, img_path = img_path,
                                       confidence = 0.9, return_image =True,
                                       relative = True)
    plt.matshow(btn)

    img_path = "E:\\pokerwindow_header_left.png"
    region, btn = find_image_on_screen(window = w, img_path = img_path,
                                       confidence = 0.9, return_image =True,
                                       relative = True)
    plt.matshow(btn)

    # ----------------------------------------
    img_path = "E:\\pokercards4.png"
    img = cv2.imread(img_path)
    cards = split_image_to_cards(img)
    [plt.matshow(c) for c in cards]

    figs = figs_of_cards(*cards)
    [plt.matshow(c) for c in figs]
    strings = images_to_strings(*figs)
    suits = suits_by_color(*figs)

    #
    img_path = "E:\\pokerstate_fold.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.8
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img)
    print(text)

    #
    img_path = "E:\\pokerstate_sitout.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.8
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img)
    print(text)

    #
    img_path = "E:\\pokerstate_check.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.8
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img)
    print(text)

    #
    img_path = "E:\\pokerstate_bigblind.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.8
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img)
    print(text)

    #
    img_path = "E:\\pokerstate_smallblind.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.8
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img)
    print(text)

    #
    img_path = "E:\\pokerstate_win.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.7
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img)
    print(text)

    #
    img_path = "E:\\pokerstate_value_passive.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.65
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img, config='--psm 8')
    print(text)

    #
    img_path = "E:\\pokerstate_value_active.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.7
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img, config='--psm 8')
    print(text)

    #
    img_path = "E:\\pokerstate_value_active_timed.png"
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    cond = img < img.max()*0.7
    img[cond] = 0
    img[~cond] = 255
    text = image_to_string(img, config='--psm 8')
    print(text)

    #
    img_path = "E:\\pokerstate_time_num.png"
    img = cv2.imread(img_path)
    text = image_to_string(img, config='--psm 6')
    print(text)

    #
    img_path = "E:\\pokerstate_win.png"
    img = cv2.imread(img_path)
    text = image_to_string(img, config='--psm 6')
    print(text)

    #
    img_path = "E:\\pokerstate_bigblind.png"
    img = cv2.imread(img_path)
    text = image_to_string(img, config='--psm 6')
    print(text)

    img_path = "E:\\pokerstate_value_passive.png"
    img = cv2.imread(img_path)
    text = image_to_string(img, config='--psm 6')
    print(text)

    img_path = "E:\\pokerstate_value_active.png"
    img = cv2.imread(img_path)
    text = image_to_string(img, config='--psm 6')
    value = float(text.replace(',','.'))
    print(value)

    plt.close('all')
    img = Image.from_screen()
    img1 = img[50:800, 40:250]
    r = img1.rect(draggable = True)
    fig, ax = img.show()
    ax.add_patch(r)
    #r.connect()
    fig1, ax1 = img1.show()

    img1 = Image.from_screen(region = [40, 50, 210, 750]).asRGB()
    r = img1.rect(draggable = True)
    fig, ax = img.show()
    ax.add_patch(r)
    #r.connect()
    fig1, ax1 = img1.show()

    screen = Image.from_screen().asRGB()
    fig1, ax1 = screen.show()
