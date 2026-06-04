import serial
import time
from typing import Optional, Dict, Callable
import os
import json
from .projector import (
    SerialProjector,
    TransmissionError,
    FunctionDisabled,
    ProjectorOFF,
    ConnectionFailed,
    CommandFailed,
    BytesEnum
)

# TODO add delay to functions that require delays

EMPTY = b'\x00'
SCANFILE = 'scan.json'
POWER_ON_WAIT_SECONDS = 30
POWER_OFF_WAIT_SECONDS = 20
UPDATE_WAIT_SECONDS = 5


    
def int_to_two_bytes(i: int) -> bytes:
    if i >= 0:
        b = bytes([i, 0x00])
    else:
        b = bytes([i + 256, 0xFF])
    return b

def two_bytes_to_int(b: bytes) -> int:
    if b[-1] == 0:
        i = b[0]
    elif b[-1] == 255:
        i = b[0] - 256
    else:
        raise ValueError('Invalid format')
    return i

def one_byte_to_int(b: bytes) -> int:
    return b[0]

class HEADER:
    '''
    5-bytes headers for read/write queries and device responses.
    I added part of the command payload to the headers when it never changes.
    '''
    NUM_BYTES = 5
    WRITE_ONE_BYTE = b'\x06\x14\x00\x04\x00' + b'\x34'
    WRITE_TWO_BYTE = b'\x06\x14\x00\x05\x00' + b'\x34'
    READ = b'\x07\x14\x00\x05\x00' + b'\x34\x00\x00'
    READ_RESPONSE_ONE_BYTE = b'\x05\x14\x00\x03\x00' + b'\x00\x00'
    READ_RESPONSE_TWO_BYTE = b'\x05\x14\x00\x04\x00' + b'\x00\x00'
    ACK = b'\x03\x14\x00\x00\x00' + b'\x14'
    DISABLED = b'\x00\x14\x00\x00\x00' + b'\x14'
    PROJ_OFF = b'\x00\x00\x00\x00\x00' + b'\x00'

class CMD(BytesEnum):
    REMOTE_KEY = b'\x02\x04'

    GAMMA = b'\x05\xca'
    
    # X = b'\x0c\x00'
    # X = b'\x0c\x01'
    # X = b'\x0c\x03'
    # X = b'\x0c\x04'
    RESET_TO_FACTORY_DEFAULT = b'\x0c\x08'
    SERIAL_NUMBER = b'\x0c\x09' 
    PROJECTOR_MODEL = b'\x0c\x0a'
    # X = b'\x0c\x0c'
    ERROR_STATUS =  b'\x0c\x0d'
    UNKNOWN_STATUS_INFO = b'\x0c\x0f' # changes with time, contains 8 bytes of info, maybe a timer/counter or something 
    # X = b'\x0c\x11'
    # X = b'\x0c\x21'
    # X = b'\x0c\x23'
    # X = b'\x0c\x2f'
    # X = b'\x0c\x31'
    AUTO_V_KEYSTONE = b'\x0c\x34'
    # X = b'\x0c\x35'
    REMOTE_CONTROL_CODE = b'\x0c\x48'
    AUTO_POWER_OFF = b'\x0c\x4c'
    # X = b'\x0c\x4f'
    # X = b'\x0c\x50'
    # X = b'\x0c\x51'
    SILENCE_MODE = b'\x0c\x53'
    FAST_INPUT_MODE = b'\x0c\x54' 
    # X = b'\x0c\x60'
    # X = b'\x0c\x8e'
    # X = b'\x0c\x9d'
    # X = b'\x0c\xa7'
    # X = b'\x0c\xaa'
    # X = b'\x0c\xaf'
    # X = b'\x0c\xd7'
    # X = b'\x0c\xd9'

    POWER_ON = b'\x11\x00'
    POWER_OFF = b'\x11\x01'
    RESET_ALL_SETTINGS = b'\x11\x02'
    SPLASH_SCREEN = b'\x11\x0a'
    QUICK_POWEROFF = b'\x11\x0b'
    HIGH_ALTITUDE_MODE = b'\x11\x0c'
    LIGHT_SOURCE_MODE = b'\x11\x10'
    # X = b'\x11\x1a'
    # X = b'\x11\x1c'
    PROJECTOR_STATUS = b'\x11\x26'
    MESSAGE = b'\x11\x27'
    HDMI_FORMAT = b'\x11\x28'
    HDMI_RANGE = b'\x11\x29'
    RESET_COLOR_SETTINGS = b'\x11\x2a'
    CEC = b'\x11\x2b'
    EOTF = b'\x11\x2c'
    FRAME_INTERPOLATION = b'\x11\x2d'
    KEYSTONE_HORIZONTAL = b'\x11\x31'
    SCREEN_COLOR = b'\x11\x32'
    OVER_SCAN = b'\x11\x33'
    PROJ_360 = b'\x11\x36'
    LENS_FOCUS = b'\x11\x37'
    DIGITAL_LENS_SHIFT_VERTICAL = b'\x11\x39'
    DIGITAL_LENS_SHIFT_HORIZONTAL = b'\x11\x3a'

    PROJECTOR_POSITION = b'\x12\x00'
    CONTRAST =  b'\x12\x02'
    BRIGHTNESS =  b'\x12\x03'
    ASPECT_RATIO =  b'\x12\x04'
    AUTO_ADJUST =  b'\x12\x05'
    HORIZONTAL_POSITION =  b'\x12\x06'
    VERTICAL_POSITION =  b'\x12\x07'
    COLOR_TEMPERATURE =  b'\x12\x08'
    BLANK = b'\x12\x09'
    KEYSTONE_VERTICAL = b'\x12\x0a'
    COLOR_MODE = b'\x12\x0b'
    SHARPNESS = b'\x12\x0e'
    BRILLIANT_COLOR = b'\x12\x0f'
    PRIMARY_COLOR = b'\x12\x10'
    HUE_TINT = b'\x12\x11'
    SATURATION = b'\x12\x12'
    GAIN = b'\x12\x13'
    ZOOM = b'\x12\x16'
    # X = b'\x12\x17'
    # X = b'\x12\x18'
    PROJECTOR_3D_SYNC =  b'\x12\x20'
    PROJECTOR_3D_SYNC_INVERT = b'\x12\x21'
    # X = b'\x12\x30'
    # X = b'\x12\x31'
    # X = b'\x12\x32'
    COLOR_MODE_CYCLE = b'\x13\x33'
    ISF_MODE = b'\x12\x38'
    HDR = b'\x12\x39'
    COLOR_TEMPERATURE_RED_GAIN_ADJUST = b'\x12\x3a\x00' 
    COLOR_TEMPERATURE_GREEN_GAIN_ADJUST = b'\x12\x3a\x01'
    COLOR_TEMPERATURE_BLUE_GAIN_ADJUST = b'\x12\x3a\x02'
    COLOR_TEMPERATURE_RED_GAIN = b'\x12\x3b'
    COLOR_TEMPERATURE_GREEN_GAIN = b'\x12\x3c'
    COLOR_TEMPERATURE_BLUE_GAIN = b'\x12\x3d'
    COLOR_TEMPERATURE_RED_OFFSET_ADJUST = b'\x12\x3e\x00' 
    COLOR_TEMPERATURE_GREEN_OFFSET_ADJUST = b'\x12\x3e\x01' 
    COLOR_TEMPERATURE_BLUE_OFFSET_ADJUST = b'\x12\x3e\x02' 
    COLOR_TEMPERATURE_RED_OFFSET = b'\x12\x3f'
    COLOR_TEMPERATURE_GREEN_OFFSET = b'\x12\x40'
    COLOR_TEMPERATURE_BLUE_OFFSET = b'\x12\x41'
    WARPING_ENABLE = b'\x12\x50'
    WARPING_CONTROL_MODE = b'\x12\x51'

    FREEZE =  b'\x13\x00'
    SOURCE_INPUT = b'\x13\x01'
    QUICK_AUTO_SEARCH = b'\x13\x02'
    ASPECT_RATIO_CYCLE =  b'\x13\x31'
    AUDIO_MODE_CYCLE = b'\x13\x35'
    LAMP_MODE_CYCLE = b'\x13\x36'
    SET_VOLUME_LEVEL = b'\x13\x2a'

    MUTE = b'\x14\x00'
    VOLUME_UP = b'\x14\x01'
    VOLUME_DOWN = b'\x14\x02'
    VOLUME = b'\x14\x03' # check that 
    AUDIO_MODE = b'\x14\x05'

    LANGUAGE = b'\x15\x00'
    LIGHT_SOURCE_USAGE_TIME = b'\x15\x01'
    OPERATING_TEMPERATURE = b'\x15\x03'
    # X = b'\x15\x0a'
    # X = b'\x15\x42' # changed with aspect_ratio, fast input mode, warping enable, auto_v_keystone -> opposite CORNER_ADJ OR KEYSTONE ?
    FIRMWARE_VERSION = b'\x15\x43' # V1.03B maybe firmware version
    # X = b'\x15\x44'
    # X = b'\x15\x45'
    # X = b'\x15\x49'

    # X = b'\x16\x01'
    # X = b'\x16\x40'
    # X = b'\x16\x41' ALSO PROJECTOR MODEL IN ASCII?
    # X = b'\x16\x8a'
    # X = b'\x16\x8b'
    # X = b'\x16\x8c' 
    # X = b'\x16\x8d' 
    # X = b'\x16\x8e'
    DIRECT_POWER_ON = b'\x16\x8f' #Allows the projector to turn on automatically once power is fed through the power cord.
    # X = b'\x16\x99'
    # X = b'\x16\xa3'
    # X = b'\x16\xa4'

    # X = b'\x40\x87'
    # X = b'\x40\x89'

