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
import logging, sys, re
from zope import interface, component
from zope.component import queryUtility, queryAdapter, queryMultiAdapter
from zope.publisher.browser import BrowserPage
from zope.publisher.interfaces import NotFound
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.tales.expressions import SimpleModuleImporter
from zope.app.publisher.browser import queryDefaultViewName

from interfaces import ILayout, IPagelet, IPageletType, IPageletContext


def queryLayout(view, request, context=None, iface=ILayout, name=''):
    if context is None:
        context = view.context

    while context is not None:
        layout = queryMultiAdapter((view, context, request), iface, name)
        if layout is not None:
            return layout

        context = getattr(context, '__parent__', None)

    return None


def queryPagelet(context, request, name, modules=SimpleModuleImporter()):
    pageletName = u''

    if name:
        splited = name.split(u'+', 1)
        if len(splited) > 1:
            name, pageletName = splited

        if name:
            iface = queryUtility(IPageletType, name)
        else:
            iface = IPagelet

        if iface is None:
            try:
                iface, iname = name.rsplit('.', 1)
                iface = getattr(modules[iface], iname)
            except:
                raise KeyError(name)
    else:
        iface = IPagelet

    if iface.providedBy(context):
        return context

    contexts = queryAdapter(context, IPageletContext, name)
    if contexts is not None:
        required = [context]
        if type(contexts) in (list, tuple):
            required.extend(contexts)
        else:
            required.append(contexts)
        required.append(request)
        return queryMultiAdapter(required, iface, pageletName)
    else:
        return queryMultiAdapter((context, request), iface, pageletName)


@interface.implementer(IPagelet)
@component.adapter(interface.Interface, interface.Interface)
def queryDefaultView(context, request):
    name = queryDefaultViewName(context, request, None)
    if name:
        view = queryMultiAdapter((context, request), name=name)
        if IPagelet.providedBy(view):
            return view


class BrowserPagelet(BrowserPage):
    interface.implements(IPagelet)

    template = None
    layoutname = u''
    isRedirected = False

    def __init__(self, context, *args):
        request = args[-1]
        super(BrowserPagelet, self).__init__(context, request)

        args = args[:-1]
        self.contexts = args

        for idx in range(len(args)):
            setattr(self, 'context%s'%idx, args[idx])

        self.__parent__ = context

    def update(self):
        pass

    def render(self):
        if self.template is not None:
            return self.template()
        else:
            template = queryMultiAdapter((self, self.request), IPagelet)
            if template is not None:
                template.update()
                return template.render()
            raise LookupError("Can't find IPagelet for this pagelet.")

    def updateAndRender(self):
        self.update()
        if self.isRedirected or not self.isAvailable():
            return u''

        return self.render()

    def isAvailable(self):
        return True

    def redirect(self, url=''):
        if url:
            self.request.response.redirect(url)

        self.isRedirected = True

    def __call__(self, *args, **kw):
        self.update()

        # see ticket #415 - workaround for opening links from MS Office products
        ua = self.request.get('HTTP_USER_AGENT')
        uri = self.request.get('REQUEST_URI')

        if ua and re.search('[^\w](Word|Excel|PowerPoint|ms-office)([^\w]|\z)', ua, re.I):
            return u''


        if self.isRedirected or self.request.response.getStatus() in (302, 303):
            return u''

        layout = queryLayout(
            self, self.request, self.__parent__, name=self.layoutname)
        if layout is None:
            return self.render()
        else:
            return layout()


class PageletPublisher(object):
    interface.implements(IBrowserPublisher)
    component.adapts(interface.Interface, interface.Interface)

    render = True

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def publishTraverse(self, request, name):
        try:
            return self[name]
        except KeyError:
            pass

        raise NotFound(self.context, name, request)

    def __call__(self, name=''):
        try:
            return self[name]
        except KeyError:
            pass

        return u''

    def __getitem__(self, name):
        view = queryPagelet(self.context, self.request, name)

        if view is not None:
            try:
                return view.updateAndRender()
            except Exception, err:
                log = logging.getLogger('zojax.layout')
                log.exception(err)

        raise KeyError(name)

    def browserDefault(self, request):
        return self.context, ('',)


class PageletObjectPublisher(PageletPublisher):

    def __getitem__(self, name):
        view = queryPagelet(self.context, self.request, name)

        if view is not None:
            try:
                view.update()
                return view
            except Exception, err:
                log = logging.getLogger('zojax.layout')
                log.exception(err)

        raise KeyError(name)
