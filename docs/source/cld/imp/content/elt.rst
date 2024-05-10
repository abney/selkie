
UI Elements
***********

Element class
-------------

The class Element is the base class for the following.  Every
element has the member contents, which is a list of content items.
The Element also provides
two methods: add is used to add items to the
contents, and the default __iter__ method simply yields each
item in contents.

When defining an element, one may override the __iter__
method, but one should be sure to include any
sub-elements in contents so that they will be found by
iterelements.
When overriding the __iter__ method, one should remember that
strings of class HTML are rendered as they stand, whereas
regular strings will be escaped before rendering.

Spans
-----

Font changes and headings
.........................

There are elements corresponding to the font-changing tags B,
I, and TT, as well as the headers H1 to H6::

   >>> e = B(page, 'test 1 2 3')
   >>> print(e)
   <b>test 1 2 3</b>

They accept multiple arguments::

   >>> e = H1(page, 'The ', I('Titanic'))
   >>> print(e)
   <h1>The <i>Titanic</i></h1>

Spacers
.......

BR is not a function but a variable::

   >>> print(BR)
   <br />

NBSP is a tag, but it also can be called as a function
taking an optional argument that indicates the
number of spaces::

   >>> print(NBSP)
   &nbsp;
   >>> e = NBSP(2)
   >>> print(e)
   &nbsp;&nbsp;

Blocks
------

Paragraphs
..........

P produces a paragraph.  It accepts any number of arguments.

Pre
...........
Pre produces a pre-formatted block.  It accepts a single
argument, and an optional width parameter.
Note that the restriction to a single item is not limiting: one can
pass in a list::

   >>> e = Pre(['hi there\r\n', 'foo bar\r\n'])
   >>> print(e)
   <pre class="source">
   hi there
   foo bar
   </pre>

Lists
.....

UL takes multiple arguments.  Each is rendered as a list item.
One may also create a UL and add items one at a time::

   >>> e = UL('Lather', 'Rinse', 'Repeat')
   >>> print(e)
   <ul>
   <li>Lather</li>
   <li>Rinse</li>
   <li>Repeat</li>
   </ul>

Additional items can be added using the add method.

Stack
.....

Stack is not a standard HTML element.  It takes multiple
arguments, and connects them with BRs::

   >>> e = Stack('Hi there', 'A test')
   >>> print(e)
   Hi there<br />
   A test

Table
.....

One can create a table all at once, or add a row at a time, or mix the
two modes::

   >>> e = Table(Row('hi', 'there'), Row('foo', 'bar'))
   >>> print(e)
   <table class="display">
   <tr><td>hi</td><td>there</td></tr>
   <tr><td>foo</td><td>bar</td></tr>
   </table>

One may also use Header instead of Row.  A Header is
a row in which each cell is wrapped in th instead of td.
Additional rows can be added using the add method.

To change the rowspan or the colspan of a cell, one must
create an explicit Cell object.  For example::

   >>> t = Table(Row('hi', 'there'), Row(Cell('boo', colspan=2)))
   >>> print(t)
   <table class="display">
   <tr><td>hi</td><td>there</td></tr>
   <tr><td colspan="2">boo</td></tr>
   </table>

Navigation
----------

Link
....

A Link represents an HTML anchor.  It takes two arguments: the
text and the URL::

   >>> e = Link('go there', '/foo')
   >>> print(e)
   <a href="/foo">go there</a>

An optional third argument is the target.  Typical values are
'_top' or '_blank'.

Button
......

The Button constructor takes two arguments:
the text that appears on the button, and the URL to be visited if the
button is clicked on.  If the URL is None, the button is
disabled.  An optional argument is target, which specifies the
window that the URL should be opened in.

Path
....

A Path is a sequence of links representing the path to the
current directory.  It takes an HtmlDirectory as argument.  For example::

   >>> from seal.examples.ui import RootDirectory
   >>> root = RootDirectory()
   >>> text = root(parse_request('doc.10/page.3/text'))
   >>> page = text.__parent__
   >>> print(Path(page))
   <div class="path">
   <a href="/">top</a> > <a href="/doc.10/">doc.10</a> > page.3
   </div>

Menubar
.......

A Menubar is a div created from a list of buttons.

Forms
-----

Forms comprise a number of different elements, so I put them in a
section of their own.

Form element
............

The Form constructor takes a single argument,
which is the callback URL.  The information in the form will be
POSTed to the callback URL when the form is submitted::

   >>> e = Form('do_it')
   >>> e.add(Submit('Go!'))
   >>> print(e)
   <form enctype="multipart/form-data" action="do_it" method="post">
   <input type="submit" name="submit" value="Go!"/>
   </form>

Each form element generates a key-value pair in the POST data.
Each of the following constructors takes a key as its first argument.

Check boxes
...........

The CheckBoxes constructor takes two arguments: a key and a list
of values.  One checkbox is generated for each value.  An optional
argument is selected, which may be a value or a list of values
that should initially be checked.  By default, no boxes are checked.
Another optional argument is separator, which specifies
what should be placed between each pair of adjacent check boxes.  By
default, it is a single space.

Dropdown
........

The Dropdown class represents a dropdown list.  The constructor
takes two arguments: key and values.  The key identifies this
piece of information in the form.  Values is a list of
possible values.  The initially selected value is the first in the
list.  An optional argument selected allows one to specify one of
the other values as the initially selected value.

