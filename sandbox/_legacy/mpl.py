from matplotlib.patches import Rectangle as Rect
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import numpy as np
from PyQt5.QtCore import Qt, Signal
from numba import njit, config
from functools import partial
from collections import defaultdict

config.THREADING_LAYER = 'omp'
__cache = True

CursorShape = Qt.CursorShape


def distance(p1, p2):
    return np.linalg.norm(np.array(p1)-np.array(p2))


@njit(nogil = True, fastmath = True, cache = __cache)
def in_box(xy, p1, p2):
    x, y = xy
    x1, y1 = p1
    x2, y2 = p2
    return (x < x2) & (x > x1) & (y < y2) & (y > y1)


@njit(nogil = True, fastmath = True, cache = __cache)
def contains_offset(xy, left, top, width, height, offset = 5):
    x, y = xy
    x1, y1 = left, top
    x2 = x1 + width
    y2 = y1 + height
    c1 = in_box((x, y), (x1 - offset, y1 - offset), (x2 + offset, y2 + offset))
    return c1


@njit(nogil = True, fastmath = True, cache = __cache)
def around_edge(xy, left, top, width, height, tol = 5):
    x, y = xy
    x1, y1 = left, top
    x2 = x1 + width
    y2 = y1 + height
    c1 = in_box((x, y), (x1 - tol, y1 - tol), (x2 + tol, y2 + tol))
    c2 = in_box((x, y), (x1 + tol, y1 + tol), (x2 - tol, y2 - tol))
    return c1 and not c2


@njit(nogil = True, fastmath = True, cache = __cache)
def around_point(xy, p, tol):
    x, y = xy
    xp, yp = p
    return in_box((x, y), (xp - tol, yp - tol), (xp + tol, yp + tol))


@njit(nogil = True, fastmath = True, cache = __cache)
def around_center(xy, left, top, width, height, tol = 5):
    p = np.array([left + int(width/2), top + int(height/2)])
    return around_point(xy, p, tol)


def tickle_index(xy, left, top, width, height, tol = 5):
    ptop = (left + int(width/2), top)
    pbottom = (left + int(width/2), top + height)
    pleft = (left, top + int(height/2))
    pright = (left + width, top + int(height/2))
    pcent = (left + int(width/2), top + int(height/2))
    points = [ptop, pbottom, pleft, pright, pcent]
    active = map(lambda p : around_point(xy, p, tol), points)
    try:
        ind = np.argwhere(list(active))[0][0]
    except IndexError:
        return -1
    return ind


def _rect_translate(rect, xy):
    x, y = xy
    x0, y0 = rect._press0
    left0, top0, width, height = rect._region0
    dx, dy = x-x0, y-y0
    return [left0 + dx, top0 + dy, width, height]


def _rect_resize_top(rect, xy):
    x, y = xy
    x0, y0 = rect._press0
    left0, top0, width, height = rect._region0
    dy = y-y0
    return [left0, top0 + dy, width, height - dy]


def _rect_resize_bottom(rect, xy):
    x, y = xy
    x0, y0 = rect._press0
    left0, top0, width, height = rect._region0
    dy = y-y0
    return [left0, top0, width, height + dy]


def _rect_resize_left(rect, xy):
    x, y = xy
    x0, y0 = rect._press0
    left0, top0, width, height = rect._region0
    dx = x-x0
    return [left0 + dx, top0, width - dx, height]


def _rect_resize_right(rect, xy):
    x, y = xy
    x0, y0 = rect._press0
    left0, top0, width, height = rect._region0
    dx = x-x0
    return [left0, top0, width + dx, height]


class FigureCanvas(FigureCanvasQTAgg):
    artist_changed = Signal()
    motion_notify_signal = Signal(object)
    button_press_signal = Signal(object)
    button_release_signal = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ArtistLock = None


