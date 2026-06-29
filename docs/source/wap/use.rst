
Defining an application
=======================

A minimal example
-----------------

The minimum application is just a **start function** that uses the WAP UI to
create a web page::
  
    from selkie.wap import document
    
    def foo (server):
        document.write('Hello, world!')
    
(The parameter ``server`` is not used in this example, but the
start function must accept it.)
If the above code is in the file ``test.py``, one may invoke it by doing::

    $ python -m selkie.wap test.foo

Instead of calling ``selkie.wap`` from the command line, one may pass
the start function to ``selkie.wap.exec_app``, as in the example in
the Introduction.

Elements
--------

In software, an HTML is represented by the Document Object Model
(DOM), in which a web page consists of Elements. Wap provides an
Element class. Here is an example of creating a web page with some
structure::

    from selkie.wap import Element

    def MyPage (Element):
    
        def __init__ (self, server):
            Element.__init__(self)
            self.server = server
            p = self.P()
            p.write('Hi there')
            ul = self.UL()
            li = ul.LI()
            li.write('Item 1')
            li = ul.LI()
            li.write('Item 2')
    	   
If that is the contents of ``test2.py``, one invokes it as::

    $ python -m selkie.wap test2.MyPage

