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
from . import llsd
import uuid
import warnings
import datetime
import urllib.request
import urllib.error
import urllib.parse

def generateUniqueName(prefix = "Resident"):
    """Returns a unique username that is almost guarenteed not to be registered.
    Useful for testing."""
    now = datetime.datetime.now()
    return "{prefix}{year:0>4}{month:0>2}{day:0>2}{hour:0>2}{minute:0>2}"\
        "{second:0>2}".format(
        prefix = prefix,
        year = now.year,
        month = now.month,
        day = now.day,
        hour = now.hour,
        minute = now.minute,
        second = now.second,
    )

def parseUsername(input):
    """Convert a string or partial list into a tuple representing a username.
        Accepts firstname.lastname, firstname, ("firstname"), etc.
        Returns ("firstname", "lastname")
    """
    if type(input) == tuple or type(input) == list:
        if len(input) == 1:
            return (input[0], "resident")
        elif len(input) == 2:
            return tuple(input)
        else:
            raise None
    elif type(input) == str:
        if "." in input:
            if " " in input:
                return None
            input = input.split(".")
            if len(input) == 1:
                return (input[0], "resident")
            elif len(input) == 2:
                return tuple(input)
            else:
                return None
        elif " " in input:
            if "." in input:
                return None
            input = input.split(" ")
            if len(input) == 1:
                return (input[0], "resident")
            elif len(input) == 2:
                return tuple(input)
            else:
                return None
        else:
            return (input, "resident")
    return None

def doRequest(*args, **kwargs):
    """Internal function, used to wrap urlopen to accept HTTP errors and not
        throw them at the window."""
    try:
        return urllib.request.urlopen(*args, **kwargs)
    except urllib.error.HTTPError as e:
        return e

class RegAPIError(BaseException):
    """General purpose RegAPI error"""
    def __init__(self, expression, message, code = -1):
        """Expression is the "error message", message is the "description",
            code is the error code given by the RegAPI. If it is -1, it is
            generated internally."""
        self.expression = expression
        self.message = message
        self.code = code

