# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# a backend

# Copyright 2007, Frank Scholz <coherence@beebits.net>
# Copyright 2008, Jean-Michel Sizun <jm.sizun@free.fr>

from twisted.internet import defer

from coherence.upnp.core import utils

from coherence.upnp.core import DIDLLite
from coherence.upnp.core.DIDLLite import classChooser, Container, Resource, DIDLElement

import coherence.extern.louie as louie

from coherence.extern.simple_plugin import Plugin

from coherence import log

from urlparse import urlsplit

import re
from coherence.upnp.core.utils import getPage
from coherence.backend import BackendStore,BackendItem
from coherence.backends.picasa_storage import Container, LazyContainer, AbstractBackendStore

class PlaylistItem(BackendItem):
    logCategory = 'playlist_store'
    
    def __init__(self, title, stream_url, mimetype):

        self.name = title
        self.stream_url = stream_url
        self.mimetype = mimetype

        self.url = stream_url
        self.item = None
        
    def get_id(self):
        return self.storage_id

    def get_item(self):
        if self.item == None:
            upnp_id = self.get_id()
            upnp_parent_id = self.parent.get_id()
            item = DIDLLite.VideoItem(upnp_id, upnp_parent_id, self.name)
            
            # what to do with MMS:// feeds?
            protocol = "http-get"
            if self.stream_url.startswith("rtsp://"):
                protocol = "rtsp-rtp-udp"
            
            res = Resource(self.stream_url, '%s:*:%s:*' % (protocol,self.mimetype))
            res.size = None
            item.res.append(res)
        
            self.item = item
        return self.item
    
    def get_url(self):
        return self.url



class PlaylistStore(AbstractBackendStore):

    logCategory = 'playlist_store'

    implements = ['MediaServer']

    wmc_mapping = {'16': 1000}

    playlist_url = None;

    def __init__(self, server, **kwargs):
        AbstractBackendStore.__init__(self, server, **kwargs)
        
        self.playlist_url = self.config.get('playlist_url', 'http://mafreebox.freebox.fr/freeboxtv/playlist.m3u')
        self.name = self.config.get('name', 'playlist')
        
        self.init_completed()


    def __repr__(self):
        return self.__class__.__name__

    def append( self, obj, parent):
        if isinstance(obj, basestring):
            mimetype = 'directory'
        else:
            mimetype = obj['mimetype']

        UPnPClass = classChooser(mimetype)
        id = self.getnextID()
        update = False
        if hasattr(self, 'update_id'):
            update = True

        item = PlaylistItem( id, obj, parent, mimetype, self.urlbase,
                                        UPnPClass, update=update)
        
        self.store[id] = item
        self.store[id].store = self
        if hasattr(self, 'update_id'):
            self.update_id += 1
            if self.server:
                self.server.content_directory_server.set_variable(0, 'SystemUpdateID', self.update_id)
            if parent:
                value = (parent.get_id(),parent.get_update_id())
                if self.server:
                    self.server.content_directory_server.set_variable(0, 'ContainerUpdateIDs', value)

        if mimetype == 'directory':
            return self.store[id]

        return None

     
    def upnp_init(self):
        self.current_connection_id = None
        if self.server:
            self.server.connection_manager_server.set_variable(0, 'SourceProtocolInfo',
                                                                  ['rtsp-rtp-udp:*:video/mpeg:*',
                                                                  'http-get:*:video/mpeg:*',
                                                                  'rtsp-rtp-udp:*:audio/mpeg:*',
                                                                  'http-get:*:audio/mpeg:*'],
                                                                  default=True)
        
        rootItem = Container(None, self.name)
        self.set_root_item(rootItem)
        self.retrievePlaylistItems(self.playlist_url, rootItem)
  
    def retrievePlaylistItems (self, url, parent_item):
        
        def gotPlaylist(playlist):
            self.info("got playlist")
            items = {}
            if playlist :
                content,header = playlist
                lines = content.splitlines().__iter__()
                line = lines.next()
                while line is not None:
                    if re.search ( '#EXTINF', line):
                        channel = re.match('#EXTINF:.*,(.*)',line).group(1)
                        mimetype = 'video/mpeg'
                        line = lines.next()
                        while re.search ( '#EXTVLCOPT', line):
                            option = re.match('#EXTVLCOPT:(.*)',line).group(1)
                            if option == 'no-video':
                                mimetype = 'audio/mpeg'
                            line = lines.next()
                        url = line
                        item = PlaylistItem(channel, url, mimetype)
                        parent_item.add_child(item)
                    try:
                        line = lines.next() 
                    except StopIteration:
                        line = None                      
            return items

        def gotError(error):
            self.warning("Unable to retrieve playlist: %s" % url)
            print "Error: %s" % error
            return None
        
        d = getPage(url)
        d.addCallback(gotPlaylist)
        d.addErrback(gotError)            
        return d
    