class AutoPowerOff(BytesEnum):
    DISABLE = b'\x00'
    THIRTY_MIN = b'\x03'
    TWENTY_MIN = b'\x02'
    TEN_MIN = b'\x01'

class WarpingControlMode(BytesEnum):
    OSD = b'\x00'
    RS232 = b'\x01'

class Gamma(BytesEnum):
    GAMMA_1_8 = b'\x00'
    GAMMA_2 = b'\x01'
    GAMMA_2_2 = b'\x02'
    GAMMA_2_35 = b'\x03'
    GAMMA_2_5 = b'\x04'
    GAMMA_sRGB = b'\x05'
    GAMMA_Cubic = b'\x06'

class AudioMode(BytesEnum):
    MOVIE = b'\x04'
    MUSIC = b'\x05'
    USER = b'\x06'
    SPEECH = b'\x01'

class PowerStatus(BytesEnum):
    '''
    Power On: System is finished all HW/FW settings and ready to work.
    Warm Up: System is at initial stage to set and check HW/FW environment. Please do not perform other commands.
    Cool Down: System is at final stage to close HW/FW environment. Please do not perform other commands.
    Power Off: System is turned off all HW/FW except MCU or LAN functions with LAN standy setting.
    '''
    WARM_UP = b'\x02'
    COOL_DOWN = b'\x03'
    ON = b'\x01'
    OFF = b'\x00'

    def __bool__(self):
        return True if self.value == b'\x01' else False

class RemoteKey(BytesEnum):
    GUIDE = b'\x0b'
    MENU = b'\x0f'
    CANCEL = b'\x13'
    UP 	= b'\x0b'
    DOWN = b'\x0c'
    LEFT = b'\x0d'
    RIGHT = b'\x0e'
    ENTER = b'\x15'

class Bool(BytesEnum):
    OFF = b'\x00'
    ON = b'\x01'

    def __bool__(self):
        return True if self.value == b'\x01' else False

class Adjustment(BytesEnum):
    DECREASE = b'\x00'
    INCREASE = b'\x01'
   
class SplashScreen(BytesEnum):
    BLACK = b'\x00'
    BLUE = b'\x01'
    VIEWSONIC = b'\x02'
    SCREENCAPTURE = b'\x03'
    OFF = b'\x04'

