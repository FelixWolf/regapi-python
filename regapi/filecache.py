#!/usr/bin/env python3
"""
Name: filecache.py
Purpose: Implements a simple file cache

Copyright (c) 2021 Kyler Eastridge

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
"""

import tempfile
import string
import os
import getpass
import pickle
import time

def getPath(cacheName):
    safe = string.ascii_letters+string.digits
    safe = "".join(c for c in getpass.getuser() if c in safe).strip()
    return os.path.join(tempfile.gettempdir(), "{}_{}.fc".format(cacheName, safe))

class FileCache:
    def __init__(self, cacheName = "filecache", path = None, expiry = 60*60):
        if not path:
            path = getPath(cacheName)
        self.path = path
        try:
            with open(path, "rb", 0o600) as f:
                self.data = pickle.load(f)
        except (FileNotFoundError, pickle.PickleError):
            self.data = {}
    
    def write(self):
        with open(self.path, "wb", 0o600) as f:
            pickle.dump(self.data, f)
    
    def set(self, key, value):
        self.data[key] = {
            "updated": time.time(),
            "data": value
        }
        self.write()
    
    def get(self, key, default = None, expires = None):
        tmp = self.data.get(key, {"updated": 0, "data": default})
        if expires and tmp["updated"] > time.now() - expires:
            del tmp[key]
            self.write()
            return default
        return tmp["data"]

