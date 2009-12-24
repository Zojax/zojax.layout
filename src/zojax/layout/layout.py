##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors.
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
from zope.app.pagetemplate.engine import TrustedAppPT
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

from zojax.layout.pagelet import queryLayout
from zojax.layout.interfaces import LayoutNotFound, ILayout, ILayoutTemplateFile


class ViewMapper(object):

    def __init__(self, ob, request):
        self.ob = ob
        self.request = request

    def __getitem__(self, name):
        return getMultiAdapter((self.ob, self.request), name=name)


class LayoutTemplateFile(TrustedAppPT, PageTemplateFile): 
    interface.implements(ILayoutTemplateFile)

    expand = False

    def __init__(self, filename, _prefix=None, content_type=None):
        _prefix = self.get_path_from_prefix(_prefix)
        super(LayoutTemplateFile, self).__init__(filename, _prefix)
        if content_type is not None:
            self.content_type = content_type

    def pt_getContext(self, layout, **_kw):
        view = layout.view

        # instance is a View component
        namespace = super(LayoutTemplateFile, self).pt_getContext(**_kw)
        namespace['view'] = view
        namespace['request'] = layout.request
        namespace['context'] = view.context
        namespace['layout'] = layout
        namespace['layoutcontext'] = layout.context
        namespace['mainview'] = layout.mainview
        namespace['maincontext'] = layout.maincontext
        namespace['views'] = ViewMapper(view.context, layout.request)
        return namespace

    def __call__(self, layout, *args, **kw):
        namespace = self.pt_getContext(layout, args=args, options=kw)
        return self.pt_render(namespace)


class Layout(browser.BrowserPage):
    interface.implements(ILayout)

    mainview = None
    maincontext = None

    def __init__(self, view, context, request):
        self.view = view
        self.context = context
        self.request = request

        self.__parent__ = view.context

    def update(self):
        pass

    def render(self):
        return self.template(self)

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
            layout = queryLayout(view, self.request, name=self.layout)
            if layout is not None:
                return layout(layout=self, view=view, *args, **kw)
        else:
            if layoutview.context is not self.context.__parent__:
                context = self.context.__parent__
            else:
                context = getattr(self.context.__parent__, '__parent__')

            layout = queryLayout(self, self.request, context, name=self.layout)
            if layout is not None:
                return layout(view=view, *args, **kw)

        layout = queryLayout(self.view, self.context, self.request, name=self.layout)
        if layout is not None:
            return layout(*args, **kw)

        raise LayoutNotFound(self.layout)
