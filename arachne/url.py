# -*- coding: utf-8 -*-
#
# Arachne: Search engine for files shared via FTP and similar protocols.
# Copyright (C) 2008-2010 Yasser González Fernández <ygonzalezfernandez@gmail.com>
# Copyright (C) 2008-2010 Ariel Hernández Amador <gnuaha7@gmail.com>
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

"""URL class.
"""

import logging

import urlparse


class URL(object):
    """Uniform Resource Locator.
    """

    def __init__(self, url, is_root=False):
        """Initialize the URL.

        Initialize the URL from the string `url`.
        """
        self._is_root = is_root
        self._encodings = ('utf-8', 'cp1252')
        url = self._decode_str(url)
        splitted_url = urlparse.urlsplit(url)
        root_url = u'%s://%s/' % (splitted_url.scheme, splitted_url.netloc)
        self._scheme = splitted_url.scheme
        self._username = splitted_url.username
        self._password = splitted_url.password
        self._hostname = splitted_url.hostname
        self._port = splitted_url.port
        path = url[len(root_url):].rstrip(u'/')
        if not path:
            self._path = u'/'
            self._url = root_url
            self._basename = u'/'
            self._dirname = u'/'
        else:
            self._path = u'/%s' % path.lstrip(u'/')
            self._url = u'%s%s' % (root_url, path.lstrip(u'/'))
            self._basename = self._path[self._path.rindex(u'/') + 1:]
            self._dirname = self._path[:- len(self._basename) - 1]
            if not self._dirname:
                self._dirname = u'/'

    def __str__(self):
        """Return the URL as string.
        """
        return self._url.encode(self._encodings[0])

    def __getstate__(self):
        """Used by pickle when instances are serialized.
        """
        return {
            'url': self._url.encode(self._encodings[0]),
            'is_root': self._is_root,
        }

    def __setstate__(self, state):
        """Used by pickle when instances are unserialized.
        """
        self.__init__(state['url'], state['is_root'])

    def join(self, path):
        """Join a path to the URL and return the new URL.
        """
        path = self._decode_str(path)
        base_url = self._url[:-1] if self._path == u'/' else self._url
        return URL(u'%s/%s' % (base_url, path.lstrip(u'/')))

    def _decode_str(self, byte_str):
        """Return an unicode object for the given string.
        """
        if isinstance(byte_str, unicode):
            return byte_str
        for encoding in self._encodings:
            try:
                return byte_str.decode(encoding)
            except UnicodeDecodeError:
                pass
        logging.error('Could not decode "%s", ignoring characters' % byte_str)
        return byte_str.decode(self._encodings[0], 'ignore')

    def _get_scheme(self):
        """Get method for the `scheme` property.
        """
        return self._scheme

    scheme = property(_get_scheme)

    def _get_username(self):
        """Get method for the `username` property.
        """
        return self._username

    username = property(_get_username)

    def _get_password(self):
        """Get method for the `password` property.
        """
        return self._password

    password = property(_get_password)

    def _get_hostname(self):
        """Get method for the `hostname` property.
        """
        return self._hostname

    hostname = property(_get_hostname)

    def _get_port(self):
        """Get method for the `port` property.
        """
        return self._port

    port = property(_get_port)

    def _get_path(self):
        """Get method for the `path` property.
        """
        return self._path

    path = property(_get_path)

    def _get_dirname(self):
        """Get method for the `dirname` property.
        """
        return self._dirname

    dirname = property(_get_dirname)

    def _get_basename(self):
        """Get method for the `basename` property.
        """
        return self._basename

    basename = property(_get_basename)

    def _get_is_root(self):
        """Get method for the `is_root` property.
        """
        return self._is_root

    is_root = property(_get_is_root)
