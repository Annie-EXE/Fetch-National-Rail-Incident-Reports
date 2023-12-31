#
# National Rail Open Data client demonstrator
# Copyright (C)2019-2022 OpenTrainTimes Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import stomp
import zlib
import io
import time
import socket
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from extract_incident_data import (
    extract_xml_incident_data,
    convert_timestamp
)

logging.basicConfig(
    format='%(asctime)s %(levelname)s\t%(message)s', level=logging.INFO)

try:
    import PPv16
except ModuleNotFoundError:
    logging.error(
        "Class files not found - please configure the client following steps in README.md!")

USERNAME = 'KBb3ad148f-a9ed-46ca-a37e-b7f6a65aba76'
PASSWORD = '8b998c5a-d74d-4bd5-a6a0-5bfb498a9b08'
HOSTNAME = 'kb-dist-261e4f.nationalrail.co.uk'
HOSTPORT = 61613
# Always prefixed by /topic/ (it's not a queue, it's a topic)
TOPIC = '/topic/kb.incidents'

CLIENT_ID = socket.getfqdn()
HEARTBEAT_INTERVAL_MS = 30000
HEARTBEAT_RESPONSE_TIMEOUT = 25000
RECONNECT_DELAY_SECS = 15

if USERNAME == '':
    logging.error(
        "Username not set - please configure your username and password in opendata-nationalrail-client.py!")


def connect_and_subscribe(connection):
    if stomp.__version__[0] < 5:
        connection.start()

    connect_header = {'client-id': USERNAME + '-' + CLIENT_ID}
    subscribe_header = {'activemq.subscriptionName': CLIENT_ID}

    connection.connect(username=USERNAME,
                       passcode=PASSWORD,
                       wait=True,
                       headers=connect_header)

    connection.subscribe(destination=TOPIC,
                         id='1',
                         ack='auto',
                         headers=subscribe_header)


class StompClient(stomp.ConnectionListener):

    def on_heartbeat(self):
        logging.info('Received a heartbeat')

    def on_heartbeat_timeout(self):
        logging.error('Heartbeat timeout')

    def on_error(self, headers, message):
        logging.error(message)

    def on_disconnected(self):
        logging.warning(
            'Disconnected - waiting %s seconds before exiting' % RECONNECT_DELAY_SECS)
        time.sleep(RECONNECT_DELAY_SECS)
        connect_and_subscribe(self.conn)

    def on_connecting(self, host_and_port):
        logging.info('Connecting to ' + host_and_port[0])

    def on_message(self, frame):
        try:
            print(frame.body.decode())
            message_data = extract_xml_incident_data(frame.body.decode())
            print(message_data)
            # print(frame.body.decode())
            input()
        except Exception as e:
            logging.error(str(e))


conn = stomp.Connection12([(HOSTNAME, HOSTPORT)],
                          auto_decode=False,
                          )

client = StompClient()
client.conn = conn
conn.set_listener('', client)
connect_and_subscribe(conn)

while True:
    time.sleep(1)

conn.disconnect()
