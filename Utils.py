import os
import subprocess
import sys
from random import choice as random_choice


def is_bundled():
    return getattr(sys, 'frozen', False)


def local_path(path):
    if local_path.cached_path is not None:
        return os.path.join(local_path.cached_path, path)

    if is_bundled():
        # we are running in a bundle
        local_path.cached_path = sys._MEIPASS  # pylint: disable=protected-access,no-member
    else:
        # we are running in a normal Python environment
        local_path.cached_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(local_path.cached_path, path)


local_path.cached_path = None


def default_output_path(path):
    if path == '':
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Output')

    if not os.path.exists(path):
        os.mkdir(path)
    return path


def open_file(filename):
    if sys.platform == 'win32':
        os.startfile(filename)
    else:
        open_command = 'open' if sys.platform == 'darwin' else 'xdg-open'
        subprocess.call([open_command, filename])


def close_console():
    if sys.platform == 'win32':
        # windows
        import ctypes.wintypes
        try:
            ctypes.windll.kernel32.FreeConsole()
        except Exception:
            pass


# Shim for the sole purpose of maintaining compatibility with older versions of
# Python 3. Note: cum weights, as well as fractional weights are unimplemented,
# as neither were used elsewhere at the time of writing.
def random_choices(population, weights=None, k=1):
    pop_size = len(population)
    if weights is None:
        weights = [1] * pop_size
    else:
        assert (pop_size == len(weights)), "population and weights mismatch"

    weighted_pop = []
    for i in range(pop_size):
        for each in range(weights[i]):
            weighted_pop.append(population[i])

    result = []
    for i in range(k):
        result.append(random_choice(weighted_pop))

    return result
