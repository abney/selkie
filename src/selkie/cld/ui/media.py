##  @package seal.cld.ui.media
#   MediaSelector and Transcriber.

import os
from seal.app.html import *
from seal.cld.db.disk import writer
from seal.cld.ui.audio import WaveData
from seal.cld.ui.video import VideoData


##  Media types that are supported by browsers.

MediaTypes = {'mp3': 'audio',
              'mp4': 'video',
              'wav': 'audio'}

##  The media suffixes that are supported by browsers.

def media_suffixes ():
    return sorted(MediaTypes.keys())


#--  Media element  ------------------------------------------------------------

##  Adds a media player to the page.

def Media (page, media):

    if media:
        suffix = media.get_default()
        fname = 'data.' + suffix
        av = MediaTypes[suffix]
        if av == 'audio':
            Audio(page, fname, htmlid='mediaPlayer')
        elif av == 'video':
            Video(page, fname, htmlid='mediaPlayer', style='width:720;height:405')
        else:
            raise Exception('Bad entry in MediaTypes: %s' % suffix)
    else:
        B(P(page), 'No Media')


#--  MediaSelector  ------------------------------------------------------------

##  A media selector.

class MediaSelector (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'root',
                 'select': 'select',
                 'upload': 'upload'}

    ##  Main entry point.

    def root (self):
        corpus = self.file.corpus()  # self.file: Text
        files = corpus.media.files()

        title = 'Select Media File'
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        bar = MenuBar(page)
        Button(bar, '<<', '../')
        H1(page, title)

        table = Table(page, htmlclass='tabbing')
        row = Header(table)
        String(row, 'File')
        String(row, 'Text')
        String(row, '')
        for (i,f) in enumerate(files):
            row = Row(table)
            TT(row, f.filename())
            #NBSP(row)
            String(row, f.text or '-')
            Button(row, 'Select', 'select.%d' % i)
        row = Row(table)
        I(row, 'upload a new file')
        String(row, '-')
        Button(row, 'Select', 'select.%d' % len(files))
        return page

    ##  Modify the media file to point to the selected media.

    def select (self, i):
        i = int(i)
        text = self.file
        corpus = text.corpus()
        files = corpus.media.files()
        if i == len(files):
            return self.uploader()
        else:
            media = text.media
            with writer(media):
                media.set(files[i].username, files[i].fname)
            return Redirect('../')

    ##  Returns an uploader page.

    def uploader (self):
        corpus = self.file.corpus()  # self.file: Text
        files = corpus.media.files()

        title = 'Upload Media file'
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        bar = MenuBar(page)
        Button(bar, '<<', '../')
        H1(page, title)

        table = Table(page, htmlclass='tabbing')
        row = Header(table)
        String(row, 'File')
        String(row, 'Text')
        for (i,f) in enumerate(files):
            row = Row(table)
            TT(row, f.filename())
            #NBSP(row)
            String(row, f.text or '-')

        BR(page)

        form = Form(page, 'upload')
        table = Table(form, htmlclass='tabbing')
        cell = Cell(Row(table))
        String(cell, 'Name on server:')
        cell = Cell(Row(table))
        TT(cell, self.file.username() + '/')
        TextBox(cell, 'fname')
        cell = Cell(Row(table))
        BrowseButton(cell, 'contents')
        cell = Cell(Row(table))
        Submit(cell, 'Submit')
        Submit(cell, 'Abort')
        return page

    ##  Callback from the uploader page.

    def upload (self, fname=None, contents=None, submit=None):
        if submit == 'Submit' and fname and contents:
            corpus = self.file.corpus()
            user = self.user()
            corpus.media.add(user, fname, contents)
            media = self.file.media
            with writer(media):
                media.set(user.name(), fname)
        return Redirect('../')


#--  Transcriber  --------------------------------------------------------------

##  A transcriber.
#   self.file is the value of text.xscript, which is a Transcription instance
#   (module seal.cld.corpus.transcript).

class Transcriber (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'edit',
                 'edit': 'edit',
                 'data': 'data',
                 #'create_snippet': 'create_snippet',
                 #'save_snippet': 'save_snippet',
                 'set_duration': 'set_duration',
                 'set_clip': 'set_clip',
                 'set_text': 'set_text',
                 'set_para': 'set_para',
                 'nudge': 'nudge',
                 'cut': 'cut',
                 'merge': 'merge'}

