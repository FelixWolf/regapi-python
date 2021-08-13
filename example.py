#!/usr/bin/env python3
"""
Name: example.py
Purpose: RegAPI example

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
#WARNING: This is a example, it is not designed to be secure!
#In production, you should implement captchas and field validation!
#This file is useful for getting a gist of how this API works, and how to set it
#up.
from http.server import BaseHTTPRequestHandler, HTTPServer
import regapi
import uuid
import urllib.parse
#Configuration
#Host address. Leave this empty for the default network interface
host = ''
#Host port. Can be anything you want over the number 1024 and below 65535.
port = 8088

config = {
    #1 is mainland
    "estate": 1,
    #Wengen is http://maps.secondlife.com/secondlife/Wengen/23/215/1101
    #This is a public Linden owned lodge
    "region": "Wengen",
    #Put them in front of the lodge
    "location": [23, 211, 86],
    #Make them face south
    "lookat": [0, -1, 0],
    #If you have an experience, you can put it here:
    "experience": uuid.UUID("00000000-0000-0000-0000-000000000000"),
    #If you have a group, put it's group name here:
    "group": ""
}
#Capability list, paste what you get from getCapabilities.py here
capabilities = {
    "example_capability": "https://cap.secondlife.com/cap/0/UUID",
    
}

regPage = """<!DOCTYPE html>
<html>
    <head>
        <title>Example registration page</title>
    </head>
    <body>
        <h1>Welcome to example.edu!</h1>
        Welcome Student! Please create an account below:
        <fieldset>
            <form method="post" action="/register">
                <label>Username: 
                    <input name="username" autocomplete="name" value="{username}" size="32">
                </label><br/>
                <label>Starting Avatar: 
                    <select name="avatar">
                        {avatars}
                    </select>
                </label><br/>
                <label>Receive emails: 
                    <input type="checkbox" name="marketing" />
                </label><br/>
                Are you an adult?:<br/>
                &nbsp;&nbsp;&nbsp;&nbsp;<label>No: <input type="radio" name="maturity" value="General" checked="true"></label><br/>
                &nbsp;&nbsp;&nbsp;&nbsp;<label>Yes: <input type="radio" name="maturity" value="Adult"></label><br/>
                <br/>
                <input type="submit" />
            </form>
        </fieldset>
    </body>
</html>
"""

errorPage = """<!DOCTYPE html>
<html>
    <head>
        <title>Uh oh!</title>
    </head>
    <body>
        <h1>An error occurred!</h1>
        {error}<br/>
        <form method="get" action="/">
            <input type="submit" value="Restart!" />
        </form>
    </body>
</html>
"""

successPage = """<!DOCTYPE html>
<html>
    <head>
        <title>Ready to go!</title>
    </head>
    <body>
        <h1>Account created!</h1>
        Congradulations {username}! Your account is ready to go!<br/>
        Need to install Second Life? <a href="https://secondlife.com/support/downloads/">Click here</a>!
    </body>
