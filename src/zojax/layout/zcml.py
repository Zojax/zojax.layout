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
import os.path
from zope import schema, interface, event
from zope.component.interface import provideInterface
from zope.component.zcml import handler, adapter, utility
from zope.security.checker import defineChecker, Checker, CheckerPublic
from zope.configuration.fields import Path, Tokens, GlobalObject, GlobalInterface
from zope.configuration.exceptions import ConfigurationError
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.app.component.metadirectives import IBasicViewInformation
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

from interfaces import IPagelet, IPageletType
from interfaces import ILayout, ILayoutCreatedEvent

from pagelet import BrowserPagelet
from layout import Layout, LayoutTemplateFile


class IPageletDirective(IBasicViewInformation):
    """A directive to register a new pagelet.

    The pagelet directive also supports an undefined set of keyword arguments
    that are set as attributes on the pagelet after creation.
    """

    for_ = GlobalObject(
        title = u"Context",
        description = u"The content interface or class this pagelet is for.",
        required = False)

    name = schema.TextLine(
        title = u"The name of the pagelet.",
        description = u"The name shows up in URLs/paths. For example 'foo'.",
        required = False)

    provides = Tokens(
        title = u"The interface this pagelets provides.",
        description = u"""A pagelet can provide an interface.  This would be used for
        views that support other views.""",
        required = False,
        value_type = GlobalInterface(),
        default = [IPagelet,])

    class_ = GlobalObject(
        title=u"Class",
        description=u"A class that provides attributes used by the pagelet.",
        required=False,
        )

    template = Path(
        title = u'Pagelet template.',
        description = u"Refers to a file containing a page template (should "\
                                    "end in extension ``.pt`` or ``.html``).",
        required=False)

    layout = schema.TextLine(
        title = u'The name of the layout.',
        description = u"The name is used to look up the layout.",
        default=u'',
        required=False)

# Arbitrary keys and values are allowed to be passed to the pagelet.
IPageletDirective.setTaggedValue('keyword_arguments', True)


class ILayoutDirective(interface.Interface):

    uid = schema.TextLine(
        title = u"Unique layout id",
        default = u'',
        required = False)

    template = Path(
        title=u'Layout template.',
        description=u"Refers to a file containing a page template (should "
                     "end in extension ``.pt`` or ``.html``).",
        required=False,
        )

    name = schema.TextLine(
        title=u"The name of the layout.",
        description=u"The name is used to look up the layout.",
        default=u'',
        required=False)

    layer = GlobalObject(
        title = u'Layer',
        description = u'The layer for which the template should be available',
        required = False,
        default=IDefaultBrowserLayer,
        )

    contentType = schema.BytesLine(
        title = u'Content Type',
        description=u'The content type identifies the type of data.',
        default='text/html',
        required=False,
        )

    provides = GlobalInterface(
        title=u"Interface the layout provides",
        description=u"This attribute specifies the interface the layout"
                      " instance will provide.",
        default=ILayout,
        required=False,
        )

    for_ = GlobalObject(
        title = u'Context',
        description = u'The object for which the layout should be available',
        default=interface.Interface,
        required = False)

    view = GlobalObject(
        title = u'View',
        description = u'The view for which the layout should be available',
        default=interface.Interface,
        required = False)

    class_ = GlobalObject(
        title=u"Class",
        description=u"A class that provides attributes used by the layout.",
        required=False,
        )

    layout = schema.TextLine(
        title = u'Layout',
        description = u'Custom layout name.',
        required = False)

    title = schema.TextLine(
        title = u'Layout title',
        required = False)

    description = schema.TextLine(
        title = u'Layout description',
        required = False)

# Arbitrary keys and values are allowed
ILayoutDirective.setTaggedValue('keyword_arguments', True)


def layoutDirective(
    _context, uid='', template='', for_=None, view=None, name = u'',
    layer = IDefaultBrowserLayer, provides = ILayout,
    contentType='text/html', class_ = None, layout = '', 
    title='', description='', **kwargs):

    if not layout:
        layout = None
    elif layout == '.':
        layout = ''

    # Make sure that the template exists
    if template:
        template = os.path.abspath(str(_context.path(template)))
        if not os.path.isfile(template):
            raise ConfigurationError("No such file", template)

    # Check
    if (for_ is None) and (view is None):
        raise ConfigurationError("FOR or VIEW are required.")

    # Build a new class that we can use different permission settings if we
    # use the class more then once.
    cdict = {}
    cdict['__name__'] = name
    cdict['layout'] = layout
    cdict['title'] = title
    cdict['description'] = description

    if template:
        cdict['template'] = LayoutTemplateFile(template, content_type=contentType)

    cdict.update(kwargs)

    class_name = 'Layout<%s>'%name

    if class_ is None:
        bases = (Layout,)
    else:
        bases = (class_, Layout)

    newclass = type(str(class_name), bases, cdict)

    # Set up permission mapping for various accessible attributes
    required = {}

    for iface in (provides, ILayout):
        for iname in iface:
            required[iname] = CheckerPublic

    required = {'__call__': CheckerPublic,
                'browserDefault': CheckerPublic,
                'publishTraverse': CheckerPublic}

    # provide the custom provides interface if not allready provided
    if not provides.implementedBy(newclass):
        interface.classImplements(newclass, provides)

    # security checker
    defineChecker(newclass, Checker(required))

    if for_ is not None:
        # register the template
        if name:
            adapter(_context, (newclass,),
                    provides, (interface.Interface, for_, layer), name=name)
        else:
            adapter(_context, (newclass,),
                    provides, (interface.Interface, for_, layer))

        # send ILayoutCreatedEvent event
        if uid:
            _context.action(
                discriminator = ('zojax.layout', uid),
                callable = sendNotification,
                args = (uid, name, interface.Interface, for_, layer, newclass, kwargs),
                order = 99999999)

    if view is not None:
        # register the template
        if name:
            adapter(_context, (newclass,),
                    provides, (view, interface.Interface, layer), name=name)
        else:
            adapter(_context, (newclass,),
                    provides, (view, interface.Interface, layer))

        # send ILayoutCreatedEvent event
        if uid:
            _context.action(
                discriminator = ('zojax.layout', uid),
                callable = sendNotification,
                args = (uid, name, view, interface.Interface, layer, newclass, kwargs),
                order = 99999999)


