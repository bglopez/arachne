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

"""Queue for crawl tasks and the crawl task definition.
"""

import os
import sys
import time
import glob
import math
import bsddb
import pickle
import threading

from arachne.error import EmptyQueue


class CrawlTask(object):
    """Crawl task.

    This class represents an action to list the content of a directory.
    Executing a task produces a `CrawlResult`.
    """

    def __init__(self, site_id, url):
        """Initialize a crawl task.
        """
        self._site_id = site_id
        self._url = url
        self._revisit_wait = 0
        self._revisit_count = 0
        self._change_count = 0

    def __getstate__(self):
        """Used by pickle when instances are serialized.
        """
        return {
            'site_id': self._site_id,
            'url': self._url,
            'revisit_wait': self._revisit_wait,
            'revisit_count': self._revisit_count,
            'change_count': self._change_count,
        }

    def __setstate__(self, state):
        """Use by pickle when instances are serialized.
        """
        self._site_id = state['site_id']
        self._url = state['url']
        self._revisit_wait = state['revisit_wait']
        self._revisit_count = state['revisit_count']
        self._change_count = state['change_count']

    def report_revisit(self, changed):
        """Report that the directory was revisited.

        The `changed` argument should be set to `True` if the content of the
        directory changed, `False` otherwise.
        """
        if changed:
            self._change_count += 1
        self._revisit_count += 1

    def _get_site_id(self):
        """Get method for the `site_id` property.
        """
        return self._site_id

    def _get_url(self):
        """Get method for the `url` property.
        """
        return self._url

    def _get_revisit_wait(self):
        """Get method for the `revisit_wait` property.
        """
        return self._revisit_wait

    def _set_revisit_wait(self, seconds):
        """Set method for the `revisit_wait` property.

        This method also resets the counters for revisits and changes.
        """
        self._revisit_wait = seconds
        self._revisit_count = 0
        self._change_count = 0

    def _get_revisit_count(self):
        """Get method for the `revisit_count` property.
        """
        return self._revisit_count

    def _get_change_count(self):
        """Get method for the `change_count` property.
        """
        return self._change_count

    site_id = property(_get_site_id)

    url = property(_get_url)

    revisit_wait = property(_get_revisit_wait, _set_revisit_wait)

    revisit_count = property(_get_revisit_count)

    change_count = property(_get_change_count)