#                 'new_clip': 'new_clip'}

    ##  Returns the contents of the media file.
    
    def data (self, type):
        media = self.file.media()
        media.check_permission('read')
        return media.data(type)

    ##  Main entry point.

    def edit (self, clip0=0, clips_per_page=10):
        xscript = self.file
        media = xscript.media()
        title = 'Media %s' % self.file.id()

        # Adjust nclips, set end

        clip0 = int(clip0)
        clips_per_page = int(clips_per_page)

        # Generate page

        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '../../')
        #if self.page.trans:
        #    Button(menu, 'Edit Translation', '../para/edit')
        #else:
        Button(menu, 'Text', '../edit')
        Button(menu, 'Edit Metadata', '../meta')

        H1(page, title)

        Media(page, media)

        BR(page)

        table = Table(page, htmlclass='grid')
        
        Cell(Row(table), style='text-align:center', htmlid='navCell')
        Button(Cell(Row(table), style='text-align:center'), '\u25b3', None, htmlid='prevButton')

        # create inner table
        Table(Cell(Row(table)), htmlid='clipTable')

#         for i in range(offset, end):
#             clip = clips[i]
#             if i >= len(trans):
#                 ascii = unicode = ''
#             else:
#                 ascii = str(trans[i])
#                 unicode = trans[i].unicode()
#             row = Row(table)
#             String(Cell(row, htmlclass='segno'), str(i))
#             p = P(Cell(row),
#                   htmlclass='transcription',
#                   data_index=i,
#                   data_ascii=ascii,
#                   data_start=clip.start,
#                   data_end=clip.end)
#             String(p, unicode)

        Button(Cell(Row(table), style='text-align:center'), '\u25bd', None, htmlid='nextButton')

        page.add_stylesheet('XScript')
        page.add_import('XScript')
        script = Script(page)
        script.write('new XScript(%d,%d);\r\n' % (clip0, clips_per_page))

        return page

#     def create_snippet (self, index, start, end):
#         index = int(index)
#         start = float(start)
#         end = float(end)
#         transcription = self.file
#         if index != len(transcription.clips):
#             raise KeyError('Bad index for create_snippet')
#         with transcription.writer() as w:
#             w.new_clip(start, end)
#         return Text(self)

    ##  Ajax callback to set the duration of the transcript.
    #   This is a kludge for the lack of a Python library that can determine the
    #   duration of an MP3 file.

    def set_duration (self, clip0, clips_per_page, duration):
        clip0 = int(clip0)
        clips_per_page = int(clips_per_page)
        duration = float(duration)
        xscript = self.file
        with writer(xscript):
            xscript.set_duration(duration)
        return Text(xscript.json(clip0, clips_per_page))

    ##  Ajax callback to set the start and end time of a clip.

    def set_clip (self, index, start, end, clip0, clips_per_page):
        index = int(index)
        start = float(start)
        end = float(end)
        clip0 = int(clip0)
        clips_per_page = int(clips_per_page)
        xscript = self.file
        with writer(xscript):
            xscript.set_clip(index, start, end)
        spec = xscript.json(clip0, clips_per_page)
        return Text(spec)

    ##  Ajax callback to nudge a boundary.  The index is the index of the
    #   clip whose right boundary is being nudged.
    #   Response is the actual value
    #   it was nudged to.  Cannot nudge full amount to the right if we are
    #   at the end of the recording or if the following clip would become
    #   too short.  Cannot nudge full amount to the left if the current
    #   clip would become too short.

    def nudge (self, index, delta):
        xscript = self.file
        index = int(index)
        delta = float(delta)
        actual = xscript.nudge(index, delta)
        return Text(str(actual))

    ##  Ajax callback to cut a clip in two.

    def cut (self, index, t, clip0, clips_per_page):
        xscript = self.file
        index = int(index)
        t = float(t)
        clip0 = int(clip0)
        clips_per_page = int(clips_per_page)
        xscript.cut(index, t)
        return Text(xscript.json(clip0, clips_per_page))

    ##  Ajax callback to merge clip i with clip i+1.

    def merge (self, index, clip0, clips_per_page):
        xscript = self.file
        index = int(index)
        clip0 = int(clip0)
        clips_per_page = int(clips_per_page)
        xscript.merge(index)
        return Text(xscript.json(clip0, clips_per_page))

    ##  Ajax callback to set the contents of the transcription for a clip.

    def set_text (self, index, text):
        index = int(index)
        xscript = self.file
        with writer(xscript):
            xscript.set_text(index, text)
        rom = xscript.romanization()
        return Text(rom.decode(text))

    ##  Ajax callback to set the value of the initial-clip flag for a given clip.

    def set_para (self, index, value):
        index = int(index)
        xscript = self.file
        with writer(xscript):
            xscript.set_para(index, value)
        return Text()

#     def new_clip (self, end, clips_per_page):
#         end = float(end)
#         clips_per_page = int(clips_per_page)
#         xscript = self.file
#         with xscript.writer() as w:
#             w.new_clip(end)
#         return self.json(len(xscript.clips), clips_per_page)
