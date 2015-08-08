from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity



class EchoLayer(YowInterfaceLayer):

    message_of_chat = 'Motc not set'

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        #send receipt otherwise we keep receiving the same message over and over

        if True:
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), 'read', messageProtocolEntity.getParticipant())
            # import pdb; pdb.set_trace()
            message = messageProtocolEntity.getBody()
                # send to a specific user
            if '@sbot' in message:
                if 'help' in message[:11]:
                    message = 'my commands are:\n\t@sbot echo <repeat this back>\t\n@sbot topic\n\t@sbot set topic <your topic here>'
                    outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                        message,
                        to = messageProtocolEntity.getFrom()
                        )
                elif 'topic' in message[:12]:
                    outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                        self.message_of_chat,
                        to = messageProtocolEntity.getFrom()
                        )
                elif 'echo' in message[:11]:
                    message = message[len('@sbot echo '):]
                    outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                        message,
                        to = messageProtocolEntity.getFrom()
                        )
                elif 'set' in message[:10]:
                    if 'topic' in message[:16]:
                        self.message_of_chat = message[len('@sbot set topic '):]
                        outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                            'setting motd to {}'.format(self.message_of_chat),
                            to = messageProtocolEntity.getFrom()
                            )
            # outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                # message,
                # to = messageProtocolEntity.getFrom())

            self.toLower(receipt)
            self.toLower(outgoingMessageProtocolEntity)

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", "delivery", entity.getFrom())
        self.toLower(ack)