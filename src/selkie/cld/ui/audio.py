##  @package seal.cld.ui.audio
#   Audio files.

from seal.app.html import *


#--  WaveData  -----------------------------------------------------------------

##  If the source is a string, returns a RawFile representing the contents of the
#   named file.  If the source is a Clip, returns Data representing the contents
#   of the clip.

def WaveData (source):
    if isinstance(source, str):
        return RawFile(source, 'wav')
    elif isinstance(source, Clip):
        data = Data(None, 'wav') # 'wav' is mime type
        source.save_wave(data)
        return data
    else:
        raise HttpException('Bad wave source: %s' % repr(source))


#--  Audio Editor  -------------------------------------------------------------

##  Add a checkbox to the parent (web page element).

def checkbox (parent, selected):
    if selected: s = ' checked'
    else: s = ''
    parent.write('<input class="checkbox" type="checkbox"%s>' % s)


##  An audio editor HTML directory.

class AudioEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'edit',
                 'edit': 'edit',
                 'clip': 'clip',
                 'savetrans': 'savetrans',
                 'tunit': 'tunit'}

    ##  Constructor.

    def __init__ (self, parent, audio):
        HtmlDirectory.__init__(self, parent)

        ##  The File, of type AudioDirectory.
        self.audio = audio
    
    ##  Main entry point.

    def edit (self, offset=0, nclips=20):
        clips = self.audio.clips
        trans = self.audio.transcript
        rom = trans.romanization()

        # Adjust offset, nclips

        offset = int(offset)
        nclips = int(nclips)

        if offset > nclips: offset = nclips
        if offset + nclips > len(clips):
            nclips = len(clips) - offset

        end = offset + nclips

        # Set prev, next, title

        if offset > 0:
            prev = offset - nclips
            if prev < 0: prev = 0
            prev = 'edit.%d' % prev
        else:
            prev = None

        next = end
        if next >= len(clips): next = None
        else: next = 'edit.%d' % next

        title = 'Audio %s: %d-%d' % (self.audio.id(), offset, end-1)

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

        table = Table(page, htmlclass='audioTable')
        
        Button(Cell(Row(table), colspan=2, style='text-align:center'), 'Previous', prev)

        for i in range(offset, end):
            if i >= len(clips): break
            row = Row(table)
            String(Cell(row, htmlclass='segno'), str(i))
            Audio(Cell(row, htmlclass='audio'), 'clip.' + str(i))
            p = P(Cell(row, htmlclass='trans'), htmlclass='transcription')
            p.add(trans[i].unicode())

        Button(Cell(Row(table), colspan=2, style='text-align:center'), 'Next', next)

        page.add_import('transcriber')
        page.add_stylesheet('transcriber')
        script = Script(page)
        # this assumes that the transcript is non-empty
        script.write('Transcriber(%d,[' % offset)
        first = True
        for block in trans[offset:end]:
            if first: first = False
            else: script.write(',')
            script.write(repr(str(block))) # repr so it has quotes
        script.write(']);\n')

        return page

    ##  Returns the contents of the i-th clip as WaveData.

    def clip (self, i):
        i = int(i)
        clip = self.audio.get_clip(i)
        return WaveData(clip)

#         data = Data(None, 'wav')
#         clip.save_wave(data)
#         return data

    ##  Callback to save a transcription unit.

    def savetrans (self, index=None, text=None):
        index = int(index)
        self.audio.transcript.set(index, text)
        rom = self.audio.text().romanization()
        return Text(decode(text, rom=rom))

    ##  Return an editor for the clips constituting the i-th plaintext unit.

    def tunit (self, i=None):
        i = int(i)
        trans = TranslationUnits(self.audio.transcript)
        block = trans[i]
        (j,k) = block.orig()
        return self.edit(j, k-j)
