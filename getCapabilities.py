#!/usr/bin/env python3
"""
Name: getCapabilities
Purpose: Simple utility to get capability info

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
import regapi
import getpass
import json

username = input("Enter your username: ")
password = getpass.getpass("Enter your password: ")

print("Please wait, getting capability list...")
api = regapi.RegAPI()
caps = api.getCapabilities(username, password, IKnowWhatIAmDoing = True)
print("WARNING: Capabilities are tied to your account.")
print("Any abuse will be traced back to you. So keep these secure!")
print("Here are your capabilities!:")
print(json.dumps(caps, indent = 4))