from pyoneer.core import Hierarchy
from poker.mpl import Rectangle
from poker.screen import find_image_on_screen, \
    region_loc_to_glob, Window
from poker.enums import SelectionState
from poker.cv import Image
from poker.ocr import image_to_string
import json
from matplotlib.colors import to_rgba
from copy import copy


class Context(Hierarchy):
    _typestr_ = 'Context'

    def __init__(self, *args, widget = None, draggable = False, region = None,
                 lw = 1.5, ec = 'r', fc = 'none', relative = False,
                 alpha = 0.5, **kwargs):
        
        super().__init__(*args, dtype = Context, **kwargs)
        
        self._widget = widget
        self.draggable = draggable
        self.rect_params = {
            'lw' : lw,
            'ec' : ec,
            'fc' : fc,
            'alpha' : alpha
        }
        self.rect = None
        self.relative = relative
        
        if region is not None:
            if isinstance(region, tuple):
                region = list(region)
            if all(list(map(lambda x : x <= 1.00001, region))):
                left, top, w, h = region
                left_p, top_p, w_p, h_p = self.parent.region()
                left = left_p + int(left * w_p)
                top = top_p + int(top * h_p)
                w = int(w * w_p)
                h = int(h * h_p)
                region = [left, top, w, h]
                self.relative = False
                
        self._region = region
        self._content = None

    def remove_artist(self):
        # this ugly but efficient line removes this rectangle
        # (including children) from the canvas
        list(map(lambda r : r.remove(),
                 map(lambda c : c.rect,
                     self.iterfiles(inclusive = True))))

    def plot_artist(self, ax = None, *args, deep = False, **kwargs):
        if ax is None:
            return
        try:
            left, top, w, h = self.region()
            _args = ((left, top), w, h)
            _kwargs = copy(self.rect_params)
            _kwargs['ec'] = to_rgba(_kwargs['ec'],
                                    alpha = _kwargs.pop('alpha'))
            self.rect = Rectangle(*_args, context = self, **_kwargs)
            self.rect.plot(ax)
            self.rect.connect()
        except Exception as e:
            print(e)
        if deep:
            [c.plot_artist(ax) for c in self.iterfiles()]

    def draw_artist(self, ax = None, *args, deep = False, **kwargs):
        if ax is None:
            return
        try:
            ax.draw_artist(self.rect)
            if hasattr(self.rect, '_nodes'):
                [ax.draw_artist(n) for n in self.rect._nodes]
        except Exception as e:
            print(e)
        if deep:
            [c.draw_artist(ax) for c in self.iterfiles()]

    def decode(self, *args, **kwargs) -> str:
        ...

    def widget(self):
        return self.root()._widget

    def image(self, *args, from_screen = False, **kwargs) -> Image:
        left, top, width, height = self.region()
        if from_screen:
            w = self.window()
            if w is None:
                return None
            img = Image.from_window(w).asRGB()
        else:
            img = self.widget().img
        return img[top : top + height, left : left + width]

    def region(self, *args, **kwargs) -> tuple:
        if self.is_root():
            if self._region is None:
                w, h = self._widget.img.shape[:2]
                return [0, 0, w, h]
            else:
                return self._region
        else:
            r = self._region
            if self.relative:
                rp = self.parent.region()
                r = region_loc_to_glob(r, region = rp)
            return r

    def screenregion(self):
        w = self.widget()
        if w._window is None:
            return None, None, None, None
        left0, top0, *_ = w._window.region()
        left, top, w, h = self.region()
        return [left0 + left, top0 + top, w, h]

    def window(self) -> Window:
        return self.widget()._window

    def to_dict(self):
        res = {}
        cls = type(self)
        res = {
                'typestr' : cls._typestr_,
                'key' : self.key,
                'region' : [str(x) for x in self._region],
                'relative' : self.relative,
                'draggable' : self.draggable,
                'rect_params' : {k : str(v) for k, v in
                                 self.rect_params.items()},
                }
        for key, value in self.items():
            if isinstance(value, Context):
                res[key] = value.to_dict()
            else:
                res[key] = value
        return res

    def dump(self, path, *args, mode = 'w', indent = 4, normalize = False,
             **kwargs):
        with open(path, mode) as f:
            json.dump(self.to_dict(), f, indent = indent)

    @staticmethod
    def string_to_type(string : str):
        if string == 'PokerContext':
            return PokerContext
        elif string == 'PlayerContext':
            return PlayerContext
        elif string == 'PlayerCardsContext':
            return PlayerCardsContext
        elif string == 'CommonTextContext':
            return CommonTextContext
        elif string == 'PlayerScoreContext':
            return PlayerScoreContext
        elif string == 'Context':
            return Context
        else:
            raise NotImplementedError

    @classmethod
    def from_dict(cls, d : dict = None, **kwargs):
        _kwargs = {
                'key' : d.pop('key'),
                'region' : [int(x) for x in d.pop('region')],
                'relative' : d.pop('relative'),
                'draggable' : d.pop('draggable'),
                }
        rect_params = d.pop('rect_params')
        rect_params['lw'] = float(rect_params['lw'])
        rect_params['alpha'] = float(rect_params.get('alpha', 0.5))
        _kwargs.update(rect_params)
        _kwargs.update(kwargs)
        cls_ = cls.string_to_type(d.pop('typestr'))
        res = cls_(**_kwargs)
        for key, value in d.items():
            if isinstance(value, dict):
                if 'typestr' in value:
                    f = cls.from_dict(value, **kwargs)
                    res.new_file(f, key = key)
                else:
                    res[key] = value
            else:
                res[key] = value
        return res

    @classmethod
    def load(cls, jsonpath : str = None, **kwargs):
        if jsonpath is not None:
            with open(jsonpath,'r') as f:
                d = json.load(f)
            return cls.from_dict(d, **kwargs)


