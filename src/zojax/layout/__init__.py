# This file is necessary to make this directory a package.

# ugly code
try:
    from zope.app.schema import vocabulary
except ImportError:
    pass
