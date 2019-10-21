def gsr_to_ohm(serial_port_reading, calibration_value=2800):
    """
    Original formula from http://wiki.seeedstudio.com/Grove-GSR_Sensor/:
    Human Resistance = ((1024+2*Serial_Port_Reading)*10000)/(512-Serial_Port_Reading),
    unit is ohm, Serial_Port_Reading is the value display on Serial Port(between 0~1023)

    We have the range 0~4095, and calibration_value != 512.
    Then I think the formula should be the following:
    Human Resistance = ((4096+2*Serial_Port_Reading)*10000)/(calibration_value-Serial_Port_Reading),

    """
    resistance = ((4096 + 2 * serial_port_reading) * 10000) / (calibration_value - serial_port_reading)

    return resistance



