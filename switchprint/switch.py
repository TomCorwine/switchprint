

# This file is part of Switchprint.
#
# Switchprint is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Switchprint is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Switchprint.  If not, see <http://www.gnu.org/licenses/>.


import os, sys
import gobject
import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop


class SwitchBoard(dbus.service.Object):
    """The SwitchBoard class implements the dbus daemon for SwitchBoard."""
    
    def __init__(self):
        namespace = "org.voxelpress.switchprint"
        bus_name = dbus.service.BusName(namespace, bus=dbus.SessionBus())
        dbus.service.Object.__init__(
            self, bus_name, "/" + namespace.replace(".", "/"))
        

def daemon():
    """
    Creates the switchprint daemon.
    """

    # TODO: daemonize this
    main_loop = gobject.MainLoop()
    DBusGMainLoop(set_as_default=True)
    switchboard = SwitchBoard()
    main_loop.run()
