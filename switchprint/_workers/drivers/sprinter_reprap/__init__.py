

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


import sys, os
import serial, time
from switchprint._workers.drivers.common import DriverBase


METADATA = {
    "hardware" : ["usbACM"],
    }


BAUDS = (2400, 9600, 19200, 38400, 57600, 115200, 250000)


#lifted from pronterface without knowing what it does
def control_ttyhup(port, disable_hup):
    """Controls the HUPCL"""
    if sys.platform == "linux2":
        if disable_hup:
            os.system("stty -F %s -hup" % port)
        else:
            os.system("stty -F %s hup" % port)


class Driver(DriverBase):
    """Driver for reprap-style printers running the sprinter firmware."""

    def __init__(self):
        self.__s = None
        self.__port = None
        self.__uuid = "butts"

    def reset(self):
        if self.__s:
            #lifted from pronterface without knowing what it does
            self.__s.setDTR(1)
            time.sleep(0.2)
            self.__s.setDTR(0)

    def __write(self, command, block=False):
        self.__s.write(command+"\n")
        if block:
            data = []
            while True:
                data += self.__s.readlines()
                if data and data[-1].strip() == "ok":
                    data.pop()
                    return map(str.strip, data)
                else:
                    time.sleep(.05)
       
    def auto_detect(self, port):
        """Called by a hardware monitor durring a hardware connect
        event.  Return True if this driver claims the device.
        This function should also set self.uuid."""
        
        control_ttyhup(port, True)
        
        for baud in BAUDS[::-1]:
            try:
                self.reset()
                self.__s = serial.Serial(port, baud, timeout=0.25)
                time.sleep(1)
                post = "".join(self.__s.readlines()).strip()
                for trigger in ("sprinter", "marlin"):
                    if post.lower().count(trigger):
                        self.__port = port
                        self.__baud = baud
                        self.post = post
                        self.info = "".join(self.__write("M115", True))
                        return True
            except ValueError:
                continue

    def inform_reconnect(self):
        """This function is called by a worker subprocess when a
        driver is detected, but the corresponding printer object
        already exists.  In which case, this function should return a
        simple argument list which can be pushed to the already
        existing service, so that it may call the informed_reconnect
        function in it's driver instance."""
        return self.__port, self.__baud

    def informed_reconnect(self, port, baud):
        """The arguments for this function should match what is
        returned by inform_reconnect.  This causes the driver to
        disconnect from whatever device it thinks it is connected to,
        and attach to whatever ostensibly new device is described."""
        
        control_ttyhup(port, True)
        self.__port = port
        self.__baud = baud
        self.__s = serial.Serial(port, baud, timeout=0.25)
        time.sleep(1)
        self.post = "".join(self.__s.readlines()).strip()        
        self.info = "".join(self.__write("M115", True))


    #### printer control functions ###

    def debug(self, command):
        """Send a raw command to the printer and return its
        response.""" 
        return "".join(self.__write(command, True))
        

    def home(self, x_axis=True, y_axis=True, z_axis=True):
        """Moves the named axises until they trigger their
        endstops."""
    
        if x_axis and y_axis and z_axis:
            self.__write("G28", True)
        elif x_axis or y_axis or z_axis:
            cmd = ["G28"]
            if x_axis:
                cmd.append("X0")
            if y_axis:
                cmd.append("Y0")
            if z_axis:
                cmd.append("Z0")
            self.__write(" ".join(cmd), True)

    
    def relative_mode(self):
        self.__write("G91")


    def absolute_mode(self):
        self.__write("G90")


    def move(self, x=0, y=0, z=0):
        cmd = "G0 X{0} Y{1} Z{2}".format(x, y, z)
        self.__write(cmd)

