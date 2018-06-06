# encoding: utf-8
# module _curses
# from /usr/local/lib/python3.6/lib-dynload/_curses.cpython-36m-x86_64-linux-gnu.so
# by generator 1.145
# no doc
# no imports

# Variables with simple values

ALL_MOUSE_EVENTS = 134217727

A_ALTCHARSET = 4194304
A_ATTRIBUTES = -256
A_BLINK = 524288
A_BOLD = 2097152
A_CHARTEXT = 255
A_COLOR = 65280
A_DIM = 1048576
A_HORIZONTAL = 33554432
A_INVIS = 8388608
A_LEFT = 67108864
A_LOW = 134217728
A_NORMAL = 0
A_PROTECT = 16777216
A_REVERSE = 262144
A_RIGHT = 268435456
A_STANDOUT = 65536
A_TOP = 536870912
A_UNDERLINE = 131072
A_VERTICAL = 1073741824

BUTTON1_CLICKED = 4

BUTTON1_DOUBLE_CLICKED = 8

BUTTON1_PRESSED = 2
BUTTON1_RELEASED = 1

BUTTON1_TRIPLE_CLICKED = 16

BUTTON2_CLICKED = 256

BUTTON2_DOUBLE_CLICKED = 512

BUTTON2_PRESSED = 128
BUTTON2_RELEASED = 64

BUTTON2_TRIPLE_CLICKED = 1024

BUTTON3_CLICKED = 16384

BUTTON3_DOUBLE_CLICKED = 32768

BUTTON3_PRESSED = 8192
BUTTON3_RELEASED = 4096

BUTTON3_TRIPLE_CLICKED = 65536

BUTTON4_CLICKED = 1048576

BUTTON4_DOUBLE_CLICKED = 2097152

BUTTON4_PRESSED = 524288
BUTTON4_RELEASED = 262144

BUTTON4_TRIPLE_CLICKED = 4194304

BUTTON_ALT = 67108864
BUTTON_CTRL = 16777216
BUTTON_SHIFT = 33554432

COLOR_BLACK = 0
COLOR_BLUE = 4
COLOR_CYAN = 6
COLOR_GREEN = 2
COLOR_MAGENTA = 5
COLOR_RED = 1
COLOR_WHITE = 7
COLOR_YELLOW = 3

ERR = -1

