#!/usr/bin/env python3
"""
Name: __init__.py
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
from .regapi import RegAPIError, RegAPI
from .filecache import FileCache
from . import llsd

__author__ = "Kyler Eastridge"
__copyright__ = "Copyright 2021, Kyler Eastridge"
__credits__ = ["Kyler Eastridge"]
__license__ = "zlib"
__version__ = "1.0.0"
__maintainer__ = "Kyler Eastridge"
__email__ = "felix.wolfz@gmail.com"
__status__ = "Production"