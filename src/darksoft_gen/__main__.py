"""Enable ``python -m darksoft_gen`` as an equivalent of the console script."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
