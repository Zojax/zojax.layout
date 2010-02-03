# This file is necessary to make this directory a package.

# ugly code
try:
    from zope.app.schema import vocabulary
except ImportError:
    pass
from zope.exceptions import UserError

from chameleon.core import utils

old_raise_template_exception =  utils.raise_template_exception

def raise_template_exception(source, description, kwargs, exc_info):
    cls, exc, tb = exc_info
    if issubclass(cls, UserError):
        raise cls, exc, tb
    return old_raise_template_exception(source, description, kwargs, exc_info)

utils.raise_template_exception = raise_template_exception