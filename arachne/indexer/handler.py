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

"""Protocol handlers.
"""

import os
import socket
import ftplib

from arachne.indexer.result import CrawlResult


class ProtocolHandler(object):
    """Protocol handler.

    Abstract class that should be subclassed by all supported protocols in the
    crawler.  This provides a way to extend the crawler to support new
    protocols.  Instances of this class are used by the `SiteCrawler`.

    The subclasses should set the `scheme` class attribute to the URL scheme
    specifier for the protocol.
    """

    scheme = ''

    def __init__(self, sites_info):
        """Initialize the protocol handler.

        The `sites_info` argument will be a dictionary mapping site IDs to the
        information for the sites.  This can be usefull to support advanced
        settings for a site (e.g. proxy server).
        """

    def execute(self, task):
        """Execute the task and return the result.

        If the task is successfully executed the `CrawlResult` instance should
        be returned, `None` otherwise.
        """
        raise NotImplementedError()


class FileHandler(ProtocolHandler):
    """Handler for local files.
    """

    scheme = 'file'

    def __init__(self, sites_info):
        """Initialize handler.
        """
        ProtocolHandler.__init__(self, sites_info)

    def execute(self, task):
        """Execute the task and return the result.
        """
        try:
            url = task.url
            if os.path.isdir(url.path):
                result = CrawlResult(task, True)
                for entry_name in os.listdir(url.path):
                    data = {}
                    entry_path = os.path.join(url.path, entry_name)
                    data['is_dir'] = os.path.isdir(entry_path)
                    result.append(entry_name, data)
            else:
                result = CrawlResult(task, False)
        except OSError:
            return None
        else:
            return result


class FTPHandler(ProtocolHandler):
    """Handler for FTP sites.
    """

    scheme = 'ftp'

    def __init__(self, sites_info):
        """Initialize the handler.
        """
        ProtocolHandler.__init__(self, sites_info)

    def execute(self, task):
        """Execute the task and return the result.
        """
        url = task.url
        try:
            ftp = ftplib.FTP()
            if url.port:
                ftp.connect(url.host, url.port)
            else:
                ftp.connect(url.host)
            if url.username:
                ftp.login(url.username, url.password)
            else:
                ftp.login()
            try:
                ftp.cwd(url.path)
            except ftplib.error_perm:
                # Failed to change directory.
                result = CrawlResult(task, False)
            else:
                # It seems to be a valid directory.
                result = CrawlResult(task, True)
                entries = []
                callback = lambda line: entries.append(self._parse_list(line))
                ftp.retrlines('LIST', callback)
                for entry_name, is_dir in (entry for entry in entries
                                           if entry is not None):
                    data = {}
                    if is_dir is not None:
                        data['is_dir'] = is_dir
                    else:
                        # The parser does not known if this entry is a
                        # directory or not.  Try to change directory, if error,
                        # assume it is a file.
                        try:
                            entry_url = url.join(entry_name)
                            ftp.cwd(entry_url.path)
                        except ftplib.error_perm:
                            data['is_dir'] = False
                        else:
                            data['is_dir'] = True
                    result.append(entry_name, data)
            ftp.quit()
        except socket.error:
            # TODO: Log the error message.
            return None
        except ftplib.Error:
            # TODO: Log the error message.
            ftp.quit()
            return None
        else:
            return result

    @staticmethod
    def _parse_list(line):
        """Parse lines from a LIST response.

        `None` is returned if could not parse the line, otherwise it returns a
        tuple containing the name of the item and a Boolean value indicating if
        it is a directory.  The Boolean value will be `None` if the parse could
        not known if the item is a directory or not.
        """
        # Based on ftpparse.c and ftpparse.h by D. J. Bernstein.
        if line.startswith(tuple('-dbclps')):
            # UNIX-style listing.
            try:
                if line[0] == '-':
                    is_dir = False
                elif line[0] == 'd':
                    is_dir = True
                else:
                    is_dir = None
                data = line.split(None, 8)
                if len(data) == 9:
                    if line[0] == 'l':
                        name = data[-1].split(' -> ')[0]
                    else:
                        name = data[-1]
                else:
                    raise ValueError()
            except ValueError:
                return None
            else:
                return (name, is_dir)
        elif line.startswith(tuple('0123456789')):
            # MSDOS format.
            try:
                line  = line[17:].lstrip()
                if line.startswith('<DIR>'):
                    is_dir = True
                    name = line[15:]
                else:
                    is_dir = False
                    name = line[line.index(' ') + 1:]
            except (IndexError, ValueError):
                return None
            else:
                return (name, is_dir)
        elif line.startswith('+'):
            # Easily Parsed LIST Format.
            try:
                facts, name = line[1:].split('\t')
                facts = facts.split(',')
                is_dir = '/' in facts
            except IndexError:
                return None
            else:
                return (name, is_dir)
        else:
            # Could not parse the line.  Maybe because the format is unknown
            # format or it contains additional information provided by the FTP
            # server that can be ignored.
            return None