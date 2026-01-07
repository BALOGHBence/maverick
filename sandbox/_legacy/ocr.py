import pytesseract


def image_to_string(img, *args, config = None, **kwargs):
    """
    Returns the text on the image using tesseract OCR by Google. The behaviour
    of tessaract can be configured by the 'config' keyword argument.
    """
    if config is not None:
        s = pytesseract.image_to_string(img, config = config)
    else:
        s = pytesseract.image_to_string(img)
    return s.split('\n')[0]


def images_to_strings(*images):
    """
    Uses tesseract OCR to read the figures on the cards.
    Returs a list of strings.
    """
    res = []
    config = r'-l eng --oem 3 --psm 10 -c ' \
        'tessedit_char_whitelist=0123456789JQKA '
    for img in images:
        res.append(image_to_string(img, config = config))
    return res