</html>
"""

ra = regapi.RegAPI(capabilities, cache = regapi.FileCache("regapi"))

class HandleRequests(BaseHTTPRequestHandler):
    def __init__(self, socket, *args, **kwargs):
        self.bindaddr = socket.getsockname()
        super().__init__(socket, *args, **kwargs)
    
    def beginResponse(self, code, headers={}):
        self.send_response(code)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
    
    def do_GET(self):
        path = self.path.split("?", 1)
        query = ""
        if len(path) == 1:
            path, = path
        else:
            path, query = path
            query = urllib.parse.parse_qs(query)
        
        if path == "/":
            avatars = ""
            for i, name in ra.getAvatars().items():
                #Iterate over all the avatars and make them a option
                avatars +="\n<option value=\"{}\">{}</option>".format(i, name)
            #Pass the generated fields to the format string
            self.beginResponse(200, {'Content-type': 'text/html'})
            self.wfile.write(regPage.format(username=regapi.regapi.generateUniqueName(), avatars=avatars).encode())
        elif path == "/success":
            self.beginResponse(200, {'Content-type': 'text/html'})
            self.wfile.write(successPage.format(username=query.get("username",["UNKNOWN!"])[0]).encode())
        elif path == "/error":
            self.beginResponse(200, {'Content-type': 'text/html'})
            self.wfile.write(errorPage.format(error="There was a problem completing the registration!").encode())
        else:
            self.beginResponse(404, {'Content-type': 'text/html'})
            self.wfile.write(errorPage.format(error="Page not found!").encode())
    
    def do_POST(self):
        path = self.path.split("?", 1)
        query = ""
        if len(path) == 1:
            path, = path
        else:
            path, query = path
        
        if path == "/register":
            content_len = int(self.headers.get('content-length', 0))
            post_body = self.rfile.read(content_len)
            body = urllib.parse.parse_qs(post_body.decode())
            
            #First parse the username
            username = body.get("username")
            if type(username) != list and len(username) != 1:
                self.beginResponse(400, {'Content-type': 'text/html'})
                self.wfile.write(errorPage.format(error="No username specified!").encode())
                return
            else:
                username = username[0]
            
            #And now the avatar
            avatar = body.get("avatar")
            if type(avatar) != list and len(avatar) != 1:
                self.beginResponse(400, {'Content-type': 'text/html'})
                self.wfile.write(errorPage.format(error="No username specified!").encode())
                return
            else:
                try:
                    #Conver the avatar ID back to a UUID
                    avatar = uuid.UUID(avatar[0])
                except ValueError:
                    self.beginResponse(400, {'Content-type': 'text/html'})
                    self.wfile.write(errorPage.format(error="Invalid avatar ID!").encode())
                    return
            
            #Now get if they opt into marketing
            marketing = body.get("marketing", ["off"])
            if marketing[0] == "on":
                marketing = True
            else:
                marketing = False
            
            #And finally if check if they are an adult
            maturity = body.get("marketing", ["general"])[0]
            if maturity not in ["General", "Moderate", "Adult"]:
                maturity = "General" #Fall back if it isn't set properly
            
            #Make sure they chose a valid avatar
            if avatar not in ra.getAvatars():
                self.beginResponse(400, {'Content-type': 'text/html'})
                self.wfile.write(errorPage.format(error="Sorry, that avatar isn't available!").encode())
                return
            
            #Now see if the username is free
            try:
                if not ra.checkName(username):
                    self.beginResponse(400, {'Content-type': 'text/html'})
                    #This shouldn't happen, but better safe than sorry!
                    self.wfile.write(errorPage.format(error="Sorry, that name is unavailable!").encode())
                    return
            except regapi.RegAPIError as err:
                #No? Print out why
                self.beginResponse(400, {'Content-type': 'text/html'})
                self.wfile.write(errorPage.format(error=err.message).encode())
                return
            
            #Ok now we can begin the actual request!
            try:
                host = self.headers.get("host", self.bindaddr[0])
                port = self.bindaddr[1]
                response = ra.createUser(username,
                    estate = config["estate"],
                    region = config["region"],
                    location = config["location"],
                    lookAt = config["lookat"],
                    marketing = marketing,
                    successUrl = "http://{}:{}/success?username={}".format(host,port,urllib.parse.quote(username)),
                    errorUrl = "http://{}:{}/error".format(host,port),
                    maturity = maturity
                )
                self.beginResponse(302, {
                    "location": response["complete_reg_url"]
                })
                try:
                    if config["experience"] != uuid.UUID("00000000-0000-0000-0000-000000000000"):
                        ra.setUserExperience(response["agent_id"], config["experience"])
                except regapi.RegAPIError as err:
                    print("Failed to set user experience: ",err)
                    #Client is gone by now, don't do anything!
                    pass
                try:
                    if config["group"] != "":
                        ra.addToGroup(username, config["group"])
                except regapi.RegAPIError as err:
                    print("Failed to set user experience: ",err)
                    #Client is gone by now, don't do anything!
                    pass
            except regapi.RegAPIError as err:
                #No? Print out why
                self.beginResponse(400, {'Content-type': 'text/html'})
                self.wfile.write(errorPage.format(error=err.message).encode())
                return
    
    def do_PUT(self):
        self.do_POST()

print("Your server is running at http://{}:{}".format("127.0.0.1" if host == "" else host, port))
HTTPServer((host, port), HandleRequests).serve_forever()