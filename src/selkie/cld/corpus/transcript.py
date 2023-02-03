##  @package seal.cld.corpus.transcript
#   Class Transcription and supporting classes.

from seal.core.io import redirect
from seal.core.misc import quoted
from seal.cld.db.disk import writer
from seal.cld.db.file import File
from seal.cld.db.dir import Structure
from seal.cld.corpus.token import TokenFile


#--  ClipsFile  ----------------------------------------------------------------

##  A snippet.

class Clip (object):
    
    ##  Constructor.

    def __init__ (self, start, end):

        ##  The start time.
        self.start = start

        ##  The end time.
        self.end = end

    ## String representation.

    def __repr__ (self):
        return '<Clip %f %f>' % (self.start, self.end)


##  A collection of snippets.

class ClipsFile (File):

    ##  Read the contents from an open file.

    def __read__ (self, f):
        self._clips = []
        for line in f:
            (start, end) = line.rstrip('\r\n').split('\t')
            start = float(start)
            end = float(end)
            self._clips.append(Clip(start, end))

    ##  Write the contents to an open file.

    def __write__ (self, f):
        for clip in self._clips:
            f.write(str(clip.start))
            f.write('\t')
            f.write(str(clip.end))
            f.write('\n')

    ##  The number of clips.

    def __len__ (self):
        self.require_load()
        return self._clips.__len__()

    ##  Get the i-th clip.

    def __getitem__ (self, i):
        self.require_load()
        return self._clips.__getitem__(i)

    ##  Iterate over clips.

    def __iter__ (self):
        self.require_load()
        return self._clips.__iter__()

    ##  Create a new clip.

    def new_clip (self, start, end):
        with writer(self):
            self.modified()
            self._clips.append(Clip(start, end))

    ##  Insert a clip.

    def insert_clip (self, i, start, end):
        with writer(self):
            self.modified()
            self._clips[i:i] = [Clip(start, end)]

    ##  Change start and end times of a clip.

    def set_clip (self, i, start, end):
        with writer(self):
            self.modified()
            clip = self._clips[i]
            clip.start = start
            clip.end = end

    ##  Delete a clip.

    def delete_clip (self, i):
        with writer(self):
            del self._clips[i]

    ##  Nudge the boundary between clip i and clip i+1.
    #   Return value is the new end value, which might not be the requested value.

    def nudge (self, i, delta):
        with writer(self):
            clip = self._clips[i]
            b = clip.end
            if i + 1 >= len(self._clips): return b
            nxt = self._clips[i+1]
            if delta < 0:
                # clip minimum length is 1/4 sec
                bmin = clip.start + 0.25
                if b <= bmin: return b
                b += delta
                if b < bmin: b = bmin
            elif delta > 0:
                bmax = nxt.end - 0.25
                if b >= bmax: return b
                b += delta
                if b > bmax: b = bmax
            self.modified()
            clip.end = b
            nxt.start = b
            return b

    ##  Cut clip i into two pieces at boundary position t.
    #   It may adjust b to assure that the two pieces are at least 1/2 sec long.
    #   If the full clip is less than 1 sec long, it will refuse to cut.
    #   Return value is boolean indicating whether the cut took place.

    def cut (self, i, t):
        with writer(self):
            clip = self._clips[i]
            bmin = clip.start + 0.5
            bmax = clip.end - 0.5
            if bmin > bmax: return False
            if t < bmin: t = bmin
            elif t > bmax: t = bmax
            self.modified()
            self._clips[i+1:i+1] = [Clip(t, clip.end)]
            clip.end = t
            return True

    ##  Merge clip i and clip i+1.  Error if either clip does not exist.

    def merge (self, i):
        with writer(self):
            if i < 0 or i+1 >= len(self._clips):
                raise KeyError('Bad index for merge: %s' % i)
            clip = self._clips[i]
            nxt = self._clips[i+1]
            self.modified()
            clip.end = nxt.end
            del self._clips[i+1]


#--  ParagraphFile  ------------------------------------------------------------

##  An array of flags, indicating which clips are initial.
#   In the plaintext version, an initial clip and following non-initial clips
#   are pasted together to make a translation unit.

class ParagraphFile (File):

    ##  Read contents from an open file.

    def __read__ (self, f):
        self._flags = []
        for line in f:
            line = line.rstrip()
            # legacy
            if line == '1': line = 'S'
            elif line == '0': line = 'W'
            self._flags.append(line)

    ##  Write contents to an open file.

    def __write__ (self, f):
        for v in self._flags:
            f.write(v)
            f.write('\n')

    ##  Fetch the flag for the i-th clip.

    def __getitem__ (self, i):
        self.require_load()
        return self._flags.__getitem__(i)

    ##  Set the flag for the i-th clip.

    def __setitem__ (self, i, v):
        with writer(self):
            self.modified()
            lst = self._flags
            while i >= len(lst):
                lst.append('W')
            lst[i] = v

    ##  Delete the i-th flag.

    def __delitem__ (self, i):
        with writer(self):
            self.modified()
            del self._flags[i]

    ##  Insert a flag.

    def insert (self, i, v):
        with writer(self):
            self.modified()
            self._flags[i:i] = [v]

    ##  Append a flag at the end.

    def append (self, v):
        with writer(self):
            self.modified()
            self._flags.append(v)


