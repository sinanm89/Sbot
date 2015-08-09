from pymongo import MongoClient
from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
import time

mongo_client = MongoClient('localhost', 27017)
message_collection = mongo_client['sbot_db']['received']
message_sent_collection = mongo_client['sbot_db']['sent']

class EchoLayer(YowInterfaceLayer):

    message_of_chat = 'Motc not set'

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        #send receipt otherwise we keep receiving the same message over and over

        if True:
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), 'read', messageProtocolEntity.getParticipant())
            # import pdb; pdb.set_trace()
            message = messageProtocolEntity.getBody()

            data = {
                'from': messageProtocolEntity.getFrom(),
                'message' : message,
                'time': time.time()}

            message_collection.insert_one(data)
                # send to a specific user
            message = 'Hello, Im currently in development. I may be wonky at times. My fathers amazing though, ' \
                      'let him know and he will fix it in a jiffy.\n' \
                      'my commands are:\n' \
                      '    @sbot echo <repeat this back>\n' \
                      '    @sbot topic\n' \
                      '    @sbot set topic <your topic here>'
            receipient = messageProtocolEntity.getFrom()

            if '@sbot' in message:
                # import pdb; pdb.set_trace()
                if 'help' in message[:11]:
                    message = 'my commands are:\n\t@sbot echo <repeat this back>\t\n@sbot topic\n\t@sbot set topic <your topic here>'
                    receipient = messageProtocolEntity.getFrom()
                elif 'topic' in message[:12]:
                    message = self.message_of_chat,
                    receipient = messageProtocolEntity.getFrom()
                elif 'echo' in message[:11]:
                    message = message[len('@sbot echo '):]
                    receipient = messageProtocolEntity.getFrom()
                elif 'set' in message[:10]:
                    if 'topic' in message[:16]:
                        self.message_of_chat = message[len('@sbot set topic '):]
                        message = 'setting motd to {}'.format(self.message_of_chat),
                        receipient = messageProtocolEntity.getFrom()

            outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                message,
                to = receipient
            )
            data = {
                'to': receipient,
                'message' : message,
                'time': time.time()}
            message_sent_collection.insert_one(data)
            self.toLower(receipt)
            self.toLower(outgoingMessageProtocolEntity)

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", "delivery", entity.getFrom())
        self.toLower(ack)