class LayoutCreatedEvent(object):
    interface.implements(ILayoutCreatedEvent)

    def __init__(self, uid, name, view, 
                 context, layer, layoutclass, keywords):
        self.uid = uid
        self.name = name
        self.view = view
        self.context = context
        self.layer = layer
        self.layoutclass = layoutclass
        self.keywords = keywords


def sendNotification(uid, name, view, context, layer, layoutclass, keywords):
    event.notify(LayoutCreatedEvent(
            uid, name, view, context, layer, layoutclass, keywords))


# pagelet directive
def pageletDirective(
    _context, permission, name=u'', class_=None, for_=interface.Interface,
    layer=IDefaultBrowserLayer, provides=[IPagelet,],
    allowed_interface=[], allowed_attributes=[],
    template=u'', layout=u'', **kwargs):

    # Security map dictionary
    required = {}

    # Get the permission; mainly to correctly handle CheckerPublic.
    if permission == 'zope.Public':
        permission = CheckerPublic

    # Make sure that the template exists
    if template:
        template = os.path.abspath(str(_context.path(template)))
        if not os.path.isfile(template):
            raise ConfigurationError("No such file", template)
        kwargs['template'] = ViewPageTemplateFile(template)

    # Build a new class that we can use different permission settings if we
    # use the class more then once.
    cdict = {}
    cdict.update(kwargs)
    cdict['__name__'] = name
    cdict['layoutname'] = layout

    if class_ is not None:
        if issubclass(class_, BrowserPagelet):
            bases = (class_,)
        else:
            bases = (class_, BrowserPagelet)
    else:
        bases = (BrowserPagelet,)

    new_class = type('PageletClass from %s'%class_, bases, cdict)

    # check name
    if not name:
        for iface in provides:
            # allow register nameless pagelet as IPagelet
            if iface is IPagelet:
                continue

            if iface.isOrExtends(IBrowserPublisher):
                raise ConfigurationError(
                    "You can't register nameless pagelet, "\
                    "interface '%s' is or extends IBrowserPublisher"%iface)

    # add IPagelet to provides
    if name:
        inProvides = False
        for iface in provides:
            if IPagelet.isOrExtends(iface) and not IPageletType.providedBy(iface):
                inProvides = True

        if not inProvides:
            provides.append(IPagelet)

    # prepare allowed interfaces and attributes
    allowed_interface.extend(provides)
    if IPagelet not in provides:
        allowed_interface.append(IPagelet)

    allowed_attributes.extend(kwargs.keys())
    allowed_attributes.extend(('__call__', 'browserDefault',
                               'update', 'render', 'publishTraverse'))

    # Set up permission mapping for various accessible attributes
    _handle_allowed_interface(
        _context, allowed_interface, permission, required)
    _handle_allowed_attributes(
        _context, allowed_attributes, permission, required)

    # Register the interfaces.
    _handle_for(_context, for_)

    # provide the custom provides interface if not allready provided
    for iface in provides:
        if not iface.implementedBy(new_class):
            interface.classImplements(new_class, iface)

    # Create the security checker for the new class
    defineChecker(new_class, Checker(required))

    # register pagelet
    _context.action(
        discriminator = ('zojax.layout:registerPagelets', new_class),
        callable = registerPagelets,
        args = (for_, layer, new_class, provides, name, _context.info))


def registerPagelets(for_, layer, newClass, provides, name, info):
    for iface in provides:
        if IPageletType.providedBy(iface):
            handler('registerAdapter', newClass, (for_, layer), iface, '', info)
        else:
            handler('registerAdapter', newClass, (for_, layer), iface, name, info)


def _handle_allowed_interface(
    _context, allowed_interface, permission, required):
    # Allow access for all names defined by named interfaces 
    if allowed_interface:
        for i in allowed_interface:
            _context.action(
                discriminator = None,
                callable = provideInterface,
                args = (None, i))

            for name in i:
                required[name] = permission

def _handle_allowed_attributes(
    _context, allowed_attributes, permission, required):

    # Allow access for all named attributes 
    if allowed_attributes:
        for name in allowed_attributes:
            required[name] = permission

def _handle_for(_context, for_):
    if for_ is not None:
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = ('', for_))
