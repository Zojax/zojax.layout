================
Template layouts
================

Layouts is different way of building skin templates without METAL.

We need load zcml file

  >>> import zojax.layout
  >>> from zope.configuration import xmlconfig
  >>> context = xmlconfig.file('meta.zcml', zojax.layout)

  >>> import os, tempfile
  >>> from zope import interface, component
  >>> from zojax.layout import tests, interfaces
  >>> from zojax.layout.pagelet import BrowserPagelet

Let's define main layout for our skin, it like 'page' macros from basicskin or 
rotterdam. It will contains <html>, <head> and <body> tags. 
It's like main_template in CMF or 'page' macro in basicskin/rotterdam

  >>> temp_dir = tempfile.mkdtemp()
  >>> layoutportal = os.path.join(temp_dir, 'layoutportal.pt')
  >>> open(layoutportal, 'w').write(
  ... '''<html>
  ...   <body>
  ...      <div id="portal" tal:content="structure view/render">
  ...      </div>
  ...   </body>
  ... </html>''')

Let's define 'portal' layout

  >>> context = xmlconfig.string("""
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:layout
  ...     name="portal"
  ...     for="zope.app.component.interfaces.ISite"
  ...     template="%s" />
  ... </configure>"""%layoutportal, context)

Here another layout.

  >>> layoutworkspace = os.path.join(temp_dir, 'layoutworkspace.pt')
  >>> open(layoutworkspace, 'w').write('''
  ... <div id="workspace" tal:content="structure view/render"></div>''')

  >>> context = xmlconfig.string("""
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:layout
  ...     name="workspace"
  ...     layout="portal"
  ...     for="zope.app.component.interfaces.ISite"
  ...     template="%s" />
  ... </configure>"""%layoutworkspace, context)

You should notice that we used layout="portal" it indicates that 
'workspace' layout uses 'portal' layout as parent. so 'workspace' will be rendered
inside 'portal' layout

Now we need very simple view that uses BrowserPagelet

  >>> class IMyView(interface.Interface):
  ...     pass

  >>> class MyView(BrowserPagelet):
  ...     interface.implements(IMyView)
  ...
  ...     def render(self):
  ...       return self.context.__name__

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> view = MyView(root, request)

It returns context __name__

  >>> view.__call__()
  'root'

By default BrowserPagelet uses layout without name, Let's create one, it will
use 'workspace' layout as parent.

  >>> layoutcontent = os.path.join(temp_dir, 'layoutcontent.pt')
  >>> open(layoutcontent, 'w').write('''
  ... <div id="content" tal:content="structure view/render"></div>''')

  >>> context = xmlconfig.string("""
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:layout
  ...     layout="workspace"
  ...     for="zope.app.component.interfaces.ISite"
  ...     template="%s" />
  ... </configure>"""%layoutcontent, context)

  >>> print view()
  <html>
  <body>
        <div id="portal">
          <div id="workspace">
          <div id="content">root</div>...
     </body>
  </html>

All 3 our layout rendered. view rendered inside nameless layout then in
-> 'workspace' layout -> 'portal' layout

Now let's create several more content objects

  >>> folder1 = tests.Folder()
  >>> root['folder1'] = folder1

  >>> print MyView(folder1, request)()
  <html>
    <body>
      <div id="portal">
        <div id="workspace">
        <div id="content">folder1</div>...
    </body>
  </html>

And another one.

  >>> folder1_1 = tests.Folder()
  >>> root['folder1']['folder1_1'] = folder1_1

  >>> folder1_1_1 = tests.Folder()
  >>> root['folder1']['folder1_1']['folder1_1_1'] = folder1_1_1

  >>> print MyView(folder1_1_1, request)()
  <html>
    <body>
      <div id="portal">
        <div id="workspace">
          <div id="content">folder1_1_1</div>...
    </body>
  </html>

This is all quite easy. Let's use more complex example. For example 
later other developers decide change how portal looks for folder1 object
they want that all folder1 and all it's childs(folder1_1, folder1_1_1) have 
same look.

