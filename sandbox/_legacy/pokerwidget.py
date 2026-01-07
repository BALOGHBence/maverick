import matplotlib as mpl
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QComboBox, QAction
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtCore import pyqtSignal
from poker.screen import Window
from poker.context import PokerContext, \
    PlayerContext as Player, CommunityCardsContext as Cards, PotContext as Pot
from poker.cv import Image
from poker.mpl import FigureCanvas
import pygetwindow as gw
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as \
    NavigationToolbar
from matplotlib import cbook
from matplotlib.figure import Figure
import numpy as np
import os
import time

CursorShape = QtCore.Qt.CursorShape


def mpl_image_folder():
    return str(cbook._get_data_path('images'))


class NavigationToolbar2(NavigationToolbar):
    """
     List of toolitems to add to the toolbar, format is:
     (
       text, # the text of the button (often not visible to users)
       tooltip_text, # the tooltip shown on hover (where possible)
       image_file, # name of the image for the button (without the extension)
       name_of_method, # name of the method in NavigationToolbar2 to call
     )

    Example
    -------
        (1) The default toolbar can be reconstructed with

            class NavigationToolbar2(NavigationToolbar):
                NavigationToolbar2QT.toolitems = (
                    ('Home', 'Reset original view', 'home', 'home'),
                    ('Back', 'Back to previous view', 'back', 'back'),
                    ('Forward', 'Forward to next view', 'forward', 'forward'),
                    (None, None, None, None),
                    ('Pan', 'Pan axes with left mouse, zoom with right',
                    'move', 'pan'),
                    ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
                    ('Subplots', 'Configure subplots', 'subplots',
                    'configure_subplots'),
                    (None, None, None, None),
                    ('Save', 'Save the figure', 'filesave', 'save_figure'),
                )
    """

    def __init__(self, *args, widget = None, **kwargs):
        self.widget = widget
        toolitems = list(self.toolitems)
        toolitems.append(('Save', 'Save the figure', 'rubic',
                          'on_capture'))
        self.toolitems = toolitems
        super().__init__(*args, **kwargs)

    def on_capture(self, *args, **kwargs):
        left, right = self.widget.table.get_xlim()
        bottom, top = self.widget.table.get_ylim()
        region = left, top, right - left, bottom - top
        print(region)


