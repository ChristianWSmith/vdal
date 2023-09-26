#!/usr/bin/env python

import shutil, os

VDAL_CACHE_DIR = f"{os.getenv('XDG_CACHE_HOME')}/vdal"
shutil.rmtree(VDAL_CACHE_DIR)
