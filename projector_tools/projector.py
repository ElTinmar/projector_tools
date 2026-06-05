from abc import ABC, abstractmethod
import serial
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Type,Tuple,Dict,List,Any

class ProjectorError(Exception): pass
class TransmissionError(ProjectorError): pass
class FunctionDisabled(ProjectorError): pass
class ProjectorOFF(ProjectorError): pass
class ConnectionFailed(ProjectorError): pass
class CommandFailed(ProjectorError): pass

class BytesEnum(bytes, Enum):
    def __str__(self):
        return self.name
    
class StrEnum(str, Enum):
    def __str__(self):
        return self.name
    
@dataclass
class ProjectorInfo:
    name: str            
    projector_cls: Type['Projector'] 
    args: Tuple[Any, ...] = field(default_factory=tuple) 
    kwargs: Dict[str, Any] = field(default_factory=dict) 

    def instantiate(self) -> 'Projector':
        return self.projector_cls(*self.args, **self.kwargs)    
    
class Projector(ABC):

    @classmethod
    @abstractmethod
    def list_available_projectors(cls, *args, **kwargs) -> List[ProjectorInfo]:
        pass

    @abstractmethod
    def connect(self):
        ...

    @abstractmethod
    def disconnect(self):
        ...

    @abstractmethod
    def power_on(self):
        ...

    @abstractmethod
    def power_off(self):
        ...

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

class SerialProjector(Projector):

    VALID_BAUD_RATES = [2400,4800,9600,14400,19200,38400,115200]

    def __init__(
        self,
        port: str = '/dev/ttyUSB0',
        baudrate: int = 115200,
        data_byte_length = serial.EIGHTBITS,
        parity_check = serial.PARITY_NONE,
        num_stop_bit: int = serial.STOPBITS_ONE,
        timeout: float | None = 10.0,
        write_timeout: float | None = 1.0,
        xonxoff: bool = False,  # Disable Software Flow Control
        rtscts: bool = False,  # Disable Hardware Flow Control (RTS/CTS)
        dsrdtr: bool = False,  # Disable Hardware Flow Control (DSR/DTR)
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
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        self.dsrdtr = dsrdtr
        self.verbose = verbose
        self.connection = None
        
    def connect(self):

        if self.connection and self.connection.is_open:
            return 

        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.data_byte_length,
                parity=self.parity_check,
                stopbits=self.num_stop_bit,
                timeout=self.timeout,
                write_timeout=self.write_timeout,
                xonxoff=self.xonxoff,
                rtscts=self.rtscts,
                dsrdtr=self.dsrdtr,
            )

            # clear the line
            self.connection.write(b"\r\r\r")
            time.sleep(0.1)
            self.connection.read_all()

        except serial.SerialException as e:
            raise ConnectionFailed(f"Failed to connect to {self.port}") from e

    def disconnect(self):

        if self.connection and self.connection.is_open:
            self.connection.close()
        self.connection = None

    def power_on(self):
        ...

    def power_off(self):
        ...
    