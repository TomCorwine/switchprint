

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


import json
import gobject
import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from common import path_from_uuid, name_from_uuid, list_printers


class PrintServer(dbus.service.Object):
    """
    """

    def __init__(self, bus, device_path, printer_uuid, driver):

        self.__device_path = device_path
        self.__driver = driver

        self.status = "ready"

        self.__path = path_from_uuid(printer_uuid)
        self.__name = name_from_uuid(printer_uuid)
        bus_name = dbus.service.BusName(self.__name, bus=bus)
        print "Printer Online:", self.__name
        dbus.service.Object.__init__(self, bus_name, self.__path)

    @dbus.service.method('org.voxelpress.hardware', out_signature='b')
    def verify_disconnect(self, device_path):
        """Called when any device disconnects.  If that device is this
        printer, then act accordingly."""

        if device_path == self.__device_path:
            self.status = "offline"
            print "Printer Offline:", self.__name
            # TODO trigger an on_disconect or on_status_change signal
            return True

        else:
            return False

    @dbus.service.method('org.voxelpress.hardware', in_signature='ss')
    def force_reconnect(self, device_path, reconnect_args):
        self.__device_path = device_path
        self.__driver.informed_reconnect(*json.loads(reconnect_args))
        self.status = "ready"
        print "Printer Reconnected:", self.__name
        # TODO trigger an on_disconect or on_status_change signal

    @dbus.service.method('org.voxelpress.hardware', in_signature='s', out_signature='s')
    def debug(self, command):
        return str(self.__driver.debug(command))

    @dbus.service.method('org.voxelpress.hardware', in_signature='bbb')
    def home(self, x_axis, y_axis, z_axis):
        self.__driver.home(x_axis, y_axis, z_axis)

    @dbus.service.method('org.voxelpress.hardware')
    def relative_mode(self):
        self.__driver.relative_mode()

    @dbus.service.method('org.voxelpress.hardware')
    def absolute_mode(self):
        self.__driver.absolute_mode()
    
    @dbus.service.method('org.voxelpress.hardware', in_signature='ddd')
    def move(self, x, y, z):
        self.__driver.move(x, y, z)
    


def start_server_loop(bus_type, device_path, printer_uuid, driver):

    # do this before creating any bus object!
    main_loop = gobject.MainLoop()
    DBusGMainLoop(set_as_default=True)

    if bus_type == "session":
        bus = dbus.SessionBus()
    elif bus_type == "system":
        bus = dbus.SystemBus()

    printers = list_printers(bus)
    check_name = name_from_uuid(printer_uuid)
    if printers.count(check_name):
        reconnect_args = json.dumps(driver.inform_reconnect())
        path = "/" + check_name.replace(".", "/")
        prox = bus.get_object(check_name, path)
        prox.force_reconnect(device_path, reconnect_args)
    else:
        server = PrintServer(bus, device_path, printer_uuid, driver)

        # notify the main process that a new printer exists
        switchboard = bus.get_object(
            "org.voxelpress.hardware", "/org/voxelpress/hardware")
        switchboard.worker_new_printer(str(printer_uuid))
        main_loop.run()

