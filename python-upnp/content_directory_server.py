# Licensed under the MIT license
# http://opensource.org/licenses/mit-license.php

# Copyright 2005, Tim Potter <tpot@samba.org>
# Copyright 2006 John-Mark Gurney <gurney_j@resnet.uoregon.edu>
# Copyright 2006, Frank Scholz <coherence@beebits.net>

# Content Directory service

from twisted.python import log
from twisted.web import resource, static, soap

from twisted.python import reflect

from elementtree.ElementTree import Element, SubElement, ElementTree, tostring

from soap_service import UPnPPublisher

import service

class ContentDirectoryControl(service.ServiceControl,UPnPPublisher):

    def soap_GetSearchCapabilities(self, *args, **kwargs):
        """Required: Return the searching capabilities supported by the device."""

        log.msg('GetSearchCapabilities()')
        return { 'SearchCapabilitiesResponse': { 'SearchCaps': '' }}

    def soap_GetSortCapabilities(self, *args, **kwargs):
        """Required: Return the CSV list of meta-data tags that can be used in
        sortCriteria."""

        log.msg('GetSortCapabilities()')
        return { 'SortCapabilitiesResponse': { 'SortCaps': '' }}

    def soap_GetSystemUpdateID(self, *args, **kwargs):
        """Required: Return the current value of state variable SystemUpdateID."""

        log.msg('GetSystemUpdateID()')
        print 'GetSystemUpdateID()', kwargs
        return { 'SystemUpdateIdResponse': { 'Id': 0 }}

    BrowseFlags = ('BrowseMetaData', 'BrowseDirectChildren')

    def soap_Browse(self, *args):
        r = { 'Result': didl.toString(), 'TotalMatches': total,
            'NumberReturned': didl.numItems(), }
        result = { 'BrowseResponse': r }
        if hasattr(self[ObjectID], 'updateID'):
            r['UpdateID'] = self[ObjectID].updateID
        else:
            r['UpdateID'] = self.updateID

        return result

    def soap_Search(self, *args, **kwargs):
        """Search for objects that match some search criteria."""

        (ContainerID, SearchCriteria, Filter, StartingIndex,
         RequestedCount, SortCriteria) = args

        log.msg('Search(ContainerID=%s, SearchCriteria=%s, Filter=%s, ' \
            'StartingIndex=%s, RequestedCount=%s, SortCriteria=%s)' %
            (`ContainerID`, `SearchCriteria`, `Filter`,
            `StartingIndex`, `RequestedCount`, `SortCriteria`))

    def soap_CreateObject(self, *args, **kwargs):
        """Create a new object."""

        (ContainerID, Elements) = args

        log.msg('CreateObject(ContainerID=%s, Elements=%s)' %
            (`ContainerID`, `Elements`))

    def soap_DestroyObject(self, *args, **kwargs):
        """Destroy the specified object."""

        (ObjectID) = args

        log.msg('DestroyObject(ObjectID=%s)' % `ObjectID`)

    def soap_UpdateObject(self, *args, **kwargs):
        """Modify, delete or insert object metadata."""

        (ObjectID, CurrentTagValue, NewTagValue) = args

        log.msg('UpdateObject(ObjectID=%s, CurrentTagValue=%s, ' \
            'NewTagValue=%s)' % (`ObjectID`, `CurrentTagValue`,
            `NewTagValue`))

    def soap_ImportResource(self, *args, **kwargs):
        """Transfer a file from a remote source to a local
        destination in the Content Directory Service."""

        (SourceURI, DestinationURI) = args

        log.msg('ImportResource(SourceURI=%s, DestinationURI=%s)' %
            (`SourceURI`, `DestinationURI`))

    def soap_ExportResource(self, *args, **kwargs):
        """Transfer a file from a local source to a remote
        destination."""

        (SourceURI, DestinationURI) = args

        log.msg('ExportResource(SourceURI=%s, DestinationURI=%s)' %
            (`SourceURI`, `DestinationURI`))

    def soap_StopTransferResource(self, *args, **kwargs):
        """Stop a file transfer initiated by ImportResource or
        ExportResource."""

        (TransferID) = args

        log.msg('StopTransferResource(TransferID=%s)' % TransferID)

    def soap_GetTransferProgress(self, *args, **kwargs):
        """Query the progress of a file transfer initiated by
        an ImportResource or ExportResource action."""

        (TransferID, TransferStatus, TransferLength, TransferTotal) = args

        log.msg('GetTransferProgress(TransferID=%s, TransferStatus=%s, ' \
            'TransferLength=%s, TransferTotal=%s)' %
            (`TransferId`, `TransferStatus`, `TransferLength`,
            `TransferTotal`))

    def soap_DeleteResource(self, *args, **kwargs):
        """Delete a specified resource."""

        (ResourceURI) = args

        log.msg('DeleteResource(ResourceURI=%s)' % `ResourceURI`)

    def soap_CreateReference(self, *args, **kwargs):
        """Create a reference to an existing object."""

        (ContainerID, ObjectID) = args

        log.msg('CreateReference(ContainerID=%s, ObjectID=%s)' %
            (`ContainerID`, `ObjectID`))


class ContentDirectoryServer(service.Server, resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)
        service.Server.__init__(self, 'ContentDirectory')
        
        self.content_directory_control = ContentDirectoryControl()
        self.putChild('scpd.xml', service.scpdXML(self, self.content_directory_control))
        self.putChild('control', self.content_directory_control)

        
    def listchilds(self, uri):
        cl = ''
        for c in self.children:
                cl += '<li><a href=%s/%s>%s</a></li>' % (uri,c,c)
        return cl

    def render(self,request):
        return '<html><p>root of the ContentDirectory</p><p><ul>%s</ul></p></html>'% self.listchilds(request.uri)
