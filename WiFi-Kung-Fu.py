#!/usr/bin/python
#
###############################################################################################################################################
#
# ABOUT THIS PROGRAM
#
#	WiFi-Kung-Fu.py
#	https://github.com/Headbolt/WiFi-Kung-Fu
#
#   This Script is designed for use in JAMF
#   - This script will ...
#       Enumerate the WiFi AP's configured and reorder according to variables
#		defined in JAMF.
#
# As written, this requires the following:
# - OS X 10.11+
# - python 2.6 or 2.7 (for collections.namedtuple usage, should be fine as default python in 10.6 is 2.6)
# - pyObjC (as such, recommended to be used with native OS X python install)
#
# Run with root
#
###############################################################################################################################################
#
# HISTORY
#
#   Version: 1.1 - 10/02/2020
#
#   - 03/02/2019 - V1.0 - Created by Headbolt by Pulling from multiple references
#
#	- 10/02/2020 - V1.1 - Updated by Headboltwith better information
#
###############################################################################################################################################
#
# DEFINE VARIABLES & READ IN PARAMETERS
#
###############################################################################################################################################
#
# Import Modules
import objc, sys, ctypes.util, os.path, collections
from Foundation import NSOrderedSet
#
preferred_SSID    = sys.argv[4] # Grab the Preferred WiFi SSID from JAMF variable #4
third_to_last_SSID = sys.argv[5] # Grab the 3rd to Last WiFi SSID from JAMF variable #4
second_to_last_SSID = sys.argv[6] # Grab the Second to Last WiFi SSID from JAMF variable #4
last_SSID         = sys.argv[7] # Grab the Last WiFi SSID from JAMF variable #4
#
###############################################################################################################################################
#
# SCRIPT CONTENTS - DO NOT MODIFY BELOW THIS LINE
#
###############################################################################################################################################
#
print ""
print "Preferred SSID = ", preferred_SSID
print "Third To Last SSID = ", third_to_last_SSID
print "Second To Last SSID = ", second_to_last_SSID
print "Last SSID = ", last_SSID
print ""
#
def load_objc_framework(framework_name):
    # Utility function that loads a Framework bundle and creates a namedtuple where the attributes are the loaded classes from the Framework bundle
    loaded_classes = dict()
    framework_bundle = objc.loadBundle(framework_name, bundle_path=os.path.dirname(ctypes.util.find_library(framework_name)), module_globals=loaded_classes)
    return collections.namedtuple('AttributedFramework', loaded_classes.keys())(**loaded_classes)


CoreWLAN = load_objc_framework('CoreWLAN') # Load the CoreWLAN.framework (10.6+)
#
interfaces = dict() # Load all available wifi interfaces
for i in CoreWLAN.CWInterface.interfaceNames():
    interfaces[i] = CoreWLAN.CWInterface.interfaceWithName_(i)

# Repeat the configuration with every wifi interface
for i in interfaces.keys():
    # Grab a mutable copy of this interface's configuration
    configuration_copy = CoreWLAN.CWMutableConfiguration.alloc().initWithConfiguration_(interfaces[i].configuration())
    # Find all the preferred/remembered network profiles
    profiles = list(configuration_copy.networkProfiles())
    # Grab all the SSIDs, in order
    SSIDs = [x.ssid() for x in profiles]
    # Check to see if our preferred SSID is in the list
    if (preferred_SSID in SSIDs):
        # Apparently it is, so let's adjust the order
        # Profiles with matching SSIDs will move to the front, the rest will remain at the end
        # Order is preserved, example where 'ssid3' is preferred:
        #    Original: [ssid1, ssid2, ssid3, ssid4]
        #   New order: [ssid3, ssid1, ssid2, ssid4]
        profiles.sort(key=lambda x: x.ssid() == preferred_SSID, reverse=True)
        # Now we move third_to_last_SSID to the end        
        profiles.sort(key=lambda x: x.ssid() == third_to_last_SSID, reverse=False)
        # Now we move second_to_last_SSID to the end
        profiles.sort(key=lambda x: x.ssid() == second_to_last_SSID, reverse=False)
        # Now we move last_SSID to the end (bumping next_to_last_SSID)
        profiles.sort(key=lambda x: x.ssid() == last_SSID, reverse=False)
        # Now we have to update the mutable configuration
        # First convert it back to a NSOrderedSet
        profile_set = NSOrderedSet.orderedSetWithArray_(profiles)
        # Then set/overwrite the configuration copy's networkProfiles
        configuration_copy.setNetworkProfiles_(profile_set)
        # Then update the network interface configuration
        result = interfaces[i].commitConfiguration_authorization_error_(configuration_copy, None, None)
