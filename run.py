import datetime
import sys
from layer import MessageResponseLayer, MyNetworkLayer
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

if __name__==  "__main__":

    if len(sys.argv) > 1 and 'debug' in sys.argv[1].lower():
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(filename='log-{}.log'.format(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")),level=logging.DEBUG)
    layers = (
        MessageResponseLayer,
        (YowAuthenticationProtocolLayer, YowMessagesProtocolLayer, YowReceiptProtocolLayer,
         YowAckProtocolLayer, YowMediaProtocolLayer, YowIqProtocolLayer, YowCallsProtocolLayer,
         YowGroupsProtocolLayer,),
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
        except AuthError as e:
            print("AuthError")
            break
        # except Exception as e:
        #     print("Other Error")
        #     time.sleep(10)