class PokerWidget(QtWidgets.QMainWindow):
    content_changed = pyqtSignal()
    context_changed = pyqtSignal()

    def __init__(self, *args, parent = None, usetex = False,
                 name = 'PokerWidget', context = None, image_folder = None,
                 icons_folder = None, **kwargs):
        super().__init__(parent)
        mpl.rcParams['text.usetex'] = usetex
        mpl.rc('font', **{'family' : "serif", 'size'   : 8})
        self.icons_folder = icons_folder
        self.image_folder = image_folder
        self._create_layout(*args, **kwargs)

        self._window = None
        self.img = None
        self.imgplot = None
        self.table = None
        self._press = None, None
        self.context = context
        self._background = None  # for blitting

        self._connect_events()
        self._init_plot(*args, **kwargs)
        self._init_plot_data(*args, **kwargs)

    def _init_plot(self, *args, **kwargs):
        self.fig.clf()
        self.table = self.fig.add_subplot(111)

    def _init_plot_data(self, *args, img = None, img_path = None,
                        window = None, **kwargs):
        self._window = None
        self.img = None
        self._background = None
        if isinstance(img, np.ndarray):
            self.img = Image(img).asRGB()
        elif isinstance(img, str):
            self.img = Image.from_path(img).asRGB()
        elif isinstance(img_path, str):
            self.img = Image.from_path(img_path).asRGB()

        if self.img is None:
            if window is not None:
                w = window
            else:
                w = Window(*args, **kwargs)
            if getattr(w, '_wrapped_obj', None) is not None:
                w._wrapped_obj = self._resize_window(w._wrapped_obj)
                self._window = w
                self.img = Image.from_window(w).asRGB()
                self.find_context()
        if self.img is not None:
            self.content_changed.emit()
        if self.context is not None:
            self.context_changed.emit()

    def _resize_window(self, w):
        title = w.title
        if 'VLC' in title:
            w.resizeTo(1208, 957)
        return w

    def scrape_window(self, *args, **kwargs):
        if self._window is not None:
            self._resize_window(self._window)
            time.sleep(0.1)
            self.img = Image.from_window(self._window).asRGB()
            self._background = None
            self.content_changed.emit()
            [c.decode() for c in self.context.iterfiles()]

    def _on_change_window(self):
        try:
            try:
                self.imgplot.remove()
            finally:
                self.imgplot = None
            self._init_plot_data(title = self.windowscb.currentText())
            self.content_changed.emit()
        except Exception as e:
            print('_on_change_window')
            print(e)

    def _on_content_changed(self):
        if self.img is not None:
            if self.imgplot is None:
                self.draw_image()
                x1, y1, w, h = self.context.region()
                self.table.set_xlim([x1, x1 + w])
                self.table.set_ylim([y1 + h, y1])
                self.context.plot_artist(self.table, deep = True)
            else:
                self.imgplot.set_data(self.img)
            self.canvas.draw_idle()
            self._store_background()
            self.canvas.flush_events()

    def _store_background(self):
        self._background = self.canvas.copy_from_bbox(self.fig.bbox)

    def _restore_background(self):
        self.canvas.restore_region(self._background)

    def _on_context_changed(self):
        self._restore_background()
        self.context.draw_artist(self.table, deep = True)
        self.canvas.blit(self.fig.bbox)
        #self.canvas.flush_events()

    def draw_image(self, *args, **kwargs):
        if self.img is not None:
            self.imgplot = self.table.imshow(self.img)
            self.table.set_xticks([])
            self.table.set_yticks([])

    def _get_icon(self, *args, **kwargs):
        return QIcon(self._get_icon_path(*args, noext = False, **kwargs))

    def _get_icon_path(self, label : str, ext = '.png', noext = False):
        if noext:
            return os.path.join(self.icons_folder, label)
        else:
            return os.path.join(self.icons_folder, label + ext)

    def _get_image(self, *args, **kwargs):
        path = self._get_image_path(*args, noext = False, **kwargs)
        return Image.from_path(path)

    def _get_image_path(self, label : str, ext = '.png', noext = False):
        if noext:
            return os.path.join(self.image_folder, label)
        else:
            return os.path.join(self.image_folder, label + ext)

    def _connect_events(self):
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('draw_event', self._on_draw)
        self.canvas.artist_changed.connect(self._on_artist_changed)
        self.toolbar._actions['zoom'].toggled.connect(self._on_zoom_toggled)
        self.content_changed.connect(self._on_content_changed)
        self.context_changed.connect(self._on_context_changed)
        self.windowscb.currentIndexChanged.connect(self._on_change_window)

    def _on_artist_changed(self):
        self.context_changed.emit()

    def _on_draw(self, *args, **kwargs):
        self._store_background()
        if self.context is not None:
            self.context.draw_artist(self.table, deep = True)

    def _create_layout(self, *args, width = 5, height = 4, dpi = 100,
                       edgecolor = 'black', facecolor = None,
                       tight_layout = True, **kwargs):
        self.frame = QtWidgets.QFrame()

        # set matplotlib related stuff
        if facecolor is None:
            _bcgclr = self.palette().color(QPalette.Background)
            facecolor = [_bcgclr.red()/255, _bcgclr.green()/255,
                         _bcgclr.blue()/255]
            facecolor = [_bcgclr.red()/255, _bcgclr.green()/255,
                         _bcgclr.blue()/255]
        self.fig = Figure(figsize=(width, height), dpi=dpi,
                          edgecolor = 'black', facecolor = facecolor,
                          constrained_layout = tight_layout)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setFocus()
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.toolbar = NavigationToolbar2(self.canvas, self.frame,
                                          widget = self)

        # layout
        self.layout = QtWidgets.QVBoxLayout()
        self.windowscb = QComboBox()
        [self.windowscb.addItem(i) for i in gw.getAllTitles() if len(i) > 0]
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.windowscb)
        self.layout.addWidget(self.canvas)
        self.canvas.setParent(self.frame)
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        # extend matplotlib toolbar
        save = self.toolbar.actions()[10]
        icon = self._get_icon('selectrect')
        newrect = QAction(icon, 'Select rectangle', self)
        self.toolbar.insertAction(save, newrect)

        icon = self._get_icon('capture')
        capture = QAction(icon, 'Capture', self)
        self.toolbar.insertAction(newrect, capture)

        newplayer = QAction(self._get_icon('adduser'), 'New player', self)
        self.toolbar.insertAction(capture, newplayer)
        newplayer.triggered.connect(self._on_capture_player)

        dealer = QAction(self._get_icon('dealer'), 'Dealer', self)
        self.toolbar.insertAction(newplayer, dealer)
        #dealer.triggered.connect(self.scrape_window)

        cards = QAction(self._get_icon('pokercards'), 'Cards', self)
        self.toolbar.insertAction(newplayer, cards)
        cards.triggered.connect(self._on_capture_cards)

        pot = QAction(self._get_icon('pokerchips'), 'Pot', self)
        self.toolbar.insertAction(newplayer, pot)
        pot.triggered.connect(self._on_capture_pot)

        remove = QAction(self._get_icon('remove'), 'Remove', self)
        self.toolbar.insertAction(newrect, remove)
        remove.triggered.connect(self.delete_selected_context)
        self.btnremove = remove

        refresh = QAction(self._get_icon('refresh'), 'Refresh content', self)
        self.toolbar.insertAction(remove, refresh)
        refresh.triggered.connect(self.scrape_window)
        self.btnrefresh = refresh
        #remove.setCheckable(True)

        self.toolbar.insertSeparator(newplayer)
        self.toolbar.insertSeparator(remove)
        self.toolbar.insertSeparator(dealer)
        self.toolbar.insertSeparator(dealer)

    def find_context(self, *args, **kwargs):
        if isinstance(self.context, str):
            if os.path.isfile(self.context):
                _, ext = os. path.splitext(self.context)
                if ext.lower() == '.json':
                    self.context = PokerContext.load(self.context)
                    self.context._widget = self
        elif isinstance(self.context, PokerContext):
            self.context._widget = self
        elif self._window is not None:
            self.find_context_from_window(*args, **kwargs)

    def find_context_from_window(self, *args, **kwargs):
        def _get_bounds(img_path):
            r = self._window.find_image(img_path = img_path,
                                        confidence = 0.9,
                                        relative = True)
            return (r[0], r[0] + r[2]), (r[1], r[1] + r[3])

        try:
            markers = [
                "E:\\pokerwindow_header_left.png",
                "E:\\pokerwindow_header_right.png",
                "E:\\pokerwindow_footer_left.png"
            ]
            bounds = np.stack([_get_bounds(m) for m in markers])
            x1 = bounds[:, 0].min()
            y1 = bounds[:, 1].min()
            w = bounds[:, 0].max() - x1
            h = bounds[:, 1].max() - y1
            region = x1, y1, w, h
            self.context = PokerContext(widget = self, region = region,
                                        key = 'bet365')
        except Exception:
            self.context = None

    def _on_capture_player(self, *args, **kwargs):
        self._store_background()
        left, right = list(map(int, self.table.get_xlim()))
        bottom, top = list(map(int, self.table.get_ylim()))
        w, h = right - left, bottom - top
        region = [left, top, w, h]
        nP = len(self.context.players())
        key = 'player' + str(nP)
        p = Player(parent = self.context, region = region, relative = False)
        self.context.new_file(p, key = key)
        p.plot_artist(self.table, deep = True)
        self.context_changed.emit()

    def _on_capture_cards(self, *args, **kwargs):
        self._store_background()
        left, right = list(map(int, self.table.get_xlim()))
        bottom, top = list(map(int, self.table.get_ylim()))
        w, h = right - left, bottom - top
        region = [left, top, w, h]
        c = Cards(parent = self.context, region = region, relative = False)
        self.context.new_file(c, key = 'cards')
        c.plot_artist(self.table)
        self.context_changed.emit()

    def _on_capture_pot(self, *args, **kwargs):
        self._store_background()
        left, right = list(map(int, self.table.get_xlim()))
        bottom, top = list(map(int, self.table.get_ylim()))
        w, h = right - left, bottom - top
        region = [left, top, w, h]
        c = Pot(parent = self.context, region = region, relative = False)
        self.context.new_file(c, key = 'pot')
        c.plot_artist(self.table)
        self.context_changed.emit()

    def _on_zoom_toggled(self, toggled):
        return

    def _on_press(self, event):
        if not self.in_mpl_action():
            self.canvas.button_press_signal.emit(event)

    def delete_selected_context(self):
        cfiles = self.context.iterfiles(inclusive = True)
        selrects = list(filter(lambda c : c.rect.selected, cfiles))
        if len(selrects) > 0:
            selected = selrects[0]
            if not selected.is_root():
                selected.rect.release()
                selected.remove_artist()
                p = selected.parent
                k = selected.key
                del p[k]
                self.canvas.artist_changed.emit()

    def _on_release(self, event):
        if not self.in_mpl_action():
            self.canvas.button_release_signal.emit(event)
        cfiles = list(self.context.iterfiles(inclusive = True))
        selrects = list(filter(lambda c : c.rect.selected, cfiles))
        enabled = False
        if len(selrects) == 1:
            if not selrects[0].is_root():
                enabled = True
        self.btnremove.setEnabled(enabled)

    def _on_motion(self, event, *args, **kwargs):
        if not self.in_mpl_action():
            self.canvas.motion_notify_signal.emit(event)

    def in_mpl_action(self):
        return self.toolbar.mode.name.lower() != 'none'

    def closeEvent(self, event):
        event.accept()
        #event.ignore()