class TaskQueue(object):
    """Task queue.

    Queue used to collect the crawl tasks (`CrawlTask`) that are going to be
    executed in the future.
    """

    def __init__(self, sites_info, db_home):
        """Initializes the queue.
        """
        # Initialize the Berkeley DB environment.  This environment will
        # contain Btree databases with duplicated records (unsorted).  Records
        # in all databases uses strings with an integer indicating when the
        # tasks should be executed.
        self._db_env = bsddb.db.DBEnv()
        self._db_env.open(db_home, bsddb.db.DB_CREATE | bsddb.db.DB_RECOVER
                          | bsddb.db.DB_INIT_TXN | bsddb.db.DB_INIT_LOG
                          | bsddb.db.DB_INIT_MPOOL)
        self._key_length = len(str(sys.maxint))
        # Create the database for the sites.
        sites_db_name = 'sites.db'
        self._sites_db = bsddb.db.DB(self._db_env)
        self._sites_db.set_flags(bsddb.db.DB_DUP)
        self._sites_db.open(sites_db_name, bsddb.db.DB_BTREE,
                            bsddb.db.DB_CREATE | bsddb.db.DB_AUTO_COMMIT)
        # Get the list of databases to purge old ones (sites that were removed
        # from the configuration file).
        old_dbs = [os.path.basename(db_path)
                   for db_path in glob.glob('%s/*.db' % db_home.rstrip('/'))]
        old_dbs.remove(sites_db_name)
        # Open or create databases for tasks.
        self._task_dbs = {}
        for site_id, info in sites_info.iteritems():
            task_db_name = '%s.db' % site_id
            task_db = bsddb.db.DB(self._db_env)
            task_db.set_flags(bsddb.db.DB_DUP)
            task_db.open(task_db_name, bsddb.db.DB_BTREE,
                         bsddb.db.DB_CREATE | bsddb.db.DB_AUTO_COMMIT)
            self._task_dbs[site_id] = task_db
            if task_db_name in old_dbs:
                old_dbs.remove(task_db_name)
            else:
                # New site added to the configuration file.  Create a new task
                # to list the content of the root directory.
                self._sites_db.put(self._get_priority(), site_id)
                task = CrawlTask(site_id, info['url'])
                self._put(task, self._get_priority())
        for task_db_name in old_dbs:
            self._db_env.dbremove(task_db_name)
        self._sites_info = sites_info
        self._revisits = 5
        self._mutex = threading.Lock()

    def __len__(self):
        """Return the number of crawl tasks in the queue.
        """
        self._mutex.acquire()
        try:
            return sum(len(task_db) for task_db in self._task_dbs.itervalues())
        finally:
            self._mutex.release()

    def put_new(self, task):
        """Put a task for a new directory.

        A new directory is a directory that has not been visited.  The
        `TaskQueue` will assign a privileged priority for this task.
        """
        self._mutex.acquire()
        try:
            self._put(task, self._get_priority())
        finally:
            self._mutex.release()

    def put_visited(self, task):
        """Put a task for a visited directory.

        A visited directory is a directory visited for first time.  The
        `TaskQueue` will schedule a task to revisit the directory.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            revisit_wait = self._sites_info[site_id]['default_revisit_wait']
            task.revisit_wait = revisit_wait
            self._put(task, self._get_priority(task.revisit_wait))
        finally:
            self._mutex.release()

    def put_revisited(self, task, changed):
        """Put a task for a revisited directory.

        A revisited directory is a directory that is already indexed and it is
        visited to check if it changed.  The `changed` argument should be
        `True` if the directory changed, `False` otherwise.  This information
        will be used to estimate the change frequency.  The `TaskQueue` will
        schedule a task to revisit the directory.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            task.report_revisit(changed)
            if task.revisit_count >= self._revisits:
                estimated = self._estimate_revisit_wait(task)
                minimum = self._sites_info[site_id]['min_revisit_wait']
                maximum = self._sites_info[site_id]['max_revisit_wait']
                task.revisit_wait = min(maximum, max(minimum, estimated))
            self._put(task, self._get_priority(task.revisit_wait))
        finally:
            self._mutex.release()

    def get(self):
        """Return an executable task.

        Return a task executable right now.  The task should be reported later
        as done or error using `report_done()` and `report_error()`.  If there
        is not executable task an `EmptyQueue` exception is raised.
        """
        self._mutex.acquire()
        try:
            if not self._sites_db:
                # Sites database is empty.
                raise EmptyQueue('Queue without sites.')
            task = None
            transaction = self._db_env.txn_begin()
            sites_cursor = self._sites_db.cursor(transaction)
            site_priority, site_id = sites_cursor.first()
            while task is None:
                site_priority, site_id = sites_cursor.current()
                if site_priority > self._get_priority():
                    # The site cannot be visited right now.
                    sites_cursor.close()
                    transaction.commit()
                    raise EmptyQueue('Queue without available sites.')
                try:
                    task_db = self._task_dbs[site_id]
                except KeyError:
                    # The head of the sites database is an old site.
                    sites_cursor.delete()
                    if not sites_cursor.next():
                        # Last site in database checked.
                        sites_cursor.close()
                        transaction.commit()
                        raise EmptyQueue('Queue without available sites.')
                else:
                    if not task_db:
                        # The task database is empty.
                        if not sites_cursor.next():
                            # Last site in database checked.
                            sites_cursor.close()
                            transaction.commit()
                            raise EmptyQueue('Queue without available sites.')
                    else:
                        task_cursor = task_db.cursor(transaction)
                        task_priority, task_data = task_cursor.first()
                        if task_priority > self._get_priority():
                            # The task at the head of the database is not
                            # executable right now.
                            if not sites_cursor.next():
                                # Last site in database checked.
                                task_cursor.close()
                                sites_cursor.close()
                                transaction.commit()
                                raise EmptyQueue('Queue without available sites.')
                        else:
                            # There is an executable task.
                            sites_cursor.delete()
                            task = pickle.loads(task_data)
                        task_cursor.close()
            sites_cursor.close()
            transaction.commit()
            return task
        finally:
            self._mutex.release()

    def report_done(self, task):
        """Report task as done.

        Report a task returned by `get()` as successfully done.  The
        `TaskQueue` will guarantee that the site will not be visited until the
        time of request wait is elapsed.
        """
        self._mutex.acquire()
        try:
            site_id = task.site_id
            task_db = self._task_dbs[site_id]
            transaction = self._db_env.txn_begin()
            request_wait = self._sites_info[site_id]['request_wait']
            site_key = self._get_priority(request_wait)
            self._sites_db.put(site_key, site_id, transaction)
            task_cursor = task_db.cursor(transaction)
            task_cursor.first()
            task_cursor.delete()
            task_cursor.close()
            transaction.commit()
        finally:
            self._mutex.release()

    def report_error(self, task):
        """Report an error executing a task.

        Report an error executing a task returned by `get()`.  This usually
        means that the site was unreachable.  The `TaskQueue` should wait a
        time longer than the request wait before allowing contact the site
        again.
        """
        self._mutex.acquire()
        try:
            # Do not remove the task from the database!
            site_id = task.site_id
            error_wait = self._sites_info[site_id]['error_wait']
            site_key = self._get_priority(error_wait)
            self._sites_db.put(site_key, site_id)
        finally:
            self._mutex.release()

    def sync(self):
        """Synchronize the queue on disk.
        """
        self._mutex.acquire()
        try:
            self._sites_db.sync()
            for task_db in self._task_dbs.itervalues():
                task_db.sync()
        finally:
            self._mutex.release()

    def close(self):
        """Close the queue.
        """
        self._mutex.acquire()
        try:
            self._sites_db.close()
            for task_db in self._task_dbs.itervalues():
                task_db.close()
            self._db_env.close()
        finally:
            self._mutex.release()

    def _put(self, task, priority):
        """Put a task in the queue.

        Internal method used to put a task in the queue.  It is invoked by
        `put_new()`, `put_visited()` and `put_revisited()` with the right
        priority for the task.
        """
        task_db = self._task_dbs[task.site_id]
        task_db.put(priority, pickle.dumps(task))

    def _get_priority(self, seconds=0):
        """Return a priority value.

        Return an string (seconds since UNIX epoch) that can be used as
        priority for a task that needs to be executed after `seconds` seconds.
        The default value for the `seconds` argument is 0, meaning right now.
        """
        return str(int(time.time()) + seconds).zfill(self._key_length)

    @staticmethod
    def _estimate_revisit_wait(task):
        """Return an estimate revisit wait for the task.
        """
        # This algorithm uses the estimator proposed by Junghoo Cho (University
        # of California, LA) and Hector Garcia-Molina (Stanford University) in
        # "Estimating Frequency of Change".
        if task.change_count:
            changes = task.change_count
            visits = task.revisit_count
            wait = task.revisit_wait
            new_wait  = wait / - math.log((visits - changes + 0.5) /
                                          (visits + 0.5))
            new_wait = int(round(new_wait))
        else:
            new_wait = task.revisit_wait
        return new_wait