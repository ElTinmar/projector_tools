import time
import string
import itertools
from .projector import (
    SerialProjector,
    ProjectorInfo,
    StrEnum
)
import serial.tools.list_ports 
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class System(StrEnum):
    POWER_ON = "* 0 IR 001\r"
    POWER_OFF = "* 0 IR 002\r"
    FREEZE = "* 0 IR 007\r"
    RESYNC = "* 0 IR 014\r"
    QUERY_MODEL = "* 0 IR 035\r"
    SOURCE = "* 0 IR 031\r"
    HIDE = "* 0 IR 030\r"
    QUERY_NATIVE_RESOLUTION = "* 0 IR 036\r"
    QUERY_COMPANY_NAME = "* 0 IR 037\r"
    QUERY_INFORMATION = "* 0 IR 073\r"
    LANGUAGE = "* 0 IR 049\r"

class Keystone(StrEnum):
    KEYSTONE = "* 0 IR 004\r"
    KEYSTONE_UP = "* 0 IR 042\r"
    KEYSTONE_DOWN = "* 0 IR 043\r"
    KEYSTONE_LEFT = "* 0 IR 044\r"
    KEYSTONE_RIGHT = "* 0 IR 045\r"

class Audio(StrEnum):
    MUTE = "* 0 IR 006\r"
    VOLUME_UP = "* 0 IR 023\r"
    VOLUME_DOWN = "* 0 IR 024\r"
    
class Menu(StrEnum):
    MENU = "* 0 IR 008\r"
    UP = "* 0 IR 009\r"
    DOWN = "* 0 IR 010\r"
    LEFT = "* 0 IR 012\r"
    RIGHT = "* 0 IR 011\r"
    ENTER = "* 0 IR 013\r"
    BACK = "* 0 IR 053\r"

class Source(StrEnum):
    HDMI_1 = "* 0 IR 050\r"
    HDMI_2 = "* 0 IR 068\r"
    HDMI_3 = "* 0 IR 069\r"
    VGA_1 = "* 0 IR 015\r"
    VGA_2 = "* 0 IR 077\r"
    DVI = "* 0 IR 016\r"
    COMPOSITE = "* 0 IR 019\r"
    LAN_WIFI = "* 0 IR 072\r"
    DISPLAY_PORT = "* 0 IR 074\r"

class AspectRatio(StrEnum):
    RATIO_16_9 = "* 0 IR 021\r"
    RATIO_4_3 = "* 0 IR 022\r"
    LETTERBOX = "* 0 IR 040\r"
    NATIVE = "* 0 IR 041\r"

class Zoom(StrEnum):
    ZOOM_IN = "* 0 IR 046\r"
    ZOOM_OUT = "* 0 IR 054\r"

class EcoMode(StrEnum):
    ON = "* 0 IR 051\r"
    QUERY = "* 0 IR 052\r"
    OFF = "* 0 IR 055\r"
    ECOPRO_ON = "* 0 IR 078\r"

class Stereo3D(StrEnum):
    ON = "* 0 IR 056\r"
    OFF = "* 0 IR 057\r"
    TWO_D_TO_THREE_D_ON = "* 0 IR 058\r"
    TWO_D_TO_THREE_D_OFF = "* 0 IR 059\r"
    FORMAT_AUTO = "* 0 IR 060\r"
    FORMAT_FRAME_PACKING = "* 0 IR 061\r"
    FORMAT_SIDE_BY_SIDE_HALF = "* 0 IR 062\r"
    FORMAT_SIDE_BY_SIDE_FULL = "* 0 IR 063\r"
    FORMAT_TOP_AND_BOTTOM = "* 0 IR 064\r"
    FORMAT_FRAME_SEQUENTIAL = "* 0 IR 066\r"
    FORMAT_FIELD_SEQUENTIAL = "* 0 IR 067\r"
    INVERT_LR = "* 0 IR 065\r"

class Picture(StrEnum):
    BRIGHTNESS = "* 0 IR 025\r"
    CONTRAST = "* 0 IR 026\r"
    COLOR_TEMP = "* 0 IR 027\r"
    SATURATION = "* 0 IR 032\r"
    HUE = "* 0 IR 033\r"
    SHARPNESS = "* 0 IR 034\r"
    COLOR_RGB = "* 0 IR 048\r"

class ProjectorQuery(StrEnum):
    LAMP_STATE = "* 0 Lamp ?\r"
    LAMP_HOURS = "* 0 Lamp\r"
    ACTIVE_SOURCE = "* 0 Src ?\r"

# TODO check if that is universal
class LampState(StrEnum):
    OFF = 'OFF'
    WAIT = 'LAMP 0' 
    ON = 'LAMP 1'

class AcerProjector(SerialProjector):

    POWER_ON_WAIT_SECONDS = 30
    POWER_OFF_WAIT_SECONDS = 20
    RESPONSE_WAIT_SECONDS = 0.1

    @classmethod
    def list_available_projectors(cls, *args, **kwargs) -> List[ProjectorInfo]:
        available_projectors = []        
        ports = serial.tools.list_ports.comports()
        for port_info in ports:
            port_name = port_info.device
            for baudrate in sorted(cls.VALID_BAUD_RATES):
                try:
                    with cls(port=port_name, baudrate=baudrate, timeout=1.0) as proj:
                        # Use a command that triggers a known response from acer projectors even if in standby
                        response = proj.send_command(ProjectorQuery.LAMP_STATE) 
                        if response in LampState:
                            info = ProjectorInfo(
                                name=port_name,
                                projector_cls=cls,
                                kwargs={"port": port_name, "baudrate": baudrate}
                            )
                            available_projectors.append(info)
                            break
                            
                except Exception as e:
                    logger.warning("Port %s baud %s failed: %s", port_name, baudrate, e)
                
        return available_projectors

    def send_command(self, command):
        
        if not self.connection or not self.connection.is_open:
            print("Serial connection is not open.")
            return None

        try:
            self.connection.read_all() # clear the line
            self.connection.write(command.encode("ascii"))
            time.sleep(self.RESPONSE_WAIT_SECONDS)
            response = self.connection.read_all().decode("ascii", errors="ignore")
            if self.verbose:
                print(f"Response: {repr(response)}")

            return response

        except Exception as e:
            print(f"Failed to execute command: {e}")
            return None

    def power_on(self) -> None:
        self.send_command(System.POWER_ON)
        time.sleep(self.POWER_ON_WAIT_SECONDS) 

    def power_off(self):
        self.send_command(System.POWER_OFF)
        time.sleep(self.POWER_OFF_WAIT_SECONDS) 

    def scan(self, start_len: int = 3, end_len: int = 5) -> Dict[str, str]:
        # try to lower RESPONSE_WAIT_SECONDS to 0.05 or lower
        discovered_commands = {}
        letters = string.ascii_uppercase

        for length in range(start_len, end_len + 1):
            print(f"Scanning length {length}...")
            for chars in itertools.product(letters, repeat=length):
                keyword = "".join(chars)
                command = f"* 0 {keyword} ?\r"
                print(command)
                response = self.send_command(command)
                
                if response:
                    print(f"FOUND MATCH: [{keyword}] -> {repr(response)}")
                    discovered_commands[command] = response
                        
        return discovered_commands
    
if __name__ == "__main__":

    with AcerProjector(port="/dev/ttyUSB0", baudrate=19200) as projector:
        print(projector.send_command(ProjectorQuery.LAMP_STATE))
        #projector.power_on()