class LightSourceMode(BytesEnum):
    NORMAL = b'\x00'
    ECO = b'\x01'
    DYNAMIC_ECO = b'\x02'
    SUPER_ECO = b'\x03'
    DYNAMIC_BLACK_1 = b'\x09'
    DYNAMIC_BLACK_2 = b'\x0a'
    CUSTOM = b'\x06'

class ProjectorPosition(BytesEnum):
    FRONT_TABLE = b'\x00'
    REAR_TABLE = b'\x01'
    FRONT_CEILING = b'\x02'
    REAR_CEILING = b'\x03'

class Projector3DSync(BytesEnum):
    PROJECTOR_3D_SYNC_OFF =  b'\x00'
    PROJECTOR_3D_SYNC_AUTO =  b'\x01'
    PROJECTOR_3D_SYNC_FRAME_SEQUENTIAL =  b'\x02'
    PROJECTOR_3D_SYNC_FRAME_PACKING =  b'\x03'
    PROJECTOR_3D_SYNC_TOP_BOTTOM =  b'\x04'
    PROJECTOR_3D_SYNC_SIDE_BY_SIDE =  b'\x05'

class AspectRatio(BytesEnum):
    AR_AUTO = b'\x00'
    AR_4_TO_3 = b'\x02'
    AR_16_TO_9 = b'\x03'
    AR_16_TO_10 = b'\x04'
    AR_ANAMORPHIC = b'\x05'
    AR_WIDE = b'\x06'
    AR_2_35_TO_1 = b'\x07'
    AR_PANORAMA = b'\x08'
    AR_NATIVE = b'\x09'

class Zoom(BytesEnum):
    X_0_8 = int_to_two_bytes(-20)
    X_0_85 = int_to_two_bytes(-15)
    X_0_9 = int_to_two_bytes(-10)
    X_0_95 = int_to_two_bytes(-5)
    X_1_0 = int_to_two_bytes(0)
    X_1_1 = int_to_two_bytes(10)
    X_1_2 = int_to_two_bytes(20)
    X_1_3 = int_to_two_bytes(30)
    X_1_4 = int_to_two_bytes(40)
    X_1_5 = int_to_two_bytes(50)
    X_1_6 = int_to_two_bytes(60)
    X_1_7 = int_to_two_bytes(70)
    X_1_8 = int_to_two_bytes(90)
    X_1_9 = int_to_two_bytes(90)
    X_2_0 = int_to_two_bytes(100)

# TODO
class CornerAdjust(BytesEnum):
    TOP_RIGHT = b''
    TOP_LEFT = b''
    BOTTOM_RIGHT = b''
    BOTTOM_LEFT = b''

# TODO
class PowerOnSource(BytesEnum):
    DISABLE = b''
    HDMI_1 = b''
    HDMI_2 = b''
    USB_C = b''

class ColorTemperature(BytesEnum):
    WARM = b'\x00'
    NORMAL_6500K = b'\x01'
    NEUTRAL_7500K = b'\x02'
    COOL = b'\x03'
    VERY_COOL_9300K = b'\x04'

class ColorMode(BytesEnum):
    BRIGHTEST = b'\x00'
    MOVIE = b'\x01'
    STANDARD = b'\x04'
    sRGB = b'\x05'
    DYNAMIC = b'\x08'
    Rec709 = b'\x09'
    DICOM_SIM = b'\x0a'
    SPORTS = b'\x11'
    PHOTO = b'\x13'
    PRESENTATION = b'\x14'
    GAMING = b'\x12'
    VIVID = b'\x15'
    ISF_DAY = b'\x16'
    ISF_NIGHT = b'\x17'
    USER = b'\x18'
    LOW_BLUE_LIGHT = b'\x1c'
    TV = b'\x1a'

class HDR(BytesEnum):
    AUTO = b'\x00'
    SDR = b'\x01'

class PrimaryColor(BytesEnum):
    R = b'\x00'
    G = b'\x01'
    B = b'\x02'
    C = b'\x03'
    M = b'\x04'
    Y = b'\x05'

class SourceInput(BytesEnum):
    NONE = b'\x10'
    D_SUB_COMP_1 = b'\x00'
    D_SUB_COMP_2 = b'\x08'
    HDMI_1 = b'\x03'
    HDMI_2 = b'\x07'
    HDMI_3 = b'\x09'
    HDMI_MHL_4 = b'\x0e'
    COMPOSITE = b'\x05'
    S_VIDEO = b'\x06'
    DVI = b'\x0a'
    COMPONENT = b'\x0b'
    HDBaseT = b'\x0c'
    USB_C = b'\x0f'
    USB_Reader = b'\x1a'
    LAN_WIFI_Display = b'\x1b'
    USB_Display = b'\x1c'

class Language(BytesEnum):
    ENGLISH = b'\x00'
    FRENCH = b'\x01'
    GERMAN = b'\x02'
    ITALIAN = b'\x03'
    SPANISH = b'\x04'
    RUSSIAN = b'\x05'
    CHINESE = b'\x06'
    SIMPLIFIED_CHINESE = b'\x07'
    JAPANESE = b'\x08'
    KOREAN = b'\x09'
    SWEDISH = b'\x0a'
    DUTCH = b'\x0b'
    TURKISH = b'\x0c'
    CZECH = b'\x0d'
    PORTUGESE = b'\x0e'
    THAI = b'\x0f'
    POLISH = b'\x10'
    FINNISH = b'\x11'
    ARABIC = b'\x12'
    INDONESIAN = b'\x13'
    HINDI = b'\x14'
    VIETNAMESE = b'\x15'

class HDMIFormat(BytesEnum):
    RGB = b'\x00'
    YUV = b'\x01'
    AUTO = b'\x02'

class HDMIRange(BytesEnum):
    ENHANCED = b'\x00'
    NORMAL = b'\x01'
    AUTO = b'\x02'

class BrilliantColor(BytesEnum):
    COLOR_01 = b'\x01'
    COLOR_02 = b'\x02'
    COLOR_03 = b'\x03'
    COLOR_04 = b'\x04'
    COLOR_05 = b'\x05'
    COLOR_06 = b'\x06'
    COLOR_07 = b'\x07'
    COLOR_08 = b'\x08'
    COLOR_09 = b'\x09'
    COLOR_10 = b'\x0a'

