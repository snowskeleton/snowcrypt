#!/usr/bin/env python3
from src.snowcrypt import main
import sys
import logging


logging.basicConfig(level=logging.DEBUG)

try:
    sys.exit(main.main())
except KeyboardInterrupt:
    print('\nReceived escape sequence')
