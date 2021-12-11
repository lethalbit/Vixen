#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
import sys
import os
from pathlib import Path

vixen_path = Path(sys.argv[0]).resolve()


if (vixen_path.parent / 'vixen').is_dir():
	sys.path.insert(0, str(vixen_path.parent))

from vixen import main

if __name__ == '__main__':
	sys.exit(main())