class RemoteControlCode(BytesEnum):
    CODE_01 = b'\x00'
    CODE_02 = b'\x01'
    CODE_03 = b'\x02'
    CODE_04 = b'\x03'
    CODE_05 = b'\x04'
    CODE_06 = b'\x05'
    CODE_07 = b'\x06'
    CODE_08 = b'\x07'

class ScreenColor(BytesEnum):
    OFF = b'\x00'
    BLACKBOARD = b'\x01'
    GREENBOARD = b'\x02'
    WHITEBOARD = b'\x03'
    BLUEBOARD = b'\x04'

class OverScan(BytesEnum):
    OFF = b'\x00'
    VALUE_01 = b'\x01'
    VALUE_02 = b'\x02'
    VALUE_03 = b'\x03'
    VALUE_04 = b'\x04'  
    VALUE_05 = b'\x05' 

class RemoteKey(BytesEnum):
    MENU = b'\x0f'
    EXIT = b'\x13'
    TOP = b'\x0b'
    BOTTOM = b'\x0c'
    LEFT = b'\x0d'
    RIGHT = b'\x0e'
    SOURCE = b'\x04'
    ENTER = b'\x15'
    AUTO = b'\x08'
    MY_BUTTON = b'\x11'
    BLUETOOTH = b'\x26'
    RETURN = b'\x27'
    NEXT_TRACK = b'\x28'
    PREVIOUS_TRACK = b'\x29'
    PLAY = b'\x2a'
    SUB_MENU = b'\x2b'

def checksum(packet: bytes) -> bytes:
    '''compute checksum as the sum of bytes 1 to end'''
    return (sum(packet[1:]) % 256).to_bytes(length=1, byteorder='big')

def payload_length(header: bytes) -> int:
    '''get payload length from header (data + checksum)'''
    lsb = header[3] 
    msb = header[4]
    ck = 1 # 1-byte checksum at the end
    return lsb + (msb << 8) + ck

def packet_data_to_ascii(response: bytes) -> str:
    data_start = payload_length(response) - 2
    data = response[-data_start:-1]
    return data.decode('ascii').replace('\x00', '')

def set_value_by_increment(
        read_fun: Callable[[], int], 
        increment_fun: Callable[[Adjustment], None], 
        desired_value: int
    ) -> None:

    # get number of steps and sign
    current_value = read_fun()
    steps = desired_value - current_value
    step_type = Adjustment.DECREASE if steps < 0 else Adjustment.INCREASE

    # iterate increments/decrements until value is reached 
    for i in range(abs(steps)):
        increment_fun(step_type)
        time.sleep(0.1) # give the projector some time to process the requests
    
    # check we have the proper value
    final_value = read_fun()
    if final_value != desired_value:
        raise RuntimeError('failed to set value')

