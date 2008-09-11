# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Yasser González Fernández <yglez@uh.cu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import urlparse

from aracne.errors import EmptyQueueError


class CrawlResult(object):
    """Crawl result.

    It represents and contains the result of listing the files and directories
    found inside of a given directory.  It is the result of executing a
    `CrawlTask`.
    """

    def __init__(self, siteid, url, found=True):
        """Initialize a crawl result without entries.
        """
        self._siteid = siteid
        self._url = url
        self._found = found
        self._entries = []

    def __iter__(self):
        """Iterate over entries in the directory.
        """
        return iter(self._entries)

    def __getstate__(self):
        """Used by pickle when instances are serialized.
        """
        return {
            'siteid': self._siteid,
            'url': self._url,
            'found': self._found,
            'entries': self._entries,
        }

    def __setstate__(self, state):
        """Used by pickle when instances are unserialized.
        """
        self._siteid = state['siteid']
        self._url = state['url']
        self._found = state['found']
        self._entries = state['entries']

    siteid = property(lambda self: self._siteid)

    url = property(lambda self: self._url)

    found = property(lambda self: self._found)

    def append(self, entry, metadata):
        """Append a new entry to the crawl result of the directory.
        """
        # TODO: Appending entries to a "not found" result?
        url = urlparse.urljoin(self._url, entry)
        self._entries.append((url, metadata))


class ResultQueue(object):
    """Crawl result queue.

    Collects and organizes the crawl results (`CrawlResult`) waiting to be
    processed.
    """

    def __init__(self, sites):
        """Initializes the queue.
        """
        logging.debug('Initializing result queue.')
        logging.debug('Result queue initialized.')

    def put(self, result):
        """Enqueue a result.

        Puts the crawl result (`CrawlResult`) received as argument in the
        queue.
        """

    def get(self):
        """Returns the result at the top of the queue.

        Returns the crawl result (`CrawlResult`) at the top of the queue.  The
        result should be reported as processed using `report_done()`.  If there
        is not an available result an `EmptyQueueError` exception is raised.
        """
        raise EmptyQueueError()

    def report_done(self, result):
        """Reports a result as processed.
        """
