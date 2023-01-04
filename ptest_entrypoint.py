#!/usr/bin/env python3
from src.tests import test__decrypt
import sys

try:
    sys.exit(test__decrypt.main())
except KeyboardInterrupt:
    print('\nReceived escape sequence')
