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
""" zojax.layout interfaces

$Id$
"""
from zope import interface
from zope.publisher.interfaces.browser import IBrowserPage


class LayoutNotFound(LookupError):
    """ Layout not found exception """


class IPagelet(interface.Interface):
    """ pagelet """

    context = interface.Attribute('Context')

    contexts = interface.Attribute('Additional contexts')

    isRedirected = interface.Attribute('is redirected')

    def redirect(url=''):
        """Redirect URL, if `update` method needs redirect,
        it should call `redirect` method, __call__ method should
        check isRendered before render or layout."""

    def update():
        """Update the pagelet data."""

    def render():
        """Render the pagelet content w/o o-wrap."""

    def updateAndRender():
        """Update pagelet and render. Prefered way to render pagelet."""

    def isAvailable():
        """Is available"""


class IPageletType(interface.interfaces.IInterface):
    """ pagelet interface type """


class IPageletContext(interface.Interface):
    """ pagelet contexts """


class ILayout(IBrowserPage):
    """ layout """

    title = interface.Attribute('Layout title')

    description = interface.Attribute('Layout description')

    template = interface.Attribute('Layout template')

    def update():
        """Update the layout data """

    def render():
        """Render the layout """


class ILayoutView(interface.Interface):
    """ layout view """


class ILayoutTemplateFile(interface.Interface):
    """ layout template file """


class ILayoutCreatedEvent(interface.Interface):
    """ notification about new layout """

    uid = interface.Attribute('UID')

    name = interface.Attribute('Name')

    view = interface.Attribute('View')

    context = interface.Attribute('Context')

    layer = interface.Attribute('Layer')

    layoutclass = interface.Attribute('Generated class for layout')

    keywords = interface.Attribute('Keywords')
