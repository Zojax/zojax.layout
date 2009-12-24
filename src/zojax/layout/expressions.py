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
import re
from chameleon.core import types
from chameleon.zpt import expressions

from tales import PageletExpression


class PageletTraverser(PageletExpression):

    __call__ = PageletExpression.render


class PageletTranslator(expressions.ExpressionTranslator):

    symbol = '_get_zojax_pagelet'
    pagelet_traverser = PageletTraverser()

    def translate(self, string, escape=None):
        value = types.value("%s(context, request, view, '%s')" % \
                                (self.symbol, string))
        value.symbol_mapping[self.symbol] = self.pagelet_traverser
        return value
