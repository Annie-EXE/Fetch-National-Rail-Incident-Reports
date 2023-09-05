import stomp
import zlib
import io
import time
import socket
import logging
import xml.etree.ElementTree as ET

logging.basicConfig(format='%(asctime)s %(levelname)s\t%(message)s', level=logging.INFO)

USERNAME = 'DARWIN5f8f7e41-6462-4b5b-a20f-8d874aefe017'
PASSWORD = '4a61e793-f18c-41d5-b06e-654883d5c190'
HOSTNAME = 'darwin-dist-44ae45.nationalrail.co.uk'
HOSTPORT = 61613
# Always prefixed by /topic/ (it's not a queue, it's a topic)
TOPIC = '/topic/darwin.pushport-v16'

CLIENT_ID = socket.getfqdn()
HEARTBEAT_INTERVAL_MS = 15000
RECONNECT_DELAY_SECS = 15

if USERNAME == '':
    logging.error("Username not set - please configure your username and password in opendata-nationalrail-client.py!")

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
        logging.warning('Disconnected - waiting %s seconds before exiting' % RECONNECT_DELAY_SECS)
        time.sleep(RECONNECT_DELAY_SECS)
        exit(-1)

    def on_connecting(self, host_and_port):
        logging.info('Connecting to ' + host_and_port[0])

    def on_message(self, frame):
        try:
            logging.info('Message sequence=%s, type=%s received', frame.headers['SequenceNumber'],
                        frame.headers['MessageType'])
            msg = zlib.decompress(frame.body, zlib.MAX_WBITS | 32)
            
            # Print the entire XML message
            logging.debug('Raw XML=%s' % msg.decode('utf-8'))
            
            # Parse the XML using ElementTree
            root = ET.fromstring(msg)
            ts = root.find('.//CreationTime').text
            logging.info("%s", ts)
        except Exception as e:
            logging.error(str(e))


conn = stomp.Connection12([(HOSTNAME, HOSTPORT)],
                          auto_decode=False,
                          heartbeats=(HEARTBEAT_INTERVAL_MS, HEARTBEAT_INTERVAL_MS))

conn.set_listener('', StompClient())
connect_and_subscribe(conn)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    conn.disconnect()
