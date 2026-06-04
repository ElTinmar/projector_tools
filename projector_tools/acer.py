import time
import serial


class AcerProjector:

    def __init__(
        self,
        port="/dev/ttyUSB0",
        baudrate=19200,  
        bytesize=serial.EIGHTBITS,  # 8 Data Bits
        parity=serial.PARITY_NONE,  # No Parity
        stopbits=serial.STOPBITS_ONE,  # 1 Stop Bit
        xonxoff=False,  # Disable Software Flow Control
        rtscts=False,  # Disable Hardware Flow Control (RTS/CTS)
        dsrdtr=False,  # Disable Hardware Flow Control (DSR/DTR)
        timeout=1,  # 1-second read timeout
        verbose: bool = False,
    ):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        self.dsrdtr = dsrdtr
        self.timeout = timeout
        self.verbose = verbose

        self.connection = None

    def connect(self):
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                xonxoff=self.xonxoff,
                rtscts=self.rtscts,
                dsrdtr=self.dsrdtr,
                timeout=self.timeout,
            )
        except serial.SerialException as e:
            print(f"Error opening serial port {self.port}: {e}")
            self.connection = None
            
    def send_command(self, command):
        
        if not self.connection or not self.connection.is_open:
            print("Serial connection is not open.")
            return None

        # Acer commands usually end with a Carriage Return (\r)
        full_command = f"{command}\r"

        try:
            # Clear buffers
            self.connection.reset_input_buffer()
            self.connection.reset_output_buffer()

            print(f"Sending: {repr(full_command)}")
            self.connection.write(full_command.encode("ascii"))

            time.sleep(0.1)

            response = self.connection.read_all().decode("ascii", errors="ignore")
            if self.verbose:
                print(f"Response: {repr(response)}")

            return response

        except Exception as e:
            print(f"Failed to execute command: {e}")
            return None

    def power_on(self):
        """Turns the projector on."""
        return self.send_command("* 0 IR 001")

    def power_off(self):
        """Turns the projector off."""
        return self.send_command("* 0 IR 002")

    def close(self):
        """Closes the serial connection."""
        if self.connection and self.connection.is_open:
            self.connection.close()


if __name__ == "__main__":

    projector = AcerProjector(port="/dev/ttyUSB0")
    projector.connect()
    if projector.connection:
        projector.power_on()
        projector.close()