class PokerContext(Context):
    _typestr_ = 'PokerContext'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.new_file(CommunityCardsContext(), key = 'cards')
        #self.new_file(DealerContext(), key = 'dealer')

    def iterplayers(self, *args, **kwargs):
        return self.iterdata(*args, dtype = PlayerContext, **kwargs)

    def players(self, ind = None, *args, **kwargs):
        if ind is None:
            return list(self.iterplayers(*args, **kwargs))
        elif isinstance(ind, int):
            return list(self.iterplayers(*args, **kwargs))[ind]


class PlayerContext(Context):
    _typestr_ = 'PlayerContext'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        region = [0.1, 0.1, 0.8, 0.3]
        self.new_file(PlayerCardsContext(parent = self, region = region,
                                         ec = 'lime', lw = 1.0),
                      key = 'cards')
        region = [0.1, 0.3, 0.8, 0.2]
        self.new_file(CommonTextContext(parent = self, region = region,
                                        ec = 'pink', lw = 1.0),
                      key = 'status')
        region = [0.1, 0.7, 0.8, 0.2]
        self.new_file(PlayerScoreContext(parent = self, region = region,
                                         ec = 'magenta', lw = 1.0),
                      key = 'score')

    def decode(self, label : str = None, from_screen = False, **kwargs):
        try:
            if label is None:
                label = 'pokerstate_active_hands'
            img = self.widget()._get_image(label).asRGB()
            (top_left, bottom_right), confidence = \
                self.image(from_screen = from_screen). \
                find_closest(img, return_confidence = True)
        except Exception as e:
            print(e)


class PlayerScoreContext(Context):
    _typestr_ = 'PlayerScoreContext'
    _ocr_config_ = r'-l eng --oem 3 --psm 8 -c ' \
        'tessedit_char_whitelist=0123456789'

    def decode(self, from_screen = False, threshold = 0.7, **kwargs):
        config = kwargs.get('config', self._ocr_config_)
        try:
            img = self.image(from_screen = from_screen).asGray()
            cond = img < img.max() * threshold
            img[cond] = 0
            img[~cond] = 255
            s = image_to_string(img, config = config)
            if "," in s:
                pot = int(1000 * float(s.replace(",", ".")))
            else:
                pot = int(float(s.replace(",", ".")))
            self._content = pot
            return pot
        except Exception as e:
            print(e)
            self._content = None


class CommonTextContext(Context):
    _typestr_ = 'CommonTextContext'
    _ocr_config_ = r'-l eng --oem 3 --psm 6'

    def decode(self, from_screen = False, **kwargs):
        config = kwargs.get('config', self._ocr_config_)
        try:
            s = self.image(from_screen = from_screen). \
                to_string(config = config)
            self._content = s
            return s
        except Exception as e:
            print(e)
            self._content = None


class CommunityCardsContext(Context):
    _typestr_ = 'CommunityCardsContext'
    ...


class PlayerCardsContext(Context):
    _typestr_ = 'PlayerCardsContext'
    ...


class CardContext(Context):
    _typestr_ = 'PlayerCardsContext'
    _ocr_config_ = r'-l eng --oem 3 --psm 10'

    def decode(self, from_screen = False, **kwargs):
        config = kwargs.get('config', self._ocr_config_)
        try:
            s = self.image(from_screen = from_screen). \
                to_string(config = config).upper()
            self._content = s
            return s
        except Exception as e:
            print(e)
            self._content = None


class PlayerDealerContext(Context):
    _typestr_ = 'DealerContext'

    def __init__(self, *args, confidence = 0.5, img_path = None, **kwargs):
        #assert img_path is not None
        super().__init__(*args, **kwargs)
        self.confidence = confidence
        self.img_path = img_path

    def decode(self):
        return
        r = self.region()
        c = self.confidence
        try:
            box = find_image_on_screen(region = r, confidence = c,
                                       relative = False, path = self.img_path)
            left, top, width, height = box
            rect_args = ((left-8, top-8), width + 16, height + 16)
            ec = SelectionState.SelectDealer.color()
            rect_kwargs = {'linewidth' : 1.5,
                           'edgecolor' : ec,
                           'facecolor' : 'none'}
            self.rect = Rectangle(*rect_args, draggable = False, **rect_kwargs)
        except Exception:
            self.rect = None


class ActionButtonsContext(Context):
    _typestr_ = 'ActionButtonsContext'
    ...


class TournamentInfoContext(Context):
    _typestr_ = 'TournamentInfoContext'
    ...


class PotContext(Context):
    _typestr_ = 'PotContext'
    _ocr_config_ = r'-l eng --oem 3 --psm 8 -c ' \
        'tessedit_char_whitelist=0123456789'

    def decode(self, from_screen = False, **kwargs):
        config = kwargs.get('config', self._ocr_config_)
        try:
            s = self.image(from_screen = from_screen). \
                to_string(config = config).lower()
            if "," in s:
                pot = int(1000 * float(s.replace(",", ".")))
            else:
                pot = int(float(s.replace(",", ".")))
            self._content = pot
            return pot
        except Exception as e:
            print(e)
            self._content = None


if __name__ == '__main__':

    P = Context(key = 'b365')
    P.new_file(Context(), key = 'P1')
    P1 = P['P1']
    P1.new_file(Context(), key = 'C1')
    C1 = P1['C1']

    json_path = "E:\\test_context_dump.json"
    P.dump(json_path)

    PC = Context.load(json_path)
