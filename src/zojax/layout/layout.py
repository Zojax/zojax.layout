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
from zope import interface
from zope.publisher import browser
from zope.component import getMultiAdapter
from zope.traversing.api import getRoot

from z3c.pt.pagetemplate import ViewPageTemplateFile

from zojax.layout.pagelet import queryLayout
from zojax.layout.interfaces import LayoutNotFound
from zojax.layout.interfaces import ILayout, ILayoutView, ILayoutTemplateFile


class LayoutTemplateFile(ViewPageTemplateFile):
    interface.implements(ILayoutTemplateFile)

    def _pt_get_context(self, layout, request, kwargs):
        view = layout.view

        namespace = super(LayoutTemplateFile, self)._pt_get_context(
            view, request, kwargs)

        namespace['layout'] = layout
        namespace['layoutcontext'] = layout.context
        namespace['mainview'] = layout.mainview
        namespace['maincontext'] = layout.maincontext
        return namespace


class Layout(browser.BrowserPage):
    interface.implements(ILayout)

    template = None
    mainview = None
    maincontext = None

    def __init__(self, view, context, request):
        self.view = view
        self.context = context
        self.request = request

        self.__parent__ = view.__parent__

    def update(self):
        pass

    def render(self):
        if self.template is None:
            view = getMultiAdapter((self, self.request), ILayoutView)
            view.update()
            return view.render()

        return self.template(
            self, context=self.view.context, request=self.request)

    def __call__(self, layout=None, view=None, *args, **kw):
        if view is None:
            view = self.view
        self.mainview = view
        self.maincontext = view.context

        layoutview = self.view
        if layout is not None:
            self.view = layout

        self.update()

        if self.layout is None:
            return self.render()

        if self.__name__ != self.layout:
            layout = queryLayout(
                view, self.request, view.__parent__, name=self.layout)
            if layout is not None:
                return layout(layout=self, view=view, *args, **kw)
        else:
            context = self.context
            if layoutview.context is not context.__parent__:
                context = context.__parent__
            else:
                context = getattr(context.__parent__, '__parent__', None)

            if context is None:
                context = getRoot(self.context)

            layout = queryLayout(self, self.request, context, name=self.layout)
            if layout is not None:
                return layout(view=view, *args, **kw)

        layout = queryLayout(
            self.view, self.context, self.request, name=self.layout)

        if layout is not None:
            return layout(*args, **kw)

        raise LayoutNotFound(self.layout)