class RegAPI:
    """The RegAPI class, the big feature, the whole burrito!"""
    LASTNAME_RESIDENT = 10327
    MATURITY_GENERAL = "General"
    MATURITY_MODERATE = "Moderate"
    MATURITY_ADULT = "Adult"
    
    baseHeaders = {
        "user-agent": "RegAPI Library (Python Edition) By Kyler Eastridge"
    }
    
    def __init__(self, capabilities = None, cache = None):
        """Capabilities is a dictionary of capabilities provided by
            get_reg_capabilities. Cache is a caching object, see caching for
            more information.
        """
        if capabilities == None:
            capabilities = []
        self.capabilities = capabilities
        self.cache = cache
    
    def getCapabilities(self, username, password, IKnowWhatIAmDoing = False):
        """This is a utility function to get the RegAPI capabilities.
            It should only be used by the developer implementing this.
            If you are writing a GUI, set IKnowWhatIAmDoing to True to suppress
            the warning message.
        """
        if not IKnowWhatIAmDoing:
            warnings.warn("""
!!! WARNING:
Storing account information in a script is dangerous. If you are running this
in a production environment, this can result in your account credentials being
leaked if the server becomes misconfiguration or hacked!\
""")
        username = parseUsername(username)
        req = urllib.request.Request(
            "https://cap.secondlife.com/get_reg_capabilities",
            data = urllib.parse.urlencode({
                "first_name": username[0],
                "last_name": username[1],
                "password": password
            }).encode(),
            headers = {
                **self.baseHeaders,
                "content-type": "application/x-www-form-urlencoded"
            }
        )
        
        result = None
        with doRequest(req) as res:
            result = llsd.llsdDecode(res.read())
        #This is funny, but correct.
        #If the request is invalid, it returns an error, but we can only get
        #the error codes after we have successfully get our capabilities.
        if type(result) == list:
            raise self.getError(result[0])
        
        self.capabilities = result
        
        return result
    
    def getCapability(self, cap):
        """Helper function - Get the capability by name, otherwise throw an
            error if we don't have it.
        """
        if cap not in self.capabilities:
            raise RegAPIError("No capability '{}'!".format(cap))
        return self.capabilities[cap]
    
    def getErrorCodes(self):
        """Returns a list of error codes in [[code, name, desc],...] format."""
        cap = self.getCapability("get_error_codes")
        result = None
        if self.cache:
            result = self.cache.get("get_error_codes")
        
        if not result:
            req = urllib.request.Request(
                cap,
                headers = {
                    **self.baseHeaders
                }
            )
            with doRequest(req) as res:
                result = llsd.llsdDecode(res.read())
            
            if self.cache:
                self.cache.set("get_error_codes", result)
        
        return result
    
    def getError(self, errCode):
        """Helper function. Resolve a error code by ID."""
        for code in self.getErrorCodes():
            if code[0] == errCode:
                return RegAPIError(code[1], code[2], code = code[0])
        return RegAPIError("Unknown Error", "Couldn't resolve the error message!")
    
    def getLastNames(self):
        """Returns a list of available usernames in {id: "name", ...} format"""
        cap = self.getCapability("get_last_names")
        result = None
        if self.cache:
            result = self.cache.get("get_last_names")
        
        if not result:
            req = urllib.request.Request(
                cap,
                headers = {
                    **self.baseHeaders
                }
            )
            with doRequest(req) as res:
                result = llsd.llsdDecode(res.read())
            
            if type(result) == list:
                raise self.getError(result[0])
            
            #Convert the keys from strings to integers
            result = {int(k): v for k, v in result.items()}
            
            if self.cache:
                self.cache.set("get_last_names", result)
        
        return result
    
    def getExperiences(self):
        """Returns a list of experiences the capability has access to in
            {id: "name"} format
        """
        cap = self.getCapability("get_experiences")
        result = None
        if self.cache:
            result = self.cache.get("get_experiences")
        
        if not result:
            req = urllib.request.Request(
                cap,
                headers = {
                    **self.baseHeaders
                }
            )
            
            if type(result) == list:
                raise self.getError(result[0])
            
            with doRequest(req) as res:
                result = llsd.llsdDecode(res.read())
            
            #Convert the keys from strings to UUIDs
            result = {uuid.UUID(k): v for k, v in result.items()}
            
            if self.cache:
                self.cache.set("get_experiences", result)
        
        return result
    
    def getAvatars(self):
        """Returns a list of available starting avatars in {id: "name"} format
        """
        cap = self.getCapability("get_avatars")
        result = None
        if self.cache:
            result = self.cache.get("get_avatars")
        
        if not result:
            req = urllib.request.Request(
                cap,
                headers = {
                    **self.baseHeaders
                }
            )
            with doRequest(req) as res:
                result = llsd.llsdDecode(res.read())
            
            if type(result) == list:
                raise self.getError(result[0])
            
            #Convert the keys from strings to UUIDs
            result = {uuid.UUID(k): v for k, v in result.items()}
            
            if self.cache:
                self.cache.set("get_avatars", result)
        
        return result
    
    def checkName(self, username, lastNameId = None):
        """Check if a username is available. Automatically assumes resident is
            the lastname if not specified.
            Raises RegAPIError if not available, returns True if available.
            Might return False if not available!
        """
        cap = self.getCapability("check_name")
        result = None
        req = urllib.request.Request(
            cap,
            headers = {
                **self.baseHeaders,
                "content-type": "application/llsd+xml"
            },
            method = "POST",
            data = llsd.llsdEncode({
                "username": username,
                "last_name_id": lastNameId or self.LASTNAME_RESIDENT
            })
        )
        
        with doRequest(req) as res:
            result = llsd.llsdDecode(res.read())
        
        if type(result) == list:
            raise self.getError(result[0])
        
        return result
    
    def createUser(self, username, lastNameId = None,
                    estate = None, region = None, location = None,
                    lookAt = None, marketing = None, successUrl = None,
                    errorUrl = None, maturity = None):
        """Creates a user with the provided username. Automatically assumes
            resident is the lastname if not specified.
            If estate is specified, region, location and lookAt can also be
                specified.
            location and lookAt must be a tuple of floats representing X, Y, Z.
            marketing will enable Marketing emails from Linden Lab.
            successUrl is where the user will be redirected to after registration.
            errorUrl is where the user will be redirected to if there is an error.
            maturity must be "G", "M", "A", "General", "Mature", "Adult", or
                one of the RegAPI.MATURITY_* values.
        """
        cap = self.getCapability("create_user")
        result = None
        data = {
            "username": username,
            "last_name_id": lastNameId or self.LASTNAME_RESIDENT
        }
        if estate:
            data["limited_to_estate"] = estate
        
        if region:
            data["start_region_name"] = region
        
        if location:
            data["start_local_x"] = float(location[0])
            data["start_local_y"] = float(location[1])
            data["start_local_z"] = float(location[2])
        
        if lookAt:
            data["start_look_at_x"] = float(lookAt[0])
            data["start_look_at_y"] = float(lookAt[1])
            data["start_look_at_z"] = float(lookAt[2])
        
        if marketing:
            data["marketing_emails"] = marketing
        
        if successUrl:
            data["success_url"] = llsd.URI(successUrl)
        
        if errorUrl:
            data["error_url"] = llsd.URI(errorUrl)
        
        if maturity:
            data["maximum_maturity"] = maturity
        
        req = urllib.request.Request(
            cap,
            headers = {
                **self.baseHeaders,
                "content-type": "application/llsd+xml"
            },
            method = "POST",
            data = llsd.llsdEncode(data)
        )
        
        with doRequest(req) as res:
            result = llsd.llsdDecode(res.read())
        
        if type(result) == list:
            raise self.getError(result[0])
        
        return result
    
    def regenerateUserNonce(self, agentId):
        """Regenerate a registration URL. Useful if you have a internal database
            and a user re-requests to create their authorized account.
            AgentID must be a UUID.
        """
        cap = self.getCapability("regenerate_user_nonce")
        result = None
        req = urllib.request.Request(
            cap,
            headers = {
                **self.baseHeaders,
                "content-type": "application/llsd+xml"
            },
            method = "POST",
            data = llsd.llsdEncode({
                "agent_id": agentId
            })
        )
        
        with doRequest(req) as res:
            result = llsd.llsdDecode(res.read())
        
        if type(result) == list:
            raise self.getError(result[0])
        
        return result
    
    def setUserAvatar(self, agentId, avatarId):
        """Set the starting avatar for agentId to avatarId. See getAvatars()
            Both agentId and avatarId must be a UUID.
            **This cannot be used after the resident logs in!**
            **This ability expires after 1 hour of the account creation!**
        """
        cap = self.getCapability("set_user_avatar")
        result = None
        req = urllib.request.Request(
            cap,
            headers = {
                **self.baseHeaders,
                "content-type": "application/llsd+xml"
            },
            method = "POST",
            data = llsd.llsdEncode({
                "agent_id": agentId,
                "avatar_id": avatarId,
            })
        )
        
        with doRequest(req) as res:
            result = llsd.llsdDecode(res.read())
        
        if type(result) == list:
            raise self.getError(result[0])
        
        return result
    
    def setUserExperience(self, agentId, experienceId):
        """Automatically make the user accept a experience.
            agentId and experienceId must both be a UUID.
            **This cannot be used after the resident logs in!**
            **This ability expires after 1 hour of the account creation!**
        """
        cap = self.getCapability("set_user_experience")
        result = None
        
        req = urllib.request.Request(
            cap,
            headers = {
                **self.baseHeaders,
                "content-type": "application/llsd+xml"
            },
            method = "POST",
            data = llsd.llsdEncode({
                "agent_id": agentId,
                "experience_id": experienceId,
            })
        )
        
        with doRequest(req) as res:
            result = llsd.llsdDecode(res.read())
        
        if type(result) == list:
            raise self.getError(result[0])
        
        return result
    
    def addToGroup(self, username, groupName):
        """Add a user to a group that you manage.
            username can be a string or tuple.
            **This CAN be used after the resident logs in!**
            **This ability expires after 1 hour of the account creation!**
        """
        cap = self.getCapability("add_to_group")
        result = None
        username = parseUsername(username)
        req = urllib.request.Request(
            cap,
            headers = {
                **self.baseHeaders,
                "content-type": "application/llsd+xml"
            },
            method = "POST",
            data = llsd.llsdEncode({
                "first": username[0],
                "last": username[1],
                "group_name": groupName
            })
        )
        
        with doRequest(req) as res:
            result = llsd.llsdDecode(res.read())
        
        if type(result) == list:
            raise self.getError(result[0])
        
        return result
