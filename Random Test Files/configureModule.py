import serial 
from pyubx2 import UBXReader, UBXMessage

port = '/dev/ttyAMA0'
baudrate = 38400
new_baudrate = 115200

## https://github.com/semuconsulting/pyubx2/issues/169

msg = [
	# ('CFG_UART1OUTPROT_UBX', 1),
	# ('CFG_UART1OUTPROT_NMEA', 0),
	# ('CFG_UART2OUTPROT_NMEA', 1),
	# ('CFG_MSGOUT_UBX_NAV_POSECEF_UART1', 1),
	# ('CFG_MSGOUT_UBX_NAV_POSLLH_UART1', 1),
	# ('CFG_MSGOUT_UBX_RXM_SFRBX_UART1', 1),
	# ('CFG_MSGOUT_UBX_RXM_RAWX_UART1', 1),
	('CFG_RATE_MEAS', 1000),
	# ('CFG_MSGOUT_NMEA_ID_GGA_UART2', 1),
	# ('CFG_MSGOUT_NMEA_ID_GSV_UART2', 1),
	# ('CFG_MSGOUT_NMEA_ID_GSA_UART2', 1),
	# ('CFG_MSGOUT_NMEA_ID_GST_UART2', 1),
	# ('CFG_MSGOUT_NMEA_ID_GNS_UART2', 1),
	# ('CFG_MSGOUT_NMEA_ID_ZDA_UART2', 1)
]

ser = serial.Serial(port, baudrate, timeout = 1)

msg_baud = UBXMessage.config_set(1, 0, [('CFG_UART1_BAUDRATE', new_baudrate)])

ser.write(msg_baud.serialize())

ser.close()

ser = serial.Serial(port, new_baudrate, timeout = 1)

msg_cfg = UBXMessage.config_set(1, 0, msg)

print(msg_cfg)

ser.write(msg_cfg.serialize())

reader = UBXReader(ser)

while True:
	raw_data, parsed_data = reader.read()
	print(raw_data)
	print(parsed_data)