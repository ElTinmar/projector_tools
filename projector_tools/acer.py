import time
import serial


class AcerProjector:

    def __init__(
        self,
        port="/dev/ttyUSB0",
        baudrate=19200,  # Optimized for Acer P1320W
        bytesize=serial.EIGHTBITS,  # 8 Data Bits
        parity=serial.PARITY_NONE,  # No Parity
        stopbits=serial.STOPBITS_ONE,  # 1 Stop Bit
        xonxoff=False,  # Disable Software Flow Control
        rtscts=False,  # Disable Hardware Flow Control (RTS/CTS)
        dsrdtr=False,  # Disable Hardware Flow Control (DSR/DTR)
        timeout=1,  # 1-second read timeout
    ):
        """Initializes all relevant RS232 serial connection parameters explicitly."""
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        self.dsrdtr = dsrdtr
        self.timeout = timeout

        self.connection = None

    def connect(self):
        """Opens the serial port using the fully configured parameter set."""
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
            print(f"Successfully opened {self.port} with explicit parameters:")
            print(
                f" -> {self.baudrate} baud, {self.bytesize} data bits, "
                f"Parity: {self.parity}, Stop Bits: {self.stopbits}"
            )
            print(
                f" -> Flow Control - XON/XOFF: {self.xonxoff}, RTS/CTS: {self.rtscts}, DSR/DTR: {self.dsrdtr}"
            )
        except serial.SerialException as e:
            print(f"Error opening serial port {self.port}: {e}")
            self.connection = None
            
    def send_command(self, command):
        """Sends a command to the projector and returns the response."""
        if not self.connection or not self.connection.is_open:
            print("Serial connection is not open.")
            return None

        # Acer commands usually end with a Carriage Return (\r)
        full_command = f"{command}\r"

        try:
            # Clear buffers
            self.connection.reset_input_buffer()
            self.connection.reset_output_buffer()

            # Send the command encoded as ASCII bytes
            print(f"Sending: {repr(full_command)}")
            self.connection.write(full_command.encode("ascii"))

            # Give the projector a moment to process and respond
            time.sleep(0.1)

            # Read the response (Acer usually echoes back or replies with 'OK')
            response = self.connection.read_all().decode("ascii", errors="ignore")
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
            print("Serial connection closed.")


# --- Example Usage ---
if __name__ == "__main__":
    # Adjust '/dev/ttyUSB0' to match your actual device path
    projector = AcerProjector(port="/dev/ttyUSB0", baudrate=9600)

    projector.connect()

    if projector.connection:
        # Example: Powering on the projector
        projector.power_on()

        # Keep the connection alive or close it depending on your automation script
        projector.close()