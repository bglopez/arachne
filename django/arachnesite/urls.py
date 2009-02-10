# -*- coding: utf-8 -*-
#
# Arachne, a search engine for files and directories.
# Copyright (C) 2008, 2009 Yasser González Fernández <yglez@uh.cu>
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

"""URL settings module.
"""

from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': '/home/ygonzalez/Projects/arachne/Arachne/django/static/uh'}),
    (r'^$', 'arachnesite.views.basic'),
    (r'^basic/$', 'arachnesite.views.basic'),
    (r'^advanced/$', 'arachnesite.views.advanced'),
    (r'^results/$', 'arachnesite.views.results'),
)