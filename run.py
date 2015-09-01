#!/usr/bin/env python
import datetime
import sys
from time import sleep
from axolotl.duplicatemessagexception import DuplicateMessageException
from layer import MessageResponseLayer, MyNetworkLayer
from yowsup.layers.protocol_chatstate import YowChatstateProtocolLayer
from yowsup.layers.protocol_groups import YowGroupsProtocolLayer
from yowsup.layers.protocol_messages           import YowMessagesProtocolLayer
from yowsup.layers.protocol_receipts           import YowReceiptProtocolLayer
from yowsup.layers.protocol_acks               import YowAckProtocolLayer
from yowsup.layers.network                     import YowNetworkLayer
from yowsup.layers.coder                       import YowCoderLayer
from yowsup.layers.auth                        import YowCryptLayer, YowAuthenticationProtocolLayer, AuthError
from yowsup.layers.coder                       import YowCoderLayer
from yowsup.layers.network                     import YowNetworkLayer
from yowsup.layers.protocol_messages           import YowMessagesProtocolLayer
from yowsup.layers.protocol_media              import YowMediaProtocolLayer
from yowsup.layers.stanzaregulator             import YowStanzaRegulator
from yowsup.layers.protocol_receipts           import YowReceiptProtocolLayer
from yowsup.layers.protocol_contacts           import YowContactsIqProtocolLayer
from yowsup.layers.protocol_acks               import YowAckProtocolLayer
from yowsup.layers.logger                      import YowLoggerLayer
from yowsup.layers.protocol_iq                 import YowIqProtocolLayer
from yowsup.layers.protocol_calls              import YowCallsProtocolLayer
from yowsup.layers.axolotl                     import YowAxolotlLayer
from yowsup.common import YowConstants
from yowsup.layers import YowLayerEvent
from yowsup.stacks import YowStack
from yowsup import env

import logging
# logging.basicConfig(filename='log-{}.log'.format(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")),level=logging.DEBUG)

CREDENTIALS = ("905396815006", "N35sXununbpdtxIKQATBMv8gCrM=") # replace with your phone and password


def start_whatsapp_server():
    layers = (
        MessageResponseLayer,
        (YowAuthenticationProtocolLayer, YowIqProtocolLayer, YowMessagesProtocolLayer, YowReceiptProtocolLayer,
         YowAckProtocolLayer, YowMediaProtocolLayer, YowCallsProtocolLayer, YowChatstateProtocolLayer),
        YowLoggerLayer,
        YowAxolotlLayer,
        YowCoderLayer,
        YowCryptLayer,
        YowStanzaRegulator,
        MyNetworkLayer
        )

    # yowsup/layers/__init__.py line 90 for data
    stack = YowStack(layers)
    stack.setProp(YowAuthenticationProtocolLayer.PROP_CREDENTIALS, CREDENTIALS)         #setting credentials
    stack.setProp(YowNetworkLayer.PROP_ENDPOINT, YowConstants.ENDPOINTS[0])    #whatsapp server address
    stack.setProp(YowCoderLayer.PROP_DOMAIN, YowConstants.DOMAIN)
    stack.setProp(YowCoderLayer.PROP_RESOURCE, env.CURRENT_ENV.getResource())          #info about us as WhatsApp client

    stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))   #sending the connect signal

    while True:
        try:
            stack.loop()
            if stack.getLayer(0).connected == False:
                sleep(5)
                break
        except AuthError as e:
            print("AuthError")
            break
        # except Exception as e:
        #     print("Other Error")

    return True

if __name__==  "__main__":

    if len(sys.argv) > 1 and 'debug' in sys.argv[1].lower():
        logging.basicConfig(level=logging.DEBUG)
    elif len(sys.argv) > 1 and 'info' in sys.argv[1].lower():
        logging.basicConfig(level=logging.INFO)
    elif len(sys.argv) > 1 and 'error' in sys.argv[1].lower():
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(filename='log-{}.log'.format(datetime.datetime.now().strftime("%d-%m-%YT%H:%M:%S%z")),level=logging.DEBUG)

    logger = logging.getLogger(__name__)
    disconnected = True

    while disconnected:
        try:
            disconnected = start_whatsapp_server()
            logger.warning('disconnected, reconnecting now.'+'===='*30)
        except DuplicateMessageException:
            logger.error("{}'".format('Duplicate found'))
            sleep(5)