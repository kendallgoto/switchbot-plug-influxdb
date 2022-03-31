#
# This file is part of switchbot-plug-influxdb (https://github.com/kendallgoto/switchbot-plug-influxdb/).
# Copyright (c) 2022 Kendall Goto.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import asyncio
import json
import struct
from bleak import BleakClient
import time
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from dotenv import load_dotenv
load_dotenv()

measurement=os.getenv("INFLUXDB_MEASUREMENT")
host=os.getenv("INFLUXDB_HOST")
token=os.getenv("INFLUXDB_TOKEN")
org=os.getenv("INFLUXDB_ORG")
bucket=os.getenv("INFLUXDB_BUCKET")
ca=os.getenv("INFLUXDB_CA")


async def writeinflux(plugname, data):
	write_api = influxClient.write_api(write_options=SYNCHRONOUS)
	point = Point(measurement).tag("plug", plugname) \
		.field("voltage", data['voltage']) \
		.field("current", data['current']) \
		.field("wattage", data['wattage']) \
		.field("uptime", data['uptime'])
	write_api.write(bucket=bucket, record=[point])

def unpack(packed):
	# print("{0}".format(packed.hex()))
	return {
		"uptime": struct.unpack_from(">H", packed, 0x7)[0],
		"voltage": struct.unpack_from(">H", packed, 0x9)[0] / 10.0,
		"current": struct.unpack_from(">H", packed, 0xB)[0] / 1000.0,
		"wattage": struct.unpack_from(">H", packed, 0xD)[0] / 10.0
	}

with open('config.json') as f:
	config = json.load(f)

async def connectDevice(device):
	client = BleakClient(device['addr'])
	try:
		loop = asyncio.get_event_loop()
		dataReceived = loop.create_future()
		def collect(sender, data):
			payload = unpack(data)
			loop.call_soon_threadsafe(dataReceived.set_result, payload)
		await client.connect()
		print("connected!")
		await asyncio.wait_for(client.start_notify(config['characteristics']['read'], collect), timeout=10.0)
		currtime = int(time.time())
		packedtime = [x for x in struct.pack(">I", currtime)]

		is_dst = time.daylight and time.localtime().tm_isdst > 0
		utc_offset = - (time.altzone if is_dst else time.timezone)
		starttime = int((time.time()+utc_offset) // 86400) * 86400 - int(utc_offset)
		packedstart = [x for x in struct.pack(">I", starttime)]

		command = [0x57, 0x0f, 0x51, 0x06] + packedtime + packedstart
		# print("".join('{:02x} '.format(x) for x in command))
		await client.write_gatt_char(
			config['characteristics']['write'],
			bytearray(command)
		)
		payload = await asyncio.wait_for(dataReceived, timeout=5.0)
		try:
			print(payload)
			await writeinflux(device['name'], payload)
		except Exception as e:
			print("influx write failed", e)
		print("got data, closing")
		await client.stop_notify(config['characteristics']['read'])
	except asyncio.TimeoutError as e:
		print("timed out", e)
	except Exception as e:
		print(e)
	finally:
		await client.disconnect()

async def main():
	global influxClient
	influxClient = InfluxDBClient(url=host, token=token, org=org, ssl_ca_cert=ca)
	while True:
		for device in config['devices']:
			print("starting {}".format(device['addr']))
			await connectDevice(device)
			print("ended {}".format(device['addr']))
			await asyncio.sleep(0.5)
		print("finished device loop")
	influxClient.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