KEY_A1 = 348
KEY_A3 = 349
KEY_B2 = 350
KEY_BACKSPACE = 263
KEY_BEG = 354
KEY_BREAK = 257
KEY_BTAB = 353
KEY_C1 = 351
KEY_C3 = 352
KEY_CANCEL = 355
KEY_CATAB = 342
KEY_CLEAR = 333
KEY_CLOSE = 356
KEY_COMMAND = 357
KEY_COPY = 358
KEY_CREATE = 359
KEY_CTAB = 341
KEY_DC = 330
KEY_DL = 328
KEY_DOWN = 258
KEY_EIC = 332
KEY_END = 360
KEY_ENTER = 343
KEY_EOL = 335
KEY_EOS = 334
KEY_EXIT = 361
KEY_F0 = 264
KEY_F1 = 265
KEY_F10 = 274
KEY_F11 = 275
KEY_F12 = 276
KEY_F13 = 277
KEY_F14 = 278
KEY_F15 = 279
KEY_F16 = 280
KEY_F17 = 281
KEY_F18 = 282
KEY_F19 = 283
KEY_F2 = 266
KEY_F20 = 284
KEY_F21 = 285
KEY_F22 = 286
KEY_F23 = 287
KEY_F24 = 288
KEY_F25 = 289
KEY_F26 = 290
KEY_F27 = 291
KEY_F28 = 292
KEY_F29 = 293
KEY_F3 = 267
KEY_F30 = 294
KEY_F31 = 295
KEY_F32 = 296
KEY_F33 = 297
KEY_F34 = 298
KEY_F35 = 299
KEY_F36 = 300
KEY_F37 = 301
KEY_F38 = 302
KEY_F39 = 303
KEY_F4 = 268
KEY_F40 = 304
KEY_F41 = 305
KEY_F42 = 306
KEY_F43 = 307
KEY_F44 = 308
KEY_F45 = 309
KEY_F46 = 310
KEY_F47 = 311
KEY_F48 = 312
KEY_F49 = 313
KEY_F5 = 269
KEY_F50 = 314
KEY_F51 = 315
KEY_F52 = 316
KEY_F53 = 317
KEY_F54 = 318
KEY_F55 = 319
KEY_F56 = 320
KEY_F57 = 321
KEY_F58 = 322
KEY_F59 = 323
KEY_F6 = 270
KEY_F60 = 324
KEY_F61 = 325
KEY_F62 = 326
KEY_F63 = 327
KEY_F7 = 271
KEY_F8 = 272
KEY_F9 = 273
KEY_FIND = 362
KEY_HELP = 363
KEY_HOME = 262
KEY_IC = 331
KEY_IL = 329
KEY_LEFT = 260
KEY_LL = 347
KEY_MARK = 364
KEY_MAX = 511
KEY_MESSAGE = 365
KEY_MIN = 257
KEY_MOUSE = 409
KEY_MOVE = 366
KEY_NEXT = 367
KEY_NPAGE = 338
KEY_OPEN = 368
KEY_OPTIONS = 369
KEY_PPAGE = 339
KEY_PREVIOUS = 370
KEY_PRINT = 346
KEY_REDO = 371
KEY_REFERENCE = 372
KEY_REFRESH = 373
KEY_REPLACE = 374
KEY_RESET = 345
KEY_RESIZE = 410
KEY_RESTART = 375
KEY_RESUME = 376
KEY_RIGHT = 261
KEY_SAVE = 377
KEY_SBEG = 378
KEY_SCANCEL = 379
KEY_SCOMMAND = 380
KEY_SCOPY = 381
KEY_SCREATE = 382
KEY_SDC = 383
KEY_SDL = 384
KEY_SELECT = 385
KEY_SEND = 386
KEY_SEOL = 387
KEY_SEXIT = 388
KEY_SF = 336
KEY_SFIND = 389
KEY_SHELP = 390
KEY_SHOME = 391
KEY_SIC = 392
KEY_SLEFT = 393
KEY_SMESSAGE = 394
KEY_SMOVE = 395
KEY_SNEXT = 396
KEY_SOPTIONS = 397
KEY_SPREVIOUS = 398
KEY_SPRINT = 399
KEY_SR = 337
KEY_SREDO = 400
KEY_SREPLACE = 401
KEY_SRESET = 344
KEY_SRIGHT = 402
KEY_SRSUME = 403
KEY_SSAVE = 404
KEY_SSUSPEND = 405
KEY_STAB = 340
KEY_SUNDO = 406
KEY_SUSPEND = 407
KEY_UNDO = 408
KEY_UP = 259

OK = 0

REPORT_MOUSE_POSITION = 134217728

version = b'2.2'

__version__ = b'2.2'

# functions

def baudrate(*args, **kwargs): # real signature unknown
    pass

def beep(*args, **kwargs): # real signature unknown
    pass

def can_change_color(*args, **kwargs): # real signature unknown
    pass

def cbreak(*args, **kwargs): # real signature unknown
    pass

def color_content(*args, **kwargs): # real signature unknown
    pass

def color_pair(*args, **kwargs): # real signature unknown
    pass

def curs_set(*args, **kwargs): # real signature unknown
    pass

def def_prog_mode(*args, **kwargs): # real signature unknown
    pass

def def_shell_mode(*args, **kwargs): # real signature unknown
    pass

def delay_output(*args, **kwargs): # real signature unknown
    pass

def doupdate(*args, **kwargs): # real signature unknown
    pass

def echo(*args, **kwargs): # real signature unknown
    pass

def endwin(*args, **kwargs): # real signature unknown
    pass

def erasechar(*args, **kwargs): # real signature unknown
    pass

def filter(*args, **kwargs): # real signature unknown
    pass

def flash(*args, **kwargs): # real signature unknown
    pass

def flushinp(*args, **kwargs): # real signature unknown
    pass

def getmouse(*args, **kwargs): # real signature unknown
    pass

def getsyx(*args, **kwargs): # real signature unknown
    pass

