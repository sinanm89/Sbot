from Queue import Queue
from yowsup.layers import YowProtocolLayer, YowLayer
from yowsup.layers.network import YowNetworkLayer
from pymongo import MongoClient
from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_groups import YowGroupsProtocolLayer
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
import time

from yowsup.layers.protocol_groups.protocolentities import *

mongo_client = MongoClient('localhost', 27017)
message_collection = mongo_client['sbot_db']['received']
message_sent_collection = mongo_client['sbot_db']['sent']

q = Queue(maxsize=0)
num_threads = 10

class EchoLayer(YowInterfaceLayer):

    message_of_chat = "Motc not set"
    g_mode = False

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        #send receipt otherwise we keep receiving the same message over and over
        data_sent = None
        data_received = None

        if messageProtocolEntity.getType() == 'text':
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), 'read', messageProtocolEntity.getParticipant())
            text_msg = messageProtocolEntity.getBody()

            data_received = {
                'from': messageProtocolEntity.getFrom(),
                'name': messageProtocolEntity.notify,
                'message' : text_msg,
                'time': time.time()
            }
            # INSERT DATA RECEIVED
            message_collection.insert_one(data_received)

            if '@sbot' in text_msg:
                # import pdb; pdb.set_trace()
                command = text_msg[text_msg.index('@sbot'):]
                recipient = messageProtocolEntity.getFrom()
                if 'help' in command[:11]:
                    text_msg = 'my commands are:\n\t@sbot echo <repeat this back>\t\n@sbot topic\n\t@sbot set topic <your topic here>'
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


                data_sent = {
                    'to': recipient,
                    'message' : text_msg,
                    'time': time.time()
                }
                # INSERT DATA SENT
                message_sent_collection.insert_one(data_sent)

                outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                        text_msg,
                        to = recipient
                    )
                self.toLower(receipt)
                self.toLower(outgoingMessageProtocolEntity)
        else:
            if messageProtocolEntity.getType() == 'media':
                data_received = {
                    'from': messageProtocolEntity.getFrom(),
                    'name': messageProtocolEntity.notify,
                    'mimeType': messageProtocolEntity.mimeType or 'UNKNOWN',
                    'time': time.time(),
                    'type': not messageProtocolEntity.getType()
                }
            else:
                data_received = {
                    'from': messageProtocolEntity.getFrom(),
                    'name': messageProtocolEntity.notify,
                    'type': not messageProtocolEntity.getType(),
                    'time': time.time(),
                    'elsetype': True
                }
            # INSERT DATA RECEIVED
            message_collection.insert_one(data_received)


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

    HANDLE = (
        CreateGroupsIqProtocolEntity,
        InfoGroupsIqProtocolEntity,
        LeaveGroupsIqProtocolEntity,
        ListGroupsIqProtocolEntity,
        SubjectGroupsIqProtocolEntity,
        ParticipantsGroupsIqProtocolEntity,
        AddParticipantsIqProtocolEntity,
        PromoteParticipantsIqProtocolEntity,
        DemoteParticipantsIqProtocolEntity,
        RemoveParticipantsIqProtocolEntity
    )

    def sendIq(self, entity):
        if entity.__class__ in self.__class__.HANDLE:
            if entity.__class__ == SubjectGroupsIqProtocolEntity:
                print '1'*30
                self._sendIq(entity, self.onSetSubjectSuccess, self.onSetSubjectFailed)
            elif entity.__class__ == CreateGroupsIqProtocolEntity:
                print '2'*30
                self._sendIq(entity, self.onCreateGroupSuccess, self.onCreateGroupFailed)
            elif entity.__class__ == ParticipantsGroupsIqProtocolEntity:
                print '3'*30
                self._sendIq(entity, self.onGetParticipantsResult)
            elif entity.__class__ == AddParticipantsIqProtocolEntity:
                print '4'*30
                self._sendIq(entity, self.onAddParticipantsSuccess, self.onAddParticipantsFailed)
            elif entity.__class__ == PromoteParticipantsIqProtocolEntity:
                print '5'*30
                self._sendIq(entity, self.onPromoteParticipantsSuccess, self.onPromoteParticipantsFailed)
            elif entity.__class__ == DemoteParticipantsIqProtocolEntity:
                print '6'*30
                self._sendIq(entity, self.onDemoteParticipantsSuccess, self.onDemoteParticipantsFailed)
            elif entity.__class__ == RemoveParticipantsIqProtocolEntity:
                print '7'*30
                self._sendIq(entity, self.onRemoveParticipantsSuccess, self.onRemoveParticipantsFailed)
            elif entity.__class__ == ListGroupsIqProtocolEntity:
                print '8'*30
                self._sendIq(entity, self.onListGroupsResult)
            elif entity.__class__ == LeaveGroupsIqProtocolEntity:
                print '9'*30
                self._sendIq(entity, self.onLeaveGroupSuccess, self.onLeaveGroupFailed)
            elif entity.__class__ == InfoGroupsIqProtocolEntity:
                print 'GROUP INFO'
                self._sendIq(entity, self.onInfoGroupSuccess, self.onInfoGroupFailed)
            else:
                self.entityToLower(entity)

    def recvNotification(self, node):
        print '=======================NOTIFICATION'
        if len(node.children) > 0 and len(node.children[0].children) > 0 and len(node.children[0].children[0].children) >= 1:
            # node.children[0].children[0].children USERS IN A CHANNEL
            if 'creator' in node.children[0].children[0].attributes:
                for child in node.children[0].children[0].children:
                    if 'type' in child.attributes and child.attributes['type'] == 'admin':
                        admin = child.attributes['jid']
                        print 'ADMIN IS {}'.format(admin)
            if len(node.children[0].children[0].children) >= 1:
                print node.children[0].children[0].children
            else:
                print 'NO ADMIN DETECTED'
        elif node.children[0].tag == 'remove':
            print '---------------DUDE REMOVED'
        elif node.children[0].tag == 'add':
            print '---------------DUDE ADDED'
        else:
            print '================SOMETHING ELSE HAPPENED'
        super(MyGroupLayer, self).recvNotification(node)

    def onCreateGroupSuccess(self, node, originalIqEntity):
        print 'CREATE GROUP SUCCESS'
        print node
        super(MyGroupLayer, self).onCreateGroupSuccess(node, originalIqEntity)

    def onInfoGroupSuccess(self, node, originalIqEntity):
        print 'INFO GROUP SUCCESS'
        print node
        super(MyGroupLayer, self).onInfoGroupSuccess(node, originalIqEntity)

    # def sendIq(self, entity):
    #     print 'IQ GROUP '
    #     print entity
    #     super(MyGroupLayer, self).sendIq(entity)

    def onGetParticipantsResult(self, node, originalIqEntity):
        print 'PARITICIPANT GROUP '
        print node
        super(MyGroupLayer, self).onGetParticipantsResult(node, originalIqEntity)