class ViewSonicProjector:
    '''
    Requires a crossover (null modem) cable for use with PC
    Only 3 pins need to be connected (RX,TX and GND)
    '''

    VALID_BAUD_RATES = [2400,4800,9600,14400,19200,38400,115200]

    def __init__(
        self,
        port: str = '/dev/ttyUSB0',
        baudrate: int = 115200,
        data_byte_length = serial.EIGHTBITS,
        parity_check = serial.PARITY_NONE,
        num_stop_bit: int = serial.STOPBITS_ONE,
        timeout: Optional[float] = 10.0,
        write_timeout: Optional[float] = 1.0,
        flow_control: bool = False,
        verbose: bool = False
        ):

        if baudrate not in self.VALID_BAUD_RATES:
            raise ValueError(f'Supported baud rates are: {self.VALID_BAUD_RATES}')
        
        self.port = port
        self.baudrate = baudrate
        self.data_byte_length = data_byte_length
        self.parity_check = parity_check
        self.num_stop_bit = num_stop_bit
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.flow_control = flow_control
        self.verbose = verbose
        self.connection = None

        try:
            self.connection = serial.Serial(
                port = port,
                baudrate = baudrate,
                bytesize = data_byte_length,
                parity = parity_check,
                stopbits = num_stop_bit,
                timeout = timeout,
                write_timeout= write_timeout,
                rtscts = flow_control
            )
        except serial.SerialException:
            raise ConnectionFailed

    def __del__(self):
        if self.connection is not None:
            self.connection.close()

    def power_on(self) -> None:
        '''
        Turn the projector on and wait for the projector to warm up.
        No command can be sent while the projector is warming up.
        '''

        self._send_write_one_byte(CMD.POWER_ON + EMPTY)
        
        # leave some time for the projector to turn on
        time.sleep(POWER_ON_WAIT_SECONDS)

        # make sure the projector is warmed up
        while True:
            res = self.get_power_status()
                
            if res in [PowerStatus.OFF, PowerStatus.WARM_UP]:
                time.sleep(UPDATE_WAIT_SECONDS)

            elif res == PowerStatus.ON:
                break

            else:
                raise ValueError

    
    def power_off(self) -> None:
        '''
        Turn the projector off and wait for the projector to cool down.
        No command can be sent while the projector is cooling down.
        '''
        self._send_write_one_byte(CMD.POWER_OFF + EMPTY)

        # leave some time for the projector to turn off
        time.sleep(POWER_OFF_WAIT_SECONDS)

        # Wait until the projector has cooled down
        while True:
            res = self.get_power_status()

            if res in [PowerStatus.ON, PowerStatus.COOL_DOWN]:
                time.sleep(UPDATE_WAIT_SECONDS)

            elif res == PowerStatus.OFF:
                break

            else:
                raise ValueError 
            
    def get_serial_number(self) -> str:
        response = self._send_read(CMD.SERIAL_NUMBER)
        return packet_data_to_ascii(response)
    
    def get_model(self) -> str:
        response = self._send_read(CMD.PROJECTOR_MODEL)
        return packet_data_to_ascii(response)
    
    def get_firmware_version(self) -> str:
        response = self._send_read(CMD.FIRMWARE_VERSION)
        return packet_data_to_ascii(response)
            
    def set_gamma(self, data: Gamma) -> None:
        self._send_write_one_byte(CMD.GAMMA + data)

    def get_gamma(self) -> Gamma:
        return Gamma(self._send_read_one_byte(CMD.GAMMA))

    def set_warping_control_mode(self, data: WarpingControlMode) -> None:
        self._send_write_one_byte(CMD.WARPING_CONTROL_MODE + data)

    def get_warping_control_mode(self) -> WarpingControlMode:
        return WarpingControlMode(self._send_read_one_byte(CMD.WARPING_CONTROL_MODE))
    
    def set_audio_mode(self, data: AudioMode) -> None:
        self._send_write_one_byte(CMD.AUDIO_MODE + data)

    def get_audio_mode(self) -> AudioMode:
        return AudioMode(self._send_read_one_byte(CMD.AUDIO_MODE))
    
    def get_power_status(self) -> PowerStatus:
        return PowerStatus(self._send_read_one_byte(CMD.POWER_ON))
    
    def reset_all_settings(self) -> None:
        self._send_write_one_byte(CMD.RESET_ALL_SETTINGS + EMPTY)

    def reset_color_settings(self) -> None:
        self._send_write_one_byte(CMD.RESET_COLOR_SETTINGS + EMPTY)

    def set_splash_screen(self, data: SplashScreen) -> None:
        self._send_write_one_byte(CMD.SPLASH_SCREEN + data)

    def get_splash_screen(self) -> SplashScreen:
        return SplashScreen(self._send_read_one_byte(CMD.SPLASH_SCREEN))

    def set_quick_poweroff(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.QUICK_POWEROFF + data)

    def get_quick_poweroff(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.QUICK_POWEROFF))

    def set_auto_v_keystone(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.AUTO_V_KEYSTONE + data)

    def get_auto_v_keystone(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.AUTO_V_KEYSTONE))
    
    def set_warping_enable(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.WARPING_ENABLE + data)

    def get_warping_enable(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.WARPING_ENABLE))
    
    def set_fast_input_mode(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.FAST_INPUT_MODE + data)
        time.sleep(UPDATE_WAIT_SECONDS)

    def get_fast_input_mode(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.FAST_INPUT_MODE))
        
    def set_high_altitude_mode(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.HIGH_ALTITUDE_MODE + data)

    def get_high_altitude_mode(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.HIGH_ALTITUDE_MODE))
    
    def set_light_source_mode(self, data: LightSourceMode) -> None:
        self._send_write_one_byte(CMD.LIGHT_SOURCE_MODE + data)

    def get_light_source_mode(self) -> LightSourceMode:
        return LightSourceMode(self._send_read_one_byte(CMD.LIGHT_SOURCE_MODE))
    
    def set_zoom(self, data: Zoom) -> None:
        self._send_write_two_byte(CMD.ZOOM + data)

    def get_zoom(self) -> Zoom:
        return Zoom(self._send_read_two_byte(CMD.ZOOM))
        
    def set_message(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.MESSAGE + data)

    def get_message(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.MESSAGE))

    def set_projector_position(self, data: ProjectorPosition) -> None:
        self._send_write_one_byte(CMD.PROJECTOR_POSITION + data)

    def get_projector_position(self) -> ProjectorPosition:
        return ProjectorPosition(self._send_read_one_byte(CMD.PROJECTOR_POSITION))
    
    def set_projector_3d_sync(self, data: Projector3DSync) -> None:
        self._send_write_one_byte(CMD.PROJECTOR_3D_SYNC + data)

    def get_projector_3d_sync(self) -> Projector3DSync:
        return Projector3DSync(self._send_read_one_byte(CMD.PROJECTOR_3D_SYNC))
    
    def set_projector_3d_sync_invert(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.PROJECTOR_3D_SYNC_INVERT + data)

    def get_projector_3d_sync_invert(self) -> Bool:
        # TODO: problem returns b'\x80'
        return Bool(self._send_read_one_byte(CMD.PROJECTOR_3D_SYNC_INVERT))
    
    def adjust_contrast(self, data: Adjustment) -> None:
        self._send_write_one_byte(CMD.CONTRAST + data)

    def get_contrast(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.CONTRAST))
    
    def set_contrast(self, value: int) -> None:
        set_value_by_increment(self.get_contrast, self.adjust_contrast, value)
 
    def adjust_brightness(self, data: Adjustment) -> None:
        self._send_write_one_byte(CMD.BRIGHTNESS + data)

    def get_brightness(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.BRIGHTNESS))
    
    def set_brightness(self, value: int) -> None:
        set_value_by_increment(self.get_brightness, self.adjust_brightness, value)

    def adjust_color_temperature_red_gain(self, data: Adjustment) -> None:
        self._send_write_two_byte(CMD.COLOR_TEMPERATURE_RED_GAIN_ADJUST + data)

    def get_color_temperature_red_gain(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.COLOR_TEMPERATURE_RED_GAIN))
    
    def set_color_temperature_red_gain(self, value: int) -> None:
        set_value_by_increment(
            self.get_color_temperature_red_gain, 
            self.adjust_color_temperature_red_gain, 
            value
        )

    def adjust_color_temperature_green_gain(self, data: Adjustment) -> None:
        self._send_write_two_byte(CMD.COLOR_TEMPERATURE_GREEN_GAIN_ADJUST + data)

    def get_color_temperature_green_gain(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.COLOR_TEMPERATURE_GREEN_GAIN))

    def set_color_temperature_green_gain(self, value: int):
        set_value_by_increment(
            self.get_color_temperature_green_gain, 
            self.adjust_color_temperature_green_gain, 
            value
        )

    def adjust_color_temperature_blue_gain(self, data: Adjustment) -> None:
        self._send_write_two_byte(CMD.COLOR_TEMPERATURE_BLUE_GAIN_ADJUST + data)

    def get_color_temperature_blue_gain(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.COLOR_TEMPERATURE_BLUE_GAIN))
    
    def set_color_temperature_blue_gain(self, value: int):
        set_value_by_increment(
            self.get_color_temperature_blue_gain, 
            self.adjust_color_temperature_blue_gain, 
            value
        )

    def adjust_color_temperature_red_offset(self, data: Adjustment) -> None:
        self._send_write_two_byte(CMD.COLOR_TEMPERATURE_RED_OFFSET_ADJUST + data)

    def get_color_temperature_red_offset(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.COLOR_TEMPERATURE_RED_OFFSET))

    def set_color_temperature_red_offset(self, value: int) -> None:
        set_value_by_increment(
            self.get_color_temperature_red_offset, 
            self.adjust_color_temperature_red_offset, 
            value
        )

    def adjust_color_temperature_green_offset(self, data: Adjustment) -> None:
        self._send_write_two_byte(CMD.COLOR_TEMPERATURE_GREEN_OFFSET_ADJUST + data)

    def get_color_temperature_green_offset(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.COLOR_TEMPERATURE_GREEN_OFFSET))

    def set_color_temperature_green_offset(self, value: int) -> None:
        set_value_by_increment(
            self.get_color_temperature_green_offset, 
            self.adjust_color_temperature_green_offset, 
            value
        )

    def adjust_color_temperature_blue_offset(self, data: Adjustment) -> None:
        self._send_write_two_byte(CMD.COLOR_TEMPERATURE_BLUE_OFFSET_ADJUST + data)

    def get_color_temperature_blue_offset(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.COLOR_TEMPERATURE_BLUE_OFFSET))

    def set_color_temperature_blue_offset(self, value: int):
        set_value_by_increment(
            self.get_color_temperature_blue_offset, 
            self.adjust_color_temperature_blue_offset, 
            value
        )
    
    def set_aspect_ratio(self, data: AspectRatio):
        self._send_write_one_byte(CMD.ASPECT_RATIO + data)

    def get_aspect_ratio(self) -> AspectRatio:
        return AspectRatio(self._send_read_one_byte(CMD.ASPECT_RATIO))
    
    def cycle_aspect_ratio(self) -> None:
        self._send_write_one_byte(CMD.ASPECT_RATIO_CYCLE + EMPTY)

    def auto_adjust(self) -> None:
        self._send_write_one_byte(CMD.AUTO_ADJUST + EMPTY)

    def adjust_horizontal_position(self, data: Adjustment) -> None:
        # Increase is RIGHT, decrease is LEFT
        self._send_write_one_byte(CMD.HORIZONTAL_POSITION + data)

    def get_horizontal_position(self) -> int:
        return one_byte_to_int(self._send_read_one_byte(CMD.HORIZONTAL_POSITION))
    
    def set_horizontal_position(self, value: int) -> None:
        set_value_by_increment(self.get_horizontal_position, self.adjust_horizontal_position, value)

    def adjust_vertical_position(self, data: Adjustment) -> None:
        # Increase is DOWN, decrease is UP
        self._send_write_one_byte(CMD.VERTICAL_POSITION + data)

    def get_vertical_position(self) -> int:
        return one_byte_to_int(self._send_read_one_byte(CMD.VERTICAL_POSITION))

    def set_vertical_position(self, value: int) -> None:
        set_value_by_increment(self.get_vertical_position, self.adjust_vertical_position, value)

    def set_color_temperature(self, data: ColorTemperature) -> None:
        self._send_write_one_byte(CMD.COLOR_TEMPERATURE + data)

    def get_color_temperature(self) -> ColorTemperature:
        return ColorTemperature(self._send_read_one_byte(CMD.COLOR_TEMPERATURE))

    def set_blank(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.BLANK + data)

    def get_blank(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.BLANK))

    def adjust_vertical_keystone(self, data: Adjustment) -> None:
        self._send_write_one_byte(CMD.KEYSTONE_VERTICAL + data)

    def get_vertical_keystone(self) -> int:
        return one_byte_to_int(self._send_read_one_byte(CMD.KEYSTONE_VERTICAL))
    
    def set_vertical_keystone(self, value: int) -> None:
        set_value_by_increment(self.get_vertical_keystone, self.adjust_vertical_keystone, value)

    def adjust_horizontal_keystone(self, data: Adjustment) -> None:
        self._send_write_one_byte(CMD.KEYSTONE_HORIZONTAL + data)

    def get_horizontal_keystone(self) -> int:
        return one_byte_to_int(self._send_read_one_byte(CMD.KEYSTONE_HORIZONTAL))

    def set_horizontal_keystone(self, value: int) -> None:
        set_value_by_increment(self.get_horizontal_keystone, self.adjust_horizontal_keystone, value)

    def set_color_mode(self, data: ColorMode) -> None:
        self._send_write_one_byte(CMD.COLOR_MODE + data)

    def get_color_mode(self) -> ColorMode:
        return ColorMode(self._send_read_one_byte(CMD.COLOR_MODE))

    def set_auto_power_off(self, data: AutoPowerOff) -> None:
        self._send_write_one_byte(CMD.AUTO_POWER_OFF + data)

    def get_auto_power_off(self) -> AutoPowerOff:
        return AutoPowerOff(self._send_read_one_byte(CMD.AUTO_POWER_OFF))
    
    def cycle_color_mode(self) -> None:
        self._send_write_one_byte(CMD.COLOR_MODE_CYCLE + EMPTY)

    def set_ISF_mode(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.ISF_MODE + data)

    def get_ISF_mode(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.ISF_MODE))

    def set_HDR(self, data: HDR) -> None:
        self._send_write_one_byte(CMD.HDR + data)

    def get_HDR(self) -> HDR:
        return HDR(self._send_read_one_byte(CMD.HDR))

    def set_primary_color(self, data: PrimaryColor) -> None:
        self._send_write_one_byte(CMD.PRIMARY_COLOR + data)

    def get_primary_color(self) -> PrimaryColor:
        # select primary color before you adjust hue/saturation/gain
        return PrimaryColor(self._send_read_one_byte(CMD.PRIMARY_COLOR))

    def adjust_hue(self, data: Adjustment) -> None:
        # set primary color before you adjust hue/saturation/gain  
        # for that color
        self._send_write_one_byte(CMD.HUE_TINT + data)

    def get_hue(self) -> int:
        # set primary color before you adjust hue/saturation/gain  
        # for that color
        return two_bytes_to_int(self._send_read_two_byte(CMD.HUE_TINT))
    
    def set_hue(self, value: int) -> None:
        set_value_by_increment(self.get_hue, self.adjust_hue, value)

    def adjust_saturation(self, data: Adjustment) -> None:
        # set primary color before you adjust hue/saturation/gain  
        # for that color
        self._send_write_one_byte(CMD.SATURATION + data)

    def get_saturation(self) -> int:
        # set primary color before you adjust hue/saturation/gain  
        # for that color
        return two_bytes_to_int(self._send_read_two_byte(CMD.SATURATION))

    def set_saturation(self, value: int) -> None:
        set_value_by_increment(self.get_saturation, self.adjust_saturation, value)

    def adjust_gain(self, data: Adjustment) -> None:
        # set primary color before you adjust hue/saturation/gain  
        # for that color
        self._send_write_one_byte(CMD.GAIN + data)

    def get_gain(self) -> int:
        # set primary color before you adjust hue/saturation/gain  
        # for that color
        return two_bytes_to_int(self._send_read_two_byte(CMD.GAIN))
    
    def set_gain(self, value: int) -> None:
        set_value_by_increment(self.get_gain, self.adjust_gain, value)
    
    def adjust_sharpness(self, data: Adjustment) -> None:
        self._send_write_one_byte(CMD.SHARPNESS + data)

    def get_sharpness(self) -> int:
        return two_bytes_to_int(self._send_read_two_byte(CMD.SHARPNESS))
    
    def set_sharpness(self, value: int) -> None:
        set_value_by_increment(self.get_sharpness, self.adjust_sharpness, value)

    def set_freeze(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.FREEZE + data)

    def get_freeze(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.FREEZE))

    def set_source_input(self, data: SourceInput) -> None:
        self._send_write_one_byte(CMD.SOURCE_INPUT + data)
        time.sleep(UPDATE_WAIT_SECONDS)

    def get_source_input(self) -> SourceInput:
        return SourceInput(self._send_read_one_byte(CMD.SOURCE_INPUT))        

    def set_quick_autosearch(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.QUICK_AUTO_SEARCH + data)

    def get_quick_autosearch(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.QUICK_AUTO_SEARCH))

    def set_mute(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.MUTE + data)

    def get_mute(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.MUTE))

    def set_silence_mode(self, data: Bool) -> None:
        self._send_write_one_byte(CMD.SILENCE_MODE + data)

    def get_silence_mode(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.SILENCE_MODE))
    
    #def set_panel_key_lock(self, data: Bool) -> None:
    #    self._send_write_one_byte(CMD.PANEL_KEY_LOCK + data)

    #def get_panel_key_lock(self) -> Bool:
    #    return Bool(self._send_read_one_byte(CMD.PANEL_KEY_LOCK))
    
    def volume_up(self) -> None:
        self._send_write_one_byte(CMD.VOLUME_UP + EMPTY)

    def volume_down(self) -> None:
        self._send_write_one_byte(CMD.VOLUME_DOWN + EMPTY)

    def adjust_volume(self, data: Adjustment) -> None:
        self.volume_up() if data == Adjustment.INCREASE else self.volume_down()

    def get_volume(self) -> int:
        return one_byte_to_int(self._send_read_one_byte(CMD.VOLUME))
    
    def set_volume(self, value: int) -> None:
        set_value_by_increment(self.get_volume, self.adjust_volume, value)

    def set_language(self, data: Language):
        self._send_write_one_byte(CMD.LANGUAGE + data)

    def get_language(self) -> Language:
        return Language(self._send_read_one_byte(CMD.LANGUAGE))    
        
    def reset_light_source_usage_time(self) -> None:
        self._send_write_one_byte(CMD.LIGHT_SOURCE_USAGE_TIME + EMPTY)

    def get_light_source_usage_time(self) -> int:
        # special case
        response = self._send_read(CMD.LIGHT_SOURCE_USAGE_TIME)
        usage_time = int.from_bytes(response[7:11],byteorder='little')
        return usage_time

    def set_HDMI_format(self, data: HDMIFormat) -> None:
        self._send_write_one_byte(CMD.HDMI_FORMAT + data)

    def get_HDMI_format(self) -> HDMIFormat:
        return HDMIFormat(self._send_read_one_byte(CMD.HDMI_FORMAT))           

    def set_HDMI_range(self, data: HDMIRange) -> None:
        self._send_write_one_byte(CMD.HDMI_RANGE + data)

    def get_HDMI_range(self) -> HDMIRange:
        return HDMIRange(self._send_read_one_byte(CMD.HDMI_RANGE))

    def set_CEC(self, data: Bool):
        self._send_write_one_byte(CMD.CEC + data)

    def get_CEC(self) -> Bool:
        return Bool(self._send_read_one_byte(CMD.CEC))
    
    def get_error_status(self) -> Dict:
        # special case
        response = self._send_read(CMD.ERROR_STATUS)
        error_status = response[7:31]
        err = {}
        err['lamp_fail_count'] = error_status[0]
        err['lamp_lit_error_count'] = error_status[1]
        err['fan1_error_count'] = error_status[2]
        err['fan2_error_count'] = error_status[3]
        err['fan3_error_count'] = error_status[4]
        err['fan4_error_count'] = error_status[5]
        err['diode1_open_error_count'] = error_status[6]
        err['diode2_open_error_count'] = error_status[7]
        err['diode1_short_error_count'] = error_status[8]
        err['diode2_short_error_count'] = error_status[9]
        err['temperature1_error_count'] = error_status[10]
        err['temperature2_error_count'] = error_status[11]
        err['fan_IC1_error_count'] = error_status[12]
        err['color_wheel_error_count'] = error_status[13]
        err['color_wheel_startup_error_count'] = error_status[14]
        err['UART1_error_count'] = error_status[15]
        err['abnormal_powerdown'] = error_status[16]
        err['first_burn_in'] = int.from_bytes(error_status[17:21], byteorder='little')
        err['lamp_status'] = error_status[21]
        err['lamp_error_status'] = error_status[22:24]
        return err
    
    def set_brilliant_color(self, data: BrilliantColor) -> None:
        self._send_write_one_byte(CMD.BRILLIANT_COLOR + data)

    def get_brilliant_color(self) -> BrilliantColor:
        return BrilliantColor(self._send_read_one_byte(CMD.BRILLIANT_COLOR))       

    def set_remote_control_code(self, data: RemoteControlCode) -> None:
        self._send_write_one_byte(CMD.REMOTE_CONTROL_CODE + data)

    def get_remote_control_code(self) -> RemoteControlCode:
        return RemoteControlCode(self._send_read_one_byte(CMD.REMOTE_CONTROL_CODE))       

    def set_screen_color(self, data: ScreenColor) -> None:
        self._send_write_one_byte(CMD.SCREEN_COLOR + data)

    def get_screen_color(self) -> ScreenColor:
        return ScreenColor(self._send_read_one_byte(CMD.SCREEN_COLOR))       

    def set_overscan(self, data: OverScan) -> None:
        self._send_write_one_byte(CMD.OVER_SCAN + data)

    def get_overscan(self) -> OverScan:
        return OverScan(self._send_read_one_byte(CMD.OVER_SCAN))       

    def set_remote_key(self, data: RemoteKey) -> None:
        self._send_write_one_byte(CMD.REMOTE_KEY + data)

    def get_remote_key(self) -> RemoteKey:
        return RemoteKey(self._send_read_one_byte(CMD.REMOTE_KEY))   
    
    def get_operating_temperature(self) -> float:
        # special case
        response = self._send_read(CMD.OPERATING_TEMPERATURE)
        temperature = int.from_bytes(response[7:11],byteorder='little')/10
        return temperature

    def cycle_lamp_mode(self) -> None:
        self._send_write_one_byte(CMD.LAMP_MODE_CYCLE + EMPTY)

    def cycle_audio_mode(self) -> None:
        self._send_write_one_byte(CMD.AUDIO_MODE_CYCLE + EMPTY)

    def is_responsive(self) -> bool:
        try:
            _ = self.get_power_status()
            return True
        except TransmissionError:
            return False

    def recover_serial(self) -> None:
        """Try to recover from a bad serial state."""
        try:
            self.connection.close()
        except Exception:
            pass
        time.sleep(1)
        try:
            self.connection.open()
            print("Serial port reopened successfully.")
        except Exception as e:
            print(f"Failed to recover serial: {e}")
        
    def _send_packet(self, packet: bytes) -> bytes:

        self.connection.read_all()

        query = packet + checksum(packet)

        if self.verbose:
            print('>> ' + query.hex(' '))

        self.connection.write(query)

        response_header = self.connection.read(HEADER.NUM_BYTES)
        
        if len(response_header) != HEADER.NUM_BYTES:
            raise TransmissionError('failed to read response header')
        
        payload_num_bytes = payload_length(response_header)
        response_payload = self.connection.read(payload_num_bytes)

        if len(response_payload) != payload_num_bytes:
            raise TransmissionError('payload size mismatch')

        response = response_header + response_payload

        if self.verbose:
            print(response.hex(' '))
            print()
        
        if checksum(response[:-1]) != response[-1:]:
            raise TransmissionError('invalid checksum')

        if response == HEADER.DISABLED:
            raise FunctionDisabled
        
        if response == HEADER.PROJ_OFF:
            raise ProjectorOFF

        return response

    def _send_write_one_byte(self, packet: bytes):

        response = self._send_packet(HEADER.WRITE_ONE_BYTE + packet)

        if response != HEADER.ACK:
            raise CommandFailed

    def _send_write_two_byte(self, packet: bytes):

        response = self._send_packet(HEADER.WRITE_TWO_BYTE + packet)

        if response != HEADER.ACK:
            raise CommandFailed
        
    def _send_read(self, packet: bytes) -> bytes:

        response = self._send_packet(HEADER.READ + packet)
        return response

    def _send_read_one_byte(self, packet: bytes) -> bytes:

        response = self._send_read(packet) 
        data = response[-2:-1]      
        return data
    
    def _send_read_two_byte(self, packet: bytes) -> bytes:

        response = self._send_read(packet)
        data = response[-3:-1]
        return data