class Rectangle(Rect):

    def __init__(self, *args, draggable = False, ax = None, animated = True,
                 aura = 5, verbose = False, context = None, **kwargs):
        super().__init__(*args, animated = animated, **kwargs)
        self.draggable = draggable
        self.hovered = False
        self.selected = False
        self.resizing = False
        self.moving = False
        self.plot(ax)
        self._alpha0 = None
        self._press0 = None
        self._region0 = None
        self._cursor_buf = None
        self.aura = aura
        self._verbose = verbose
        self._dragged = False
        self._trfncdict = defaultdict(lambda *_ : None)
        self._trfnc = None
        self._context = context
        self._init_transfer_functions()

    def _init_transfer_functions(self):
        self._trfncdict[0] = partial(_rect_resize_top, self)
        self._trfncdict[1] = partial(_rect_resize_bottom, self)
        self._trfncdict[2] = partial(_rect_resize_left, self)
        self._trfncdict[3] = partial(_rect_resize_right, self)
        self._trfncdict[4] = partial(_rect_translate, self)

    def plot(self, ax = None):
        if ax is not None:
            ax.add_patch(self)
            self._alpha0 = self._alpha
            x0, y0, w, h = self.region()
            x1 = x0 + w
            y1 = y0 + h
            coords = np.vstack([[x0, y0], [x0, y1], [x1, y1],
                                [x1, y0], [x0, y0]]).T
            c = self.get_edgecolor()
            self._nodes = ax.plot(*coords, c = c, animated = self._animated,
                                  marker = ".", markersize = 8, alpha = 1.0)
            self._nodes[0].set_visible(False)

    def acquire(self):
        if self.figure.canvas.ArtistLock is None:
            self.figure.canvas.ArtistLock = self
            return True
        return False

    def release(self):
        if self.figure.canvas.ArtistLock == self:
            self.figure.canvas.ArtistLock = None
            return True
        return False

    def _on_enter(self, event):
        if self._verbose:
            print('entered {}'.format(self))
        needsdraw = False
        if not self.hovered:
            self.acquire()
            self.hovered = True
            self.set(alpha = 1.0)
            needsdraw = True
            self._cursor_buf = int(self.figure.canvas.cursor().shape())
        return needsdraw

    def _on_leave(self, event):
        if self._verbose:
            print('exited {}'.format(self))
        needsdraw = False
        if not self.selected:
            if self.hovered:
                self.hovered = False
                self.set(alpha = self._alpha0)
                self.release()
                needsdraw = True
        else:
            if self._cursor_buf is not None:
                self.figure.canvas.setCursor(CursorShape(self._cursor_buf))
                self._trfnc = None
        return needsdraw

    def _on_move(self, event):
        if self._verbose:
            print('moved {}'.format(self))
        cursor, trfnc = self.get_cursor(event, tol = 5)
        self.figure.canvas.setCursor(CursorShape(cursor))
        self._trfnc = trfnc
        return False

    def _on_drag(self, event):
        needsdraw = False
        if self._trfnc is not None:
            self._dragged = True
            xy = event.xdata, event.ydata
            try:
                self.set_bounds(*self._trfnc(xy))
                needsdraw = True
            except Exception:
                pass
            if needsdraw:
                coords = self.coords(as_path = True)
                self._nodes[0].set_data(coords)
        return needsdraw

    def on_motion(self, event):
        if not event.inaxes == self.axes:
            return
        needsdraw = False
        if event.button is not None:
            if event.button == 1:
                needsdraw = self._on_drag(event)
        else:
            if self.figure.canvas.ArtistLock is None:
                # None of the rectangles are active
                contains = self.contains_around_edge(event)
                if contains:
                    needsdraw = self._on_enter(event)
            elif self.figure.canvas.ArtistLock == self:
                if self.selected:
                    contains_center = self.contains_around_center(event)
                    contains_edge = self.contains_around_edge(event)
                    if contains_center or contains_edge:
                        needsdraw = self._on_move(event)
                    else:
                        needsdraw = self._on_leave(event)
                else:
                    contains = self.contains_around_edge(event)
                    if not contains:
                        needsdraw = self._on_leave(event)
            else:
                return
        if needsdraw:
            self.figure.canvas.artist_changed.emit()

    def _on_select(self):
        if not self.selected:
            if self._verbose:
                print('selected {}'.format(self))
            self.selected = True
            self._nodes[0].set_visible(True)
            self.set(alpha = 1.0)
            return True
        return False

    def _on_deselect(self, event):
        if self.selected:
            if self._verbose:
                print('deselected {}'.format(self))
            self.selected = False
            self.set(alpha = self._alpha0)
            self._nodes[0].set_visible(False)
            if self._cursor_buf is not None:
                self.figure.canvas.setCursor(CursorShape(self._cursor_buf))
            return True
        return False

    def on_press(self, event):
        if not event.inaxes == self.axes:
            return
        if self.hovered or self.selected:
            if event.button == 1:
                self._press0 = event.xdata, event.ydata
                self._region0 = self.region()
        else:
            self._press0 = None

    def _on_drag_release(self):
        left, top, width, height = self.region()
        modified = False
        if height < 0:
            top += height
            height = abs(height)
            modified = True
        if width < 0:
            left += width
            width = abs(width)
            modified = True
        if modified:
            self.set_bounds(left, top, width, height)
        return modified

    def on_release(self, event):
        if not event.inaxes == self.axes:
            return
        needsdraw = False
        if self._press0 is None:
            return

        if not self._dragged:
            if self.hovered and not self.selected:
                needsdraw = self._on_select()
            elif self.selected and not self.hovered:
                needsdraw = self._on_deselect(event)
            elif self.selected and self.hovered:
                d = distance(self._press0, (event.xdata, event.ydata))
                if d < self.aura:
                    needsdraw = self._on_deselect(event)
            else:
                raise NotImplementedError
        else:
            # check negative width or height
            self._on_drag_release()
            if self._context is not None:
                self._context._region = list(map(int, self.region()))

        self._dragged = False
        self._press0 = None
        if needsdraw:
            self.figure.canvas.artist_changed.emit()

    def region(self):
        left, top = self.xy
        return [left, top, self._width, self._height]

    def contains(self, event, *args, offset = 0, **kwargs):
        if offset == 0:
            return super().contains(event, *args, **kwargs)
        else:
            x, y = event.xdata, event.ydata
            left, top, width, height = self.region()
            return contains_offset((x, y), left, top, width, height, offset)

    def contains_around_edge(self, event, tol = None):
        tol = tol if tol is not None else self.aura
        x, y = event.xdata, event.ydata
        left, top, width, height = self.region()
        return around_edge((x, y), left, top, width, height, tol)

    def contains_around_center(self, event, tol = 5):
        x, y = event.xdata, event.ydata
        left, top, width, height = self.region()
        return around_center((x, y), left, top, width, height, tol)

    def coords(self, *args, as_path = False, dtype = np.float32, **kwargs):
        x0, y0, w, h = self.region()
        x1, y1 = x0 + w, y0 + h
        if as_path:
            return np.vstack([[x0, y0], [x1, y0], [x1, y1],
                              [x0, y1], [x0, y0]]).astype(dtype).T
        else:
            return np.vstack([[x0, y0], [x1, y0], [x1, y1],
                              [x0, y1]]).astype(dtype)

    def get_cursor(self, event, tol = 5):
        xy = event.xdata, event.ydata
        left, top, width, height = self.region()
        ind = tickle_index(xy, left, top, width, height, tol)
        if ind == 0:
            # cursor is around the top center point
            cursor = int(Qt.SizeVerCursor)
        elif ind == 1:
            # cursor is around the bottom center point
            cursor = int(Qt.SizeVerCursor)
        elif ind == 2:
            # cursor is around the left center point
            cursor = int(Qt.SizeHorCursor)
        elif ind == 3:
            # cursor is around the right center point
            cursor = int(Qt.SizeHorCursor)
        elif ind == 4:
            # cursor is around the center point
            cursor = int(Qt.OpenHandCursor)
        else:
            cursor = self._cursor_buf
        return cursor, self._trfncdict[ind]

    def connect(self):
        """Connect to all the events we need."""
        c = self.figure.canvas
        c.motion_notify_signal.connect(self.on_motion)
        c.button_press_signal.connect(self.on_press)
        c.button_release_signal.connect(self.on_release)

    def disconnect(self):
        """Disconnect all callbacks."""
        c = self.figure.canvas
        c.motion_notify_signal.disconnect(self.on_motion)
        c.button_press_signal.disconnect(self.on_press)
        c.button_release_signal.disconnect(self.on_release)

    def remove(self):
        self.disconnect()
        self._nodes[0].remove()
        super().remove()
