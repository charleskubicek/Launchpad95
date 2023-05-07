import functools


off = 12
colour_red_flash = 11
colour_red_low = 13
colour_red_full = 15
colour_amber_low = 29
colour_amber_full = 63
colour_yellow = 62
colour_green_low = 28
colour_green_full = 60


def single_non_zero_arg(f_py=None):
    assert callable(f_py) or f_py is None
    def _decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if args[0] != 0:
                return func(*args, **kwargs)
        return wrapper
    return _decorator(f_py) if callable(f_py) else _decorator
