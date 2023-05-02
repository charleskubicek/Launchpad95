import functools


def single_non_zero_arg(f_py=None):
    assert callable(f_py) or f_py is None
    def _decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if args[0] != 0:
                return func(*args, **kwargs)
        return wrapper
    return _decorator(f_py) if callable(f_py) else _decorator
