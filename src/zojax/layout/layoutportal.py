##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id$
"""
from zope.app.pagetemplate import ViewPageTemplateFile


class DefaultLayoutPortal(object):

    content = ViewPageTemplateFile('layoutportaltmpl.pt')

    def render(self):
        rendered = self.template(
            self, context=self.view.context, request=self.request)

        tmpl = self.content(self)

        parts = tmpl.split(u'<!-- default layout portal contents -->', 1)

        if len(parts) == 2:
            return parts[0] + rendered + parts[1]
        else:
            return rendered
