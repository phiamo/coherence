from telepathy.interfaces import CONN_INTERFACE, CHANNEL_INTERFACE_GROUP, \
     CHANNEL_TYPE_TUBES, CONNECTION_INTERFACE_ALIASING, CHANNEL_TYPE_TEXT
from telepathy.constants import TUBE_STATE_LOCAL_PENDING
from telepathy.constants import CONNECTION_HANDLE_TYPE_CONTACT
import telepathy

from coherence.extern.telepathy.client import Client

class TubePublisher(Client):

    def __init__(self, connection, muc_id, tubes_to_offer):
        super(TubePublisher, self).__init__(connection, muc_id)
        self._tubes_to_offer = tubes_to_offer

    def tube_opened(self, id):
        super(TubePublisher, self).tube_opened(id)
        channel_obj = self.channel_text[CHANNEL_TYPE_TEXT]
        channel_obj.connect_to_signal('Received', self.received_cb)

    def received_cb(self, id, timestamp, sender, type, flags, text):
        channel_obj = self.channel_text[CHANNEL_TYPE_TEXT]
        channel_obj.AcknowledgePendingMessages([id])
        contact = self.conn[telepathy.CONN_INTERFACE].InspectHandles(
            telepathy.HANDLE_TYPE_CONTACT, [sender])[0]

    def muc_joined(self):
        super(TubePublisher, self).muc_joined()
        self.info("muc joined. Offering the tubes")

        tubes_obj = self.channel_tubes[CHANNEL_TYPE_TUBES]
        for interface, params in self._tubes_to_offer.iteritems():
            tubes_obj.OfferDBusTube(interface, params)

class Peer:

    def __init__(self, tube_id, initiator, service):
        self.tube_id = tube_id
        self.initiator = initiator
        self.initiator_contact = None
        self.service = service
        self.remote_object = None
        self.remote_object_proxy = None

class TubeConsumer(Client):

    def __init__(self, connection, muc_id, found_peer_callback=None,
                 disapeared_peer_callback=None):
        super(TubeConsumer, self).__init__(connection, muc_id)

        self.found_peer_callback = found_peer_callback
        self.disapeared_peer_callback = disapeared_peer_callback
        self._peers = {}

    def new_tube_cb(self, id, initiator, type, service, params, state):
        self._peers[id] = Peer(id, initiator, service)

        super(TubeConsumer, self).new_tube_cb(id, initiator, type, service,
                                              params, state)
        if state == TUBE_STATE_LOCAL_PENDING:
            self.info("accepting tube %r", id)
            self.channel_tubes[CHANNEL_TYPE_TUBES].AcceptDBusTube(id)

    def _create_peer_remote_object(self, peer, interface):
        pass

    def _create_peer_object_proxy(self, peer, interface):
        pass

    def tube_opened(self, id):
        super(TubeConsumer, self).tube_opened(id)

        peer = self._peers[id]
        service = peer.service
        initiator = peer.initiator

        def find_initiator_contact(contact_list):
            conn_obj = self.conn[CONN_INTERFACE]
            initiator_contact = None
            for contact in contact_list:
                if contact[0] == initiator:
                    initiator_contact = contact[1]
                    break
            return initiator_contact

        self._create_peer_remote_object(peer, service)

        def cb(added, removed):

            # skip tubes offered by myself
            conn_obj = self.conn[CONN_INTERFACE]
            myself = conn_obj.GetSelfHandle()
            print '>>>', initiator, myself
            ## if initiator == myself:
            ##     return

            initiator_contact = find_initiator_contact(added)
            self.info("contact %r for service %r", initiator_contact,
                      service)
            peer.initiator_contact = initiator_contact
            
            self._create_peer_object_proxy(peer, service)

        peer.remote_object.tube.watch_participants(cb)

    def tube_closed_cb (self, id):
        super(TubeConsumer, self).tube_closed_cb(id)
        peer = self._peers[id]
        self.disapeared_peer_callback(peer)
        del self._peers[id]
