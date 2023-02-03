##  @package seal.cld.ui.course
#   Interface to Course File.

from seal.app.html import *
from seal.cld.corpus.course import Drill


# class CourseEditor (Editor):
# 
#     __pages__ = {'': 'view',
#                  'view': 'view',
#                  'edit': 'edit',
#                  'lesson': 'lesson'}
# 
#     def __init__ (self, parent, course):
#         Editor.__init__(self, parent)
#         self.course = course
# 
#     def view (self):
#         page = HtmlPage(self, title='Course')
#         PathWithLogin(page)
#         bar = MenuBar(page)
#         Button(bar, 'Edit', 'edit')
#         if self.course:
#             ul = UL(page)
#             for lesson in self.course:
#                 Link(LI(ul), lesson.title, 'lesson.%d' % lesson.index)
#         else:
#             I(P(page), 'Empty course')
#         return page
# 
#     def edit (self):
#         if self.course:
#             page = HtmlPage(self, title='Course')
#             PathWithLogin(page)
#             bar = MenuBar(page)
#             Button(bar, 'View', 'view')
#             form = Form(page, 'do_edit')
#             table = Table(form)
#             for (i, lesson) in enumerate(self.course):
#                 row = Row(table)
#                 CheckBox(row, 'lessons*', str(i))
#                 String(row, lesson.title)
#             p = P(form)
#             Submit(p, '+')
#             Submit(p, 'Submit')
#             Submit(p, 'Cancel')
#             return page
#         else:
#             return Redirect('lesson.new/edit')
# 
#     def lesson (self, lesson_id):
#         if lesson_id == 'new': i = None
#         else: i = int(lesson_id)
#         return LessonEditor(self, self.course, i)
# 
# 
# class LessonEditor (Editor):
# 
#     __pages__ = {'edit': 'edit'}
# 
#     def __init__ (self, parent, course, i):
#         Editor.__init__(self, parent)
#         self.course = course
#         if i is None:
#             self.lesson = None
#         else:
#             self.lesson = self.course[i]
# 
#     def edit (self):
#         if self.lesson is not None:
#             page_title = 'Edit Lesson %d' % self.lesson.index
#             lesson_title = self.lesson.title
#             ents_string = '<br/>\r\n'.join(ent.name() for ent in self.lesson)
#         else:
#             page_title = 'New Lesson'
#             lesson_title = ''
#             ents_string = ''
#         page = HtmlPage(self, title=page_title)
#         PathWithLogin(page)
#         H2(page, page_title)
#         form = Form(page, 'do_edit')
#         table = Table(form, htmlclass='tabbing')
#         row = Row(table)
#         String(row, 'Title:')
#         TextBox(row, 'title', lesson_title)
#         row = Row(table)
#         String(row, 'Words:')
#         TextArea(row, 'words', ents_string, size=(20,51))
#         p = P(form)
#         row = Row(table)
#         String(row, '')
#         I(row, 'Write words separated by spaces or newlines')
#         Submit(p, 'Submit')
#         Submit(p, 'Cancel')
#         return page


##  Drill viewer.

class DrillViewer (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'view',
                 'handle_response': 'handle_response'}

    ##  Constructor.

    def __init__ (self, parent, page): # page: Page
        HtmlDirectory.__init__(self, parent, page)

        ##  A Drill object.
        self.drill = Drill(page)

    ##  Main entry point.

    def view (self, word=None, glosses=None, response=None):
        drill = self.drill
        if word is not None:
            drill.advance()
        new_word = drill.form()
        new_glosses = drill.glosses()

        title = 'Drill %s' % self.file.title()
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        bar = MenuBar(page)
        Button(bar, '<<', '../')
        H1(page, title)
        form = Form(page, 'handle_response')
        table = Table(form, htmlclass='tabbing')
        if word is not None:
            row = Row(table)
            String(row, word)
            String(row, response)
            if response in [s.strip() for s in glosses.split(',')]:
                Span(row, 'Right', style='color:green')
            else:
                Span(row, 'Wrong', style='color:red')
            String(row, glosses)
        row = Row(table)
        String(row, new_word)
        cell = Cell(row, colspan=3)
        TextBox(cell, 'response', htmlid='textbox')
        page.focus('textbox')
        Hidden(form, 'word', new_word)
        Hidden(form, 'glosses', new_glosses)
        p = P(form)
        Submit(p, 'Submit')
        Submit(p, 'Done')
        return page

    ##  Callback to handle the user response.

    def handle_response (self, submit=None, word=None, glosses=None, response=None):
        if submit == 'Done':
            return Redirect('../')
        elif submit == 'Submit':
            return self.view(word, glosses, response)
        else:
            raise HttpException('Bad submit reason')