File upload
...........

A File element supports file upload.  In the form, it takes the
form of a browse button that allows a user to select a file.  In the
POST information, the entire contents of the file, as a string,
is the value of key associated with the File element.

Here is an example::

   class FileTest (HtmlDirectory):
   
       def getitem (self, name, args, kargs):
           if name == '': return self.test()
           elif name == 'upload': return self.upload(**kargs)
   
       def test (self):
           form = Form('upload')
           form.add(Table(Row('File:', File('file')),
                          Row(Cell(Submit('Submit'), colspan=2))))
           p = HtmlPage(title='File Test')
           p.add(form)
           return p
   
       def upload (self, file='', submit=''):
           p = HtmlPage(title='File Contents')
           p.add(Pre(file))
           return p

To run it::

   >>> from seal.wsgi import App, run
   >>> from seal.examples.ui import FileTest
   >>> run(App(FileTest()))

Then visit http://localhost:8000/.

Hidden
......

A Hidden element can be used to pass information from the code
that creates the form to the code that receives the resulting POST.
The constructor takes two arguments: key and value.

Not editable
............

The NotEditable constructor takes two arguments, key and value.
Like a hidden element, the key-value pair is included in the POST.
But unlike a hidden element, the value is displayed -- though it is not
editable.

Radio buttons
.............

The RadioButtons constructor takes two arguments: a key and a
list of values.  Each value generates a radio button.  An optional
argument is selected, which contains one of the values.  By
default, none of the boxes is initially selected.  Another optional
argument is separator, which specifies what should be between
each pair of adjacent radio buttons.  By default, it is a single space.

Submit
......

A Submit button constructor takes two optional arguments.  The
first is the <i>value,</i> which is the text to display on the button.
It defaults to 'Submit'.
The second is the <i>name,</i> which is the key in the key-value pair
that is generated by pressing the button.  It defaults to 'action'.

Text box
........

The Textbox constructor takes two arguments: key and value.  The
value provides the initial text in the box.  If omitted, it defaults
to the empty string.  An optional argument is size, whose value
is an integer representing the width of the text box in characters.

Text area
.........

The Textarea constructor is just like Textbox, except that
the size parameter expects a pair of numbers, representing the
number of rows and columns in the box.

Example
.......

The class FormTest illustrates the use of a form.  It is defined
as follows::

   class FormTest (HtmlDirectory):
   
       def getitem (self, name, args, kargs):
           if name == '': return Redirect('form.42')
           elif name == 'form': return self.form(*args)
           elif name == 'update': return self.update(**kargs)
   
       def form (self, id):
           t = Table(Row('Name:', Textbox('name')),
                     Row('Password:', Password('passwd')),
                     Row('Sex:', RadioButtons('sex',
                                              ['Female', 'Male'])),
                     Row('Income:', Dropdown('inc',
                                             ['', 'Some', 'Lots'])),
                     Row('Pets:', CheckBoxes('pets',
                                             ['Dog', 'Cat', 'Python'])))
           form = Form('update')
           form.add(t)
           form.add(Hidden('id', id))
           form.add([Submit('Submit'), NBSP(), Submit('Cancel')])
   
           p = HtmlPage(title='Form Example')
           p.add(H1('Form'))
           p.add(form)
           return p
   
       def update (self, id='', name='', passwd='', sex='',
                   inc='', pets=[], submit=''):
           p = HtmlPage(title='Update')
           p.add(Table(Row('Id:', id),
                       Row('Name:', name),
                       Row('Password:', passwd),
                       Row('Sex:', sex),
                       Row('Income:', inc),
                       Row('Pets:', ', '.join(pets)),
                       Row('Submit:', submit)))
           return p

Note the line ``getlist('pets')`` in update.  With check
boxes, multiple boxes may be checked, yielding multiple values for "pets".

To run the test::

   >>> d = FormTest()
   >>> d.run()

Visit http://localhost:8000/.  The browser will redirect to
form.42.  Fill in some information and click either Submit
or Cancel.  You should get a web page showing what you entered.

Widgets
-------

A widget is an element that does something.  In particular:

 * it contains Javascript code in addition to HTML,

 * it has its own stylesheet,

 * it can be addressed in a URL and handles page requests.

Here is a simplified example::

   class Foo (Widget):
   
       __pages__ = {'doit': 'doit'}
   
       def __init__ (self, parent, **kwargs):
           Widget.__init__(self, parent, **kwargs)
           Div(self, htmlid='foodiv')
           script = Script(self)
           String(script, "new Foo('%s');\r\n" % self.callback_prefix())
   
       def doit (self, x=None):
           resp = Text(self)
           resp.write(str(x + 2))
           return resp

In addition to the Widget definition, one must also provide
files called Foo.js and Foo.css in the Seal data
directory.  The script in the widget definition provides
initialization code for the Javascript class Foo defined in
Foo.js.

The widget behaves like a directory, accessed by name.
For example, the code for the page containing the Foo widget
might contain::

   def edit (self):
       page = HtmlPage()
       Foo(page, name='foo1')
       return page

Then a URL addressing the widget's doit callback would have the
form::

   /path/mypage/foo1/doit.42

