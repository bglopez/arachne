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

import Queue

from aracne.errors import EmptyQueueError


class CrawlTask(object):
    """Crawl task.

    Represents the action of retrieving the list of files and directories found
    inside of a given directory in a site.  The result of executing this task
    is a `CrawlResult`.
    """


class TaskQueue(object):
    """Task queue.

    Collects and organizes the pending `CrawlTask`.
    """

    def __init__(self, config):
        """Initialize attributes.
        """
        self._queue = Queue.Queue()

    def put(self, item):
        """Put an item into the queue.
        """
        self._queue.put(item)

    def get(self):
        """Remove and return an item from the queue.
        """
        try:
            item = self._queue.get(False)
        except Queue.Empty:
            raise EmptyQueueError()
        else:
            return item