if __name__ == '__main__':
    #import cv2

    image_folder_path = "E:\\b365\\"
    icons_folder_path = "F:\\Google Drive\\icons\\"
    fnc = lambda t : 'VLC' in t
    context_path = "E:\\test_context_dump.json"
    context_path = None
    w = PokerWidget(fltr = fnc, context = context_path,
                    image_folder = image_folder_path,
                    icons_folder = icons_folder_path)
    w.show()

    # [p.decode('pokerstate_active_hands') for p in w.context.players()]
    # [p.decode('poker_card_back') for p in w.context.players()]
    # [p.decode('poker_dealer_btn') for p in w.context.players()]
    # [p.decode('pokerstate_fold') for p in w.context.players()]
    # [p.decode('pokerstate_sitout') for p in w.context.players()]
    # [p.decode('pokerstate_check') for p in w.context.players()]
    # [p.decode('pokerstate_check2') for p in w.context.players()]
    # [p.decode('pokerstate_call') for p in w.context.players()]
    # [p.decode('pokerstate_value_empty') for p in w.context.players()]
    # [p.decode('pokerstate_bigblind') for p in w.context.players()]
    # [p.decode('pokerstate_smallblind') for p in w.context.players()]
    # [p.decode('pokerstate_ante') for p in w.context.players()]

    config = r'-l eng --oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
