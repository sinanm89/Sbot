import random
import asyncore, socket, logging
import datetime
from concurrent.futures import ThreadPoolExecutor
from pymongo import MongoClient
from yowsup.layers import YowProtocolLayer, YowLayer
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_chatstate.protocolentities import OutgoingChatstateProtocolEntity, ChatstateProtocolEntity
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
import time

logger = logging.getLogger(__name__)

mongo_client = MongoClient('localhost', 27017)
message_collection = mongo_client['sbot_db']['received']
message_sent_collection = mongo_client['sbot_db']['sent']

response_choice_list = ["yo", "sup?", "hello", "greetings", "aloha", "komenstnala", "pepelu", "BiBi <3",
                       "Eyvallah bebegim", "Ne oldu?", "Ismim bu", "Sanane", "Banane", "Babandir",
                       "rahatol.com", "WWTDD", "s2trt", "olur oyle hatalar", "chillax", "go",
                       "u wot m8?", "DO IIIIT!", "YESTERDAY YOU SAID TOMORROW", "Thats what she said",
                       "I'm in your phone ;)", "FUCK.", "NPC's Rule!", "sudo rm -rf /*", "I'm at %89",
                       "TIGERS BLOOD", "WINNING!", "DID IT.", "Nuri Alco Protect me.", "WITNESS MEEEEEEE",
                       "PUT CHO FAITH IN THE LIGHT", "Well met.", "Sorry about that.", "Pro Moves",
                       "Smoke weed everyday", "subhaneke", "do yo want to build a snowman?", "LET IT GOOOOOO",
                       "Han shot first.", "YOU MUST CONSTRUCT ADDITIONAL PYLONS", "mo' money mo' poblems",
                       "puddi puddi", "<3", ":3", ":)"]

pls_list = ["ballisi?", "anasi?", "anam?", "cicim?", "kucuk parfem?", "tatlim?", "kuzum?", "yavrum?", "canim?", "soyle",
            "sole.", "suyle", "soyle canisi", "sole ballisi", "sole bebisim", "soyleeeeeee", "yerim seni", "uy", "da"]

class MessageResponseLayer(YowInterfaceLayer):

    message_of_chat = "Motc not set"
    g_mode = False

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        #send receipt otherwise we keep receiving the same message over and over
        data_sent = None
        data_received = None

        # typing...
        self.toLower(OutgoingChatstateProtocolEntity(ChatstateProtocolEntity.STATE_TYPING, messageProtocolEntity.getFrom()))

        recipient = messageProtocolEntity.getFrom()
        if messageProtocolEntity.getType() == 'text':
            text_msg = messageProtocolEntity.getBody()

            data_received = {
                'from': messageProtocolEntity.getFrom(),
                'name': messageProtocolEntity.notify,
                'message' : text_msg,
                'time': datetime.datetime.now(),
            }

            # INSERT DATA RECEIVED
            with ThreadPoolExecutor(max_workers=4) as executor:
                executor.submit(message_collection.insert_one, data_received)
                # print(future.result())

            if '@sbot' in text_msg:
                # import pdb; pdb.set_trace()
                command = text_msg[text_msg.index('@sbot'):]

                if 'help' in command[:11]:
                    text_msg = 'my commands are:\n\t@sbot echo <repeat this back>\t\n@sbot topic\n\t@sbot set topic <your topic here>'
                elif 'pls' in command[:10]:
                    text_msg = str(random.choice(pls_list))
                elif 'topic' in command[:12]:
                    text_msg = self.message_of_chat
                elif 'gaddar' in command[:12]:
                    text_msg = 'Gaddar mode: {}'.format(self.g_mode)
                elif 'echo' in command[:11]:
                    text_msg = text_msg[len('@sbot echo '):]
                elif 'set' in command[:10]:
                    if 'topic' in command[:16]:
                        self.message_of_chat = text_msg[len('@sbot set topic '):]
                        text_msg = 'setting motd to {}'.format(self.message_of_chat)
                elif 'disconnect' in command:
                    self.toLower(messageProtocolEntity.ack())
                    self.toLower(messageProtocolEntity.ack(True))
                    self.disconnect()
                else:
                    text_msg = str(random.choice(response_choice_list))

                data_sent = {
                    'to': recipient,
                    'message' : text_msg,
                    'time': datetime.datetime.now(),
                }
                # INSERT DATA SENT
                with ThreadPoolExecutor(max_workers=4) as executor:
                    executor.submit(message_sent_collection.insert_one, data_sent)

                outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                        text_msg,
                        to = recipient
                    )

                self.toLower(outgoingMessageProtocolEntity)
        else:
            if messageProtocolEntity.getType() == 'media':
                data_received = {
                    'from': messageProtocolEntity.getFrom(),
                    'name': messageProtocolEntity.notify,
                    'mimeType': messageProtocolEntity.mimeType or 'UNKNOWN',
                    'url': messageProtocolEntity.url or None,
                    'time': datetime.datetime.now(),
                    'type': not messageProtocolEntity.getType()
                }
                outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                        "Thanks for the image.",
                        to = recipient
                    )
                self.toLower(outgoingMessageProtocolEntity)
            else:
                data_received = {
                    'from': messageProtocolEntity.getFrom(),
                    'name': messageProtocolEntity.notify,
                    'type': not messageProtocolEntity.getType(),
                    'time': datetime.datetime.now(),
                    'elsetype': True
                }
            # INSERT DATA RECEIVED
            with ThreadPoolExecutor(max_workers=4) as executor:
                # future = executor.submit(message_collection.insert_one, data_received)
                executor.submit(message_collection.insert_one, data_received)
                # print(future.result())

        self.toLower(messageProtocolEntity.ack())
        self.toLower(messageProtocolEntity.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())


class MyNetworkLayer(YowNetworkLayer):

    def onEvent(self, ev):
        if ev.getName() == YowNetworkLayer.EVENT_STATE_CONNECT:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.out_buffer = bytearray()
            endpoint = self.getProp(self.__class__.PROP_ENDPOINT)
            logger.debug("Connecting to %s:%s" % endpoint)
            if self.proxyHandler != None:
                logger.debug("HttpProxy connect: %s:%d" % endpoint)
                self.proxyHandler.connect(self, endpoint)
            else:
                self.connect(endpoint)
            return True
        elif ev.getName() == YowNetworkLayer.EVENT_STATE_DISCONNECT:
            self.handle_close(ev.getArg("reason") or "Requested")
            return True