import pygetwindow as gw
import pyautogui as gui
from pyautogui import locateOnScreen, locateAllOnScreen, screenshot
import time
from typing import Callable
from pyoneer.core.wrap import Wrapper


class Window(Wrapper):

    def __init__(self, *args, get_active = False, sleep = None, **kwargs):
        super().__init__(*args, **kwargs)
        if self._wrapped_obj is None:
            try:
                w = find_window_with_title(*args, **kwargs)
                if w is None and get_active:
                    if sleep is not None:
                        time.sleep(sleep)
                    w = gw.getActiveWindow()
                self._wrapped_obj = w
            except Exception as e:
                print(e)

    def region(self):
        return window_to_region(self)

    def image(self, *args, **kwargs):
        w_ = gw.getActiveWindow()
        self.activate()
        img = screenshot(region = self.region()).convert('RGB')
        w_.activate()
        return img

    @staticmethod
    def get_active():
        return Window(wrap = gw.getActiveWindow())

    def find_image(self, img_path, *args, **kwargs):
        return find_image_on_screen(*args, window = self,
                                    img_path = img_path, **kwargs)


def find_image_on_screen(*args, window = None, confidence = 0.9,
                         return_image = False, relative = True,
                         img_path = None, multiple = False, region = None,
                         **kwargs):
    assert img_path is not None
    activewindow = None
    region = None

    # Check if window or region is provided directly by a window, a region, or
    # both. If both region and window are provided, it is assumed that the
    # coordinates of region are relative to the window, and the necessary
    # transformation is carried out.
    if window is not None and region is not None:
        region = region_loc_to_glob(region, window = window)
    elif window is not None:
        region = window_to_region(window)

    # If region can not be assumed from direct input, try to guess
    # a window from title.
    if region is None:
        window = find_window_with_title(*args, **kwargs)
        if window is not None:
            region = window_to_region(window)

    # Store currently active window and activate the window we need to
    # locate our image on.
    if window is not None:
        activewindow = gw.getActiveWindow()
        window.activate()

    if region is None:
        w, h = gui.size()
        region = [0, 0, w, h]

    if not multiple:
        boxes = [locateOnScreen(img_path, confidence = confidence,
                                region = region),]
    else:
        boxes = locateAllOnScreen(img_path, confidence = confidence,
                                  region = region)

    regions, images = [], []
    for box in boxes:
        r = box_to_region(box)
        if return_image:
            images.append(screenshot(region = r))
        if relative:
            r = region_glob_to_loc(r, region = region)
        regions.append(r)
    if activewindow is not None:
        activewindow.activate()

    if return_image:
        return (regions, images) if multiple else (regions[0], images[0])
    return regions if multiple else regions[0]


def find_window_with_title(*args, title = None, fltr : Callable = None,
                           **kwargs):
    try:
        if isinstance(title, Callable):
            titles = gw.getAllTitles()
            title = list(filter(title, titles))[0]
        elif title is None:
            assert fltr is not None
            titles = gw.getAllTitles()
            title = list(filter(fltr, titles))[0]
        w = gw.getWindowsWithTitle(title)[0]
        return w
    except IndexError:
        return None


def window_to_image(*args, title = None, fltr = None, sleep = None,
                    window = None, return_window = False, **kwargs):

    def w_to_img(w):
        w_ = gw.getActiveWindow()
        r = window_to_region(w)
        w.activate()
        img = screenshot(region = r)
        w_.activate()
        return img

    img = None
    w = None
    if title is None and fltr is None:
        if window is not None:
            w = window
        else:
            if sleep is not None:
                time.sleep(sleep)
            w = gw.getActiveWindow()
    elif title is not None:
        try:
            w = find_window_with_title(title = title)
        except Exception:
            pass
    elif fltr is not None:
        try:
            w = find_window_with_title(fltr = fltr)
        except Exception:
            pass
    if w is not None:
        img = w_to_img(w)
    if return_window:
        return w, img
    return img


def box_to_region(box):
    return list(map(lambda attr : getattr(box, attr),
                    ['left', 'top', 'width', 'height']))


def window_to_region(w):
    return box_to_region(w._rect)


def region_loc_to_glob(r, *args, window = None, region = None, **kwargs):
    if window is not None:
        rw = window_to_region(window)
    if region is not None:
        rw = region
    r[0] = r[0] + rw[0]
    r[1] = r[1] + rw[1]
    return r


def region_glob_to_loc(r, *args, window = None, region = None, **kwargs):
    if window is not None:
        rw = window_to_region(window)
    if region is not None:
        rw = region
    r[0] = r[0] - rw[0]
    r[1] = r[1] - rw[1]
    return r