#--  Transcription  ------------------------------------------------------------

##  A transcription, consisting of a transcript (TokenFile), clips, and
#   initial-clip flags.

class Transcription (Structure):

    ##  Map child name to class.
    signature = {'clips': ClipsFile,
                 'transcript': TokenFile,
                 'paras': ParagraphFile}

    ##  Constructor.

    def __init__ (self, *args, **kwargs):
        Structure.__init__(self, *args, **kwargs)
        assert self.parent().__class__.__name__ == 'Text'
        self._wave = None

    ##  The Text that this transcription belongs to.
    def text (self): return self.parent()

    ##  The TID.
    def id (self): return self.text().id()

    ##  The language of the text.
    def language (self): return self.text().language()

    ##  The lexicon for the language.
    def lexicon (self): return self.text().lexicon()

    ##  The text metadata.
    def metadata (self): return self.text().metadata()

    ##  The media file that is being transcribed.
    def media (self): return self.text().media

    ##  The romanization of the transcript.
    def romanization (self): return self.transcript.romanization()

    ##  End of currently last clip; not necessarily the end of the recording.

    def end (self):
        clips = self.clips
        if len(clips) > 0:
            return clips[-1].end
        else:
            return 0.0

    ##  Get the WaveFile for the audio.  Caches it the first time this is called.

    def wave (self):
        if self._wave is None:
            tab = self.parent().media
            if 'wav' not in tab:
                raise HttpException('Missing media file')
            self._wave = WaveFile(tab['wav'])
        return self._wave

    ##  Get the i-th clip.

    def get_clip (self, i):
        clip = self.clips[i]
        return self.wave().get_audio(clip)

    ##  Convert to JSON.

    def json (self, start, clips_per_page):
        end = start + clips_per_page
        nclips = len(self.clips)
        if end > nclips: end = nclips
        with redirect() as f:
            f.write('{"start":"%d","end":"%d","total":"%d","clips":[' %
                    (start, end, nclips))
            for i in range(start, end):
                clip = self.clips[i]
                block = self.transcript[i]
                para = self.paras[i]
                if i > start: f.write(',')
                f.write('{"i":"%d","start":"%f","end":"%f","para":"%s","ascii":%s,"unicode":%s}' % (i, clip.start, clip.end, para, quoted(block.ascii()), quoted(block.unicode())))
            f.write(']}')
        return redirect.output

    ##  Create a new clip.

    def new_clip (self, end):
        with writer(self.clips, self.transcript, self.paras):
            start = self.end()
            self.clips.new_clip(start, end)
            self.transcript.append('')
            self.paras.append('W')

    ##  Set the duration.  The duration is defined to be the end time of the
    #   last clip.  If the last clip ends too soon, add a new clip covering
    #   the remainder of the duration.  (Nothing happens if the current duration
    #   is too short.)

    def set_duration (self, duration):
        if duration > self.end():
            self.new_clip(duration)

#     def insert_clip (self, i, start, end):
#         self.modified = True
#         self.clips_writer.insert_clip(i, start, end)
#         self.transcript_writer.insert(i, '')

    ##  Set the start and end times of the i-th clip.

    def set_clip (self, i, start, end):
        with writer(self.clips, self.transcript, self.paras):
            old_eot = self.end()
            clips = self.clips
            clips.set_clip(i, start, end)
            j = i + 1
            while j < len(clips):
                next = clips[j]
                if next.start > end:
                    clips.insert_clip(j, end, next.start)
                    self.transcript.insert(j, '')
                    self.paras.insert(j, 'W')
                    break
                elif next.start == end:
                    break
                # next.start < end
                elif end >= next.end:
                    clips.delete_clip(j)
                    self.transcript.delete(j)
                    del self.paras[j]
                # next.start < end < next.end
                else:
                    clips.set_clip(j, end, next.end)
            # in case we just changed the end time of the last clip 
            new_eot = self.end()
            if new_eot < old_eot:
                self.new_clip(old_eot)

    ##  Set the transcription of the i-th clip.

    def set_text (self, index, text):
        self.transcript[index] = text

    ##  Set the value for the initial-clip flag, for the i-th clip.

    def set_para (self, index, value):
        self.paras[index] = value

    ##  Delete the i-th clip.

    def delete (self, index):
        with writer(self.clips, self.transcript, self.paras):
            self.clips.delete_clip(index)
            self.transcript.delete(index)
            del self.paras[index]

    ##  Nudge the right boundary of clip i.

    def nudge (self, i, delta):
        return self.clips.nudge(i, delta)

    ##  Cut clip i at boundary position t.
    #   May fail; return value is boolean indicating success.

    def cut (self, i, t):
        with writer(self.clips, self.transcript, self.paras):
            if self.clips.cut(i,t):
                self.paras.insert(i+1, 'W')
                self.transcript.insert(i+1, '')
                return True
            else:
                return False
    
    ##  Merge clip i and clip i+1.
    #   Error if they do not both exist.

    def merge (self, i):
        with writer(self.clips, self.transcript, self.paras):
            self.clips.merge(i)
            del self.paras[i+1]
            text2 = self.transcript[i+1]
            self.transcript[i].extend(text2)
            del self.transcript[i+1]
