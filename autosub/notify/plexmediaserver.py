import autosub
import logging
import library.requests as requests
import base64

from xml.etree import ElementTree as ET

log = logging.getLogger('thelogger')

def test_update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword):
    log.info("Trying to update the TV shows library.")
    plexservertoken = None
    if autosub.PLEXSERVERTOKEN:
        plexservertoken = autosub.PLEXSERVERTOKEN

    return _update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword, plexservertoken)

def send_update_library():
    log.info("Trying to update the TV shows library.")
    if not autosub.PLEXSERVERPORT :
        plexserverhost = "127.0.0.1"
    else:
        plexserverhost = autosub.PLEXSERVERHOST
    if not autosub.PLEXSERVERPORT:
        plexserverport = "32400"
    else:
        plexserverport = autosub.PLEXSERVERPORT.strip()
    plexserverusername = autosub.PLEXSERVERUSERNAME
    plexserverpassword = autosub.PLEXSERVERPASSWORD
    plexservertoken = autosub.PLEXSERVERTOKEN
    return _update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword, plexservertoken)

def _update_library(plexserverhost, plexserverport, plexserverusername, plexserverpassword, plexservertoken):
    if not plexserverhost:
        plexserverhost = autosub.PLEXSERVERHOST
    
    if not plexserverport:
        plexserverport = int(autosub.PLEXSERVERPORT)

    if not plexserverusername:
        plexserverusername = autosub.PLEXSERVERUSERNAME

    if not plexserverpassword:
        plexserverpassword = autosub.PLEXSERVERPASSWORD

    if not plexservertoken:
        plexservertoken = autosub.PLEXSERVERTOKEN

    #Maintain support for older Plex installations without myPlex
    if not plexservertoken and not plexserverusername and not plexserverpassword:
        url = "http://%s:%s/library/sections" % (plexserverhost, plexserverport)

        try:
            response = requests.get(url,timeout=10)
        except:
            log.error("Error while trying to contact plexmedia server")
            return False
    #SubLines = re.findall('<tr class="epeven completed">(.*?)</tr>', SubOverviewPage, re.S)
    else:
        #Fetch X-Plex-Token if it doesn't exist but a username/password do
        if not plexservertoken and plexserverusername and plexserverpassword:
            log.info("Fetching a new X-Plex-Token from plex.tv")
            authheader = "Basic %s" % base64.encodestring('%s:%s' % (plexserverusername, plexserverpassword))[:-1]

            headers = {
                "Authorization": authheader,
                "X-Plex-Product": "AutoSub Notifier",
                "X-Plex-Client-Identifier": "b3a6b24dcab2224bdb101fc6aa08ea5e2f3147d6",
                "X-Plex-Version": "1.0"
            }
            try:
                response = requests.post("https://plex.tv/users/sign_in.xml", headers=headers,verify=autosub.CERT,timeout=10);
            except:
                log.error("Error while trying to contact plexmediaserver")
                return False

            auth_tree = ET.fromstring(response.text)
            plexservertoken = auth_tree.findall(".//authentication-token")[0].text
            autosub.PLEXSERVERTOKEN = plexservertoken

        if plexservertoken:
            #Add X-Plex-Token header for myPlex support workaround
            try:
                response = requests.get('%s/%s?X-Plex-Token=%s' % (
                    "%s:%s" % (plexserverhost, plexserverport),
                    'library/sections',
                    plexservertoken
                ),timeout=10)
            except Exception as error:
                log.error("Error from get header. Error is: %s" % error)
                return False
            xml_sections = ET.fromstring(response.text)
    try:
        sections = xml_sections.findall('Directory')
    except:
        pass
    if not sections:
        log.info("Server not running on: %s:%s" % (plexserverhost, plexserverport))
        return False

    for s in sections:
        if s.get('type') == "title":
            if plexservertoken:
                try:
                    requests.get('%s/%s?X-Plex-Token=%s' % (
                        "%s:%s" % (plexserverhost, plexserverport),
                        "library/sections/%s/refresh" % (s.get('key')),
                        plexservertoken
                    ),timeout=10)
                    log.info("TV Shows library (%s) is currently updating." % s.get('title'))
                    return True
                except Exception, e:
                    log.error("Error updating library section: %s" % e)
                    return False
            else:
                url = "http://%s:%s/library/sections/%s/refresh" % (plexserverhost, plexserverport, s.getAttribute('key'))
                try:
                    requests.get(url,timeout=10)
                    log.info("TV Shows library is currently updating.")
                    return True
                except Exception, e:
                    log.error("Error updating library section: %s" % e)
                    return False
    return True