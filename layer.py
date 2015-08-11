from yowsup.layers import YowProtocolLayer, YowLayer
from yowsup.layers.network import YowNetworkLayer
from pymongo import MongoClient
from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_groups import YowGroupsProtocolLayer
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
import time

mongo_client = MongoClient('localhost', 27017)
message_collection = mongo_client['sbot_db']['received']
message_sent_collection = mongo_client['sbot_db']['sent']

class EchoLayer(YowInterfaceLayer):

    message_of_chat = "Motc not set"

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        #send receipt otherwise we keep receiving the same message over and over
        if True:
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), 'read', messageProtocolEntity.getParticipant())
            text_msg = messageProtocolEntity.getBody()

            data = {
                'from': messageProtocolEntity.getFrom(),
                'message' : text_msg,
                'time': time.time()
            }

            message_collection.insert_one(data)

            if '@sbot' in text_msg:
                # import pdb; pdb.set_trace()
                if 'help' in text_msg[:11]:
                    text_msg = 'my commands are:\n\t@sbot echo <repeat this back>\t\n@sbot topic\n\t@sbot set topic <your topic here>'
                    recipient = messageProtocolEntity.getFrom()
                elif 'topic' in text_msg[:12]:
                    text_msg = self.message_of_chat
                    recipient = messageProtocolEntity.getFrom()
                elif 'echo' in text_msg[:11]:
                    text_msg = text_msg[len('@sbot echo '):]
                    recipient = messageProtocolEntity.getFrom()
                elif 'set' in text_msg[:10]:
                    if 'topic' in text_msg[:16]:
                        self.message_of_chat = text_msg[len('@sbot set topic '):]
                        text_msg = 'setting motd to {}'.format(self.message_of_chat)
                        recipient = messageProtocolEntity.getFrom()
            else:
                text_msg = 'Hello, Im currently in development. I may be wonky at times. My fathers amazing though, ' \
                      'let him know and he will fix it in a jiffy.\n' \
                      'my commands are:\n' \
                      '    @sbot echo <repeat this back>\n' \
                      '    @sbot topic\n' \
                      '    @sbot set topic <your topic here>'
                recipient = messageProtocolEntity.getFrom()

            outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                text_msg,
                to = recipient
            )
            data = {
                'to': recipient,
                'message' : text_msg,
                'time': time.time()}
            message_sent_collection.insert_one(data)
            self.toLower(receipt)
            self.toLower(outgoingMessageProtocolEntity)

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        # ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", "delivery", entity.getFrom())
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
        self.toLower(ack)

class MyProtocolLayer(YowProtocolLayer):

    def receive(self, data):
        """
        After decoding is done this layer receives the data and filters out so that only a group info message is taken
        and sets a variable for admin

        :param data:
        :return:
        """
        if data.tag not in ['stream:features','challenge', 'success']:
            if len(data.children) > 0 and len(data.children[0].children) > 0 and len(data.children[0].children[0].children) >= 1:
                # data.children[0].children[0].children USERS IN A CHANNEL
                if 'creator' in data.children[0].children[0].attributes:
                    for child in data.children[0].children[0].children:
                        if 'type' in child.attributes and child.attributes['type'] == 'admin':
                            admin = child.attributes['jid']
                            print 'ADMIN IS {}'.format(admin)
                else:
                    print 'NO ADMIN DETECTED'

        super(MyProtocolLayer, self).receive(data)


class MyNetworkLayer(YowNetworkLayer):

    def receive(self, data):
        print '=================NETWORK LAYER'
        print data
        print '=================//////////NETWORK LAYER'
        super(MyNetworkLayer, self).receive(data)

class PassThroughLayer(YowLayer):

    def send(self, data):
        self.toLower(data)

    def receive(self, data):
        print '--------PASSTHROUGH'
        print data
        print '--------////////////PASSTHROUGH'
        self.toUpper(data)


class MyGroupLayer(YowGroupsProtocolLayer):

    def recvNotification(self, node):
        print '=======================NOTIFICATION'
        if len(node.children) > 0 and len(node.children[0].children) > 0 and len(node.children[0].children[0].children) >= 1:
            # data.children[0].children[0].children USERS IN A CHANNEL
            if 'creator' in node.children[0].children[0].attributes:
                for child in node.children[0].children[0].children:
                    if 'type' in child.attributes and child.attributes['type'] == 'admin':
                        admin = child.attributes['jid']
                        print 'ADMIN IS {}'.format(admin)
            else:
                print 'NO ADMIN DETECTED'
        super(MyGroupLayer, self).recvNotification(node)

    def onCreateGroupSuccess(self, node, originalIqEntity):
        print 'CREATE GROUP SUCCESS'
        print node
        super(MyGroupLayer, self).onCreateGroupSuccess(node, originalIqEntity)

    def onInfoGroupSuccess(self, node, originalIqEntity):
        print 'INFO GROUP SUCCESS'
        print node
        super(MyGroupLayer, self).onInfoGroupSuccess(node, originalIqEntity)

    def sendIq(self, entity):
        print 'IQ GROUP '
        print entity
        super(MyGroupLayer, self).sendIq(entity)

    def onGetParticipantsResult(self, node, originalIqEntity):
        print 'PARITICIPANT GROUP '
        print node
        super(MyGroupLayer, self).onGetParticipantsResult(node, originalIqEntity)