def getwin(*args, **kwargs): # real signature unknown
    pass

def halfdelay(*args, **kwargs): # real signature unknown
    pass

def has_colors(*args, **kwargs): # real signature unknown
    pass

def has_ic(*args, **kwargs): # real signature unknown
    pass

def has_il(*args, **kwargs): # real signature unknown
    pass

def has_key(*args, **kwargs): # real signature unknown
    pass

def initscr(*args, **kwargs): # real signature unknown
    pass

def init_color(*args, **kwargs): # real signature unknown
    pass

def init_pair(*args, **kwargs): # real signature unknown
    pass

def intrflush(*args, **kwargs): # real signature unknown
    pass

def isendwin(*args, **kwargs): # real signature unknown
    pass

def is_term_resized(*args, **kwargs): # real signature unknown
    pass

def keyname(*args, **kwargs): # real signature unknown
    pass

def killchar(*args, **kwargs): # real signature unknown
    pass

def longname(*args, **kwargs): # real signature unknown
    pass

def meta(*args, **kwargs): # real signature unknown
    pass

def mouseinterval(*args, **kwargs): # real signature unknown
    pass

def mousemask(*args, **kwargs): # real signature unknown
    pass

def napms(*args, **kwargs): # real signature unknown
    pass

def newpad(*args, **kwargs): # real signature unknown
    pass

def newwin(*args, **kwargs): # real signature unknown
    pass

def nl(*args, **kwargs): # real signature unknown
    pass

def nocbreak(*args, **kwargs): # real signature unknown
    pass

def noecho(*args, **kwargs): # real signature unknown
    pass

def nonl(*args, **kwargs): # real signature unknown
    pass

def noqiflush(*args, **kwargs): # real signature unknown
    pass

def noraw(*args, **kwargs): # real signature unknown
    pass

def pair_content(*args, **kwargs): # real signature unknown
    pass

def pair_number(*args, **kwargs): # real signature unknown
    pass

def putp(*args, **kwargs): # real signature unknown
    pass

def qiflush(*args, **kwargs): # real signature unknown
    pass

def raw(*args, **kwargs): # real signature unknown
    pass

def resetty(*args, **kwargs): # real signature unknown
    pass

def reset_prog_mode(*args, **kwargs): # real signature unknown
    pass

def reset_shell_mode(*args, **kwargs): # real signature unknown
    pass

def resizeterm(*args, **kwargs): # real signature unknown
    pass

def resize_term(*args, **kwargs): # real signature unknown
    pass

def savetty(*args, **kwargs): # real signature unknown
    pass

def setsyx(*args, **kwargs): # real signature unknown
    pass

def setupterm(*args, **kwargs): # real signature unknown
    pass

def start_color(*args, **kwargs): # real signature unknown
    pass

def termattrs(*args, **kwargs): # real signature unknown
    pass

def termname(*args, **kwargs): # real signature unknown
    pass

def tigetflag(*args, **kwargs): # real signature unknown
    pass

def tigetnum(*args, **kwargs): # real signature unknown
    pass

def tigetstr(*args, **kwargs): # real signature unknown
    pass

def tparm(*args, **kwargs): # real signature unknown
    pass

def typeahead(*args, **kwargs): # real signature unknown
    pass

def unctrl(*args, **kwargs): # real signature unknown
    pass

def ungetch(*args, **kwargs): # real signature unknown
    pass

def ungetmouse(*args, **kwargs): # real signature unknown
    pass

def unget_wch(*args, **kwargs): # real signature unknown
    pass

def update_lines_cols(*args, **kwargs): # real signature unknown
    pass

def use_default_colors(*args, **kwargs): # real signature unknown
    pass

def use_env(*args, **kwargs): # real signature unknown
    pass

# classes

class error(Exception):
    # no doc
    def __init__(self, *args, **kwargs): # real signature unknown
        pass

    __weakref__ = property(lambda self: object(), lambda self, v: None, lambda self: None)  # default
    """list of weak references to the object (if defined)"""



# variables with complex values

_C_API = None # (!) real value is ''

__loader__ = None # (!) real value is ''

__spec__ = None # (!) real value is ''