Let's add '<table>' with couple columns

  >>> layoutcolumns = os.path.join(temp_dir, 'layoutcolumns.pt')
  >>> open(layoutcolumns, 'w').write('''
  ... <table id="columns">
  ...   <tr>
  ...     <td id="column1">Column1</td>
  ...     <td id="column2" tal:content="structure view/render"></td>
  ...     <td id="column3">Column3</td>
  ...   </tr>
  ... </table>''')

We register new layout for different interafce

  >>> context = xmlconfig.string("""
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:layout
  ...     name="workspace"
  ...     layout="portal"
  ...     for="zojax.layout.tests.IFolder1"
  ...     template="%s" />
  ... </configure>"""%layoutcolumns, context)

  >>> interface.directlyProvides(folder1, tests.IFolder1)

  >>> print MyView(folder1, request)()
  <html>
    <body>
      <div id="portal">
        <table id="columns">
          <tr>
            <td id="column1">Column1</td>
            <td id="column2">
              <div id="content">folder1</div>...
            <td id="column3">Column3</td>
          </tr>
        </table>...
    </body>
  </html>

folder1 uses new 'workspace' layout, but what about other folders

  >>> print MyView(folder1_1, request)()
  <html>
    <body>
      <div id="portal">
        <table id="columns">
          <tr>
            <td id="column1">Column1</td>
            <td id="column2">
              <div id="content">folder1_1</div>...
            <td id="column3">Column3</td>
          </tr>
        </table>...
    </body>
  </html>


  >>> print MyView(folder1_1_1, request)()
  <html>
    <body>
      <div id="portal">
        <table id="columns">
          <tr>
            <td id="column1">Column1</td>
            <td id="column2">
              <div id="content">folder1_1_1</div>...
            <td id="column3">Column3</td>
          </tr>
        </table>...
    </body>
  </html>


Now we also change how folder1_1 looks, we can replace nameless layout.
Also we can use nameless layout as parent with layout="."

  >>> layoutcontent1_1 = os.path.join(temp_dir, 'layoutcontent1_1.pt')
  >>> open(layoutcontent1_1, 'w').write('''
  ... <div id="content1_1">
  ...   <h1>Folder1_1</h1>
  ...   <div tal:content="structure view/render"></div>
  ... </div>''')

  >>> context = xmlconfig.string("""
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:layout
  ...     layout="."
  ...     for="zojax.layout.tests.IFolder1_1"
  ...     template="%s" />
  ... </configure>"""%layoutcontent1_1, context)

  >>> interface.directlyProvides(folder1_1, tests.IFolder1_1)
  
  >>> print MyView(folder1_1, request)()
  <html>
    <body>
      <div id="portal">
        <table id="columns">
          <tr>
            <td id="column1">Column1</td>
            <td id="column2">
              <div id="content">
                <div id="content1_1">
                  <h1>Folder1_1</h1>
                  <div>folder1_1</div>
                </div>...
            <td id="column3">Column3</td>
          </tr>
        </table>...
     </body>
  </html>

It still uses nameless layout that we defined for 'root'. 

And same for folder1_1_1

  >>> layoutcontent1_1_1 = os.path.join(temp_dir, 'layoutcontent1_1_1.pt')
  >>> open(layoutcontent1_1_1, 'w').write('''
  ... <div id="content1_1_1">
  ...   <h1>Folder1_1_1</h1>
  ...   <div tal:content="structure view/render"></div>
  ... </div>''')

  >>> context = xmlconfig.string("""
  ... <configure xmlns:zojax="http://namespaces.zope.org/zojax">
  ...   <zojax:layout
  ...     layout="."
  ...     for="zojax.layout.tests.IFolder1_1_1"
  ...     template="%s" />
  ... </configure>"""%layoutcontent1_1_1, context)

  >>> interface.directlyProvides(folder1_1_1, tests.IFolder1_1_1)

  >>> print MyView(folder1_1_1, request)()
  <html>
    <body>
      <div id="portal">
        <table id="columns">
          <tr>
            <td id="column1">Column1</td>
            <td id="column2">
              <div id="content">
                <div id="content1_1">
                  <h1>Folder1_1</h1>
                  <div>
                    <div id="content1_1_1">
                      <h1>Folder1_1_1</h1>
                      <div>folder1_1_1</div>...
            <td id="column3">Column3</td>
          </tr>
        </table>...
    </body>
  </html>