def scan(proj: ViewSonicProjector) -> Dict:

    res = {}

    if os.path.exists(SCANFILE):

        print('scan file found, loading commands')

        with open(SCANFILE,'r') as f:
            commands = json.load(f)

        for hex in commands.keys():
            
            if hex in [CMD.OPERATING_TEMPERATURE.hex(' '), CMD.UNKNOWN_STATUS_INFO.hex(' ')]:
                continue

            cmd = bytes.fromhex(hex)
            try:
                response = proj._send_read(cmd)
                res[cmd.hex(' ')] = response.hex(' ')
            except FunctionDisabled:
                pass

    else:

        print('scan file not found, performing an exhaustive scan')

        for cmd2 in range(256): 
            for cmd3 in range(256):
                cmd = bytes([cmd2, cmd3])
                try:
                    response = proj._send_read(cmd)
                    res[cmd.hex(' ')] = response.hex(' ')
                except FunctionDisabled:
                    pass
        
        with open(SCANFILE,'w') as f:
            commands = json.dump(res,f)
        
    return res    

def reverse_engineer(proj: ViewSonicProjector):
    '''reverse engineer command codes
       - exhaustive scan of cmd2/cmd3 space using read query (should be safe)
       - modify setting with projector OSD
       - exhaustive scan of cmd2/cmd3 space using read query
       - check which values have changed (hopefully only one, but some OSD settings might alter several registers at once)
    '''

    scan1 = scan(proj)
    input('Change function on the projector using OSD. Press Enter when done')
    scan2 = scan(proj)
    diff = set(scan1.items()) ^ set(scan2.items()) 
    return diff
    
def set_fast_mode(proj: ViewSonicProjector) -> None:
    # somehow this seems to be a bit unreliable
    
    if proj.get_power_status() == PowerStatus.OFF:
        proj.power_on()
        
    proj.reset_all_settings()
    proj.set_mute(Bool.ON)
    proj.set_source_input(SourceInput.HDMI_1)
    proj.set_fast_input_mode(Bool.ON)
    
    if proj.get_fast_input_mode() == 0:
        raise RuntimeError('failed to set to fast mode')

