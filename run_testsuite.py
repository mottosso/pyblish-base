import os
import sys
import warnings

# Expose Pyblish to PYTHONPATH
path = os.path.dirname(__file__)
sys.path.insert(0, path)

from pyblish.vendor import nose, mock

warnings.warn = mock.MagicMock()


if __name__ == '__main__':
    argv = sys.argv[:]
    argv.extend(['--exclude=vendor', '--with-doctest', '--verbose'])
    nose.main(argv=argv)
