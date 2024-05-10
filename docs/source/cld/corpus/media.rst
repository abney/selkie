
Recordings
**********

External media directory
------------------------

On disk
.......

Audio files are orders of magnitude larger than text files.  For
example, my working corpus.cld directory as of this writing contains
one WAV file of size 41.845 MB, and all other files together amount to
0.147 MB.  Video files are an order of magnitude larger than audio
files.  If nothing else, such lopsidedly large files are problematic for distributing
the corpus.cld directory by GIT.  For this reason,
we create an external **media directory** and distribute media files
separately.

The location of the media directory is specified in the configuration
table used to instantiate App, under the key 'media'.
In our earlier example (Instantiating the App class), recall
that we specified::

   >>> cfg['media'] = '~/git/cld/media'

One may also access the value from the app as <code>app.config['media']</code>.

The media directory is subdivided by user.  Upload to the media
directory is outside the usual permissions system, but one may only
upload to one's own subdirectory.  A user's subdirectory is
simply a flat directory containing audio and video files.  There are
no constraints on file names except that it is expected that each
filename have a standard suffix representing the format (wav, mp3,
mp4, etc.)  The filename without the suffix we call the **recording ID**.
For example::

   $ cd ~/git/cld/media
   $ ls
   abney
   $ ls abney
   otw-bmcc-01-010-sample.clips    otw-mchi-01-004.clips
   otw-bmcc-01-010-sample.mp4      otw-mchi-01-004.wav
   otw-bmcc-01-010-sample.wav

There are two recording IDs, otw-bmcc-01-010-sample and otw-mchi-01-004,
and multiple files for each ID.

MediaDirectory
..............

In memory, the media directory is represented by a MediaDirectory
object.  This is not a specialization of File, as it does not
represent a disk-file within the corpus.
When the top-level CorpusEnvironment is instantiated, it creates a
MediaDirectory and stores it under the key 'media'.
It can be accessed as env.media().

The method files is called with *username* as argument and
returns an iteration over RawMediaFile objects for the named user.
The list of files is obtained by reading the user's subdirectory of
the media disk-directory.  The user's **media index** is used to
determine which text, if any, each file is associated with.
(See below.)

For example::

   >>> media = corpus.env.media()
   >>> media
   <seal.cld.media.MediaDirectory object at 0x...&gt;
   >>> files = list(media.files('abney'))

The MediaDirectory also provides a method **add** for uploading
a media file.  It takes three arguments: a User instance,
an fname, and the contents (bytes).

RawMediaFile
............

The files are instances of RawMediaFile.  They have members username,
fname, and text::

   >>> files[4]
   <RawMediaFile abney otw-mchi-01-004.wav 16>
   >>> files[4].username
   'abney'
   >>> files[4].fname
   'otw-mchi-01-004.wav'
   >>> files[4].text
   '16'

**CAUTION:** A RawMediaFile is meant to be a short-lived object.
In particular, if a new association between media file and text is
created, it will not be tracked to any existing RawMediaFile.

Media texts (recordings)
------------------------

Media file
..........

Media files are usually associated with
particular texts.
Such a text has a child named media of class MediaFile.

A MediaFile behaves like a dict that maps a media file suffix (such
as .wav or .mp3) to a RawMediaFile.
Internally, it contains a table that maps suffixes to
pairs (*username, fname*), where
fname includes the suffix, e.g. otw-mchi-01-004.wav.  It then
uses the MediaDirectories files method to get a RawMediaFile.

The usual dict methods are supported: __getitem__, get, __contains__,
__len__, __iter__.

More conveniently, the
method data() takes a suffix and returns a RawFile containing
the media file contents.  It may be called without a suffix, in which
case it returns the default entry.

MediaFile has a method media_filename()
that takes a suffix (optionally) and returns the absolute pathname of the media file::

   >>> text16.media.media_filename('wav')
   /Users/abney/git/cld/media/abney/otw-mchi-01-004.wav

A new entry can be added using the method **set.**  It takes a
username and fname.  If the table was previously empty, the fname's
suffix becomes the default suffix.  One can explicitly change the
default suffix using **set_default,** which takes a suffix as
argument.

User media index
................

The reverse index, mapping media filenames to texts, is found in the
User object, in a file named media.  It is a PropDict
whose keys are fnames and whose values are text names.

Audio and Video
---------------

Media
.....

The module seal.cld.ui.media
contains MediaSelector and Transcriber.  The latter is discussed in
the next section, Transcription.

The MediaSelector displays the current user's media files.  If
the media file is associated with a text, a link to the text is shown,
otherwise a link is shown that calls the set_media()
method of the parent.

Audio
.....

Video
.....

Transcription
-------------

Transcription (data object)
...........................

A Transcription
(seal.cld.corpus.transcript)
is the written version of an audio or audio-visual
recording.  On disk, a text contains a child called 'media' that
represents the audio or movie file, and a child called 'xscript'
that represents the transcription.

The xscript child loads into memory as a Transcription
object.  For example::

   >>> x = oji/'texts'/'33'/'xscript'
   >>> x
   <Transcription langs/oji/texts/33/xscript>

The user interface is represented by the Transcriber
class (seal.cld.ui.media).
It is intended to make transcription as
easy as possible.  Functionality is intentionally limited; it is meant
to server one purpose as well as possible.

The approach is as follows.  The user
plays a small bit of audio, writes down what was said,
and then proceeds to the next bit of audio.  Precise alignment is not
important.  Support for additional tiers of annotation is not provided
in the transcription interface.
The units of transcription are expected to consist of only a word or
two, at most a second or two of audio.  We call these units
**clips** (or "snippets").  Keeping clips small not
only makes transcription easier, it also allows finer-grained access
to audio from text or lexicon.

A clip consists of a start position
in the recording, an end position, and a bit of target-language text
as transcription.  In the interest of simplicity,
we require that the start position of a clip be the
same as the end position of the previous clip.  A possible criticism
is that there may be silence or non-speech sound between clips, but
we address that possibility by using clips labeled with the empty
string to represent non-speech.

Clips are smaller than translation units.  A consequence is that
there is a conversion step to obtain translation units from a
transcription.  In the interest of simplicity, we simply add a flag
indicating whether or not a clip begins a new translation unit or not.
This presumes that a clip never spans a translation unit
boundary, a constraint that seems acceptable.

In sum, a transcription can be thought of as a table in which each
record represents a clip.  The columns are the end position, the text,
and a boolean indicating whether the clip begins a new translation
unit.  The clip's start position is determined by the end position
of the previous clip, and the first clip's start position is 0.

TransTokenFile
..............

A TransTokenFile (seal.cld.corpus.token) is the result of converting a
list of snippets into translation units.  Its constructor takes a Transcription.

Transcriber (server-side UI)
............................

The web directory is represented on the server side by the class
Transcriber.  For
example::

   >>> t = app.follow('/langs/lang.oji/texts/text.7/page/xscript')
   >>> t
   <seal.cld.ui.media.Transcriber object at 0x...>
   >>> t.file
   <Transcription langs/oji/texts/33/xscript>

Its edit() method generates the transcription
page.  The edit() method accepts two
arguments, *i* and *n*, where *i* represents the index
of the first clip to display (default 0), and *n* represents the
number of clips to display on the page.  It is expected that *i*
is a multiple of *n/2*.  *n* is a maximum, not an
exact number; it is possible that fewer clips are available.

XScript.js (client-side UI)
...........................

The web page consists of a media element
(audio or video) followed by a table of clips in a navigation frame.
The table displays a "pageful" of clips, a pageful being up to
*n* clips, depending on how many are available.
The navigation frame allows one to move among pagefuls.  Motion is by
the half-page so that context is preserved.

The navigation frame and an empty clip table element are included in
the web page.  The clip records are generated by javascript.
The user interaction is handled by the javascript
file XScript.js.
 
The following is an example of a clip record:
<img src="../figs/snippet.jpg"></img>

The controls are as follows:

 * A **play button** that plays the clip.

 * A **record button** that allows one to (re-)set the end point of the
   clip.  After clicking, the label changes to "cut," and a second
   click sets the end point and shifts focus to the text box.
   The end time precedes that actual click
   by a fraction of a second.

 * Next to the record button are **left nudge**
   and **right nudge** buttons that adjust the end time by about half
   a second.  They replay the last half-second of the adjusted clip.

 * A **new-paragraph checkbox.**  If it is checked, this clip
   introduces a new translation unit in the text.

 * The **text box**.  One enters transcription text and
   saves it by pressing enter.  One may cancel by pressing escape.

If the new end position is earlier than the old end position, a new
empty clip is inserted to fill the gap.  If the new end position is
later than the old one, any following clips that are completely
covered are deleted, and their texts are appended to the current
clip's text.  A following clip that is only partially covered
has its start position adjusted.  Apart from these automatic
insertions and deletions, the interface provides no facility for
changing the number of clips.

Nudging is not problematic.
Nudging simultaneously alters the end time of the nudged clip and the start time
of the following clip (if any).
A left nudge is not allowed if it would make the clip shorter than a
fixed minimum length, and a right nudge is disallowed if it would make
the following clip too short.

Since no facility is provided to add new clips, there is always an
empty "sentinel" clip at the end of the table that covers the
untranscribed remainder of the recording.  (The sentinel clip is not
included in the file on disk, only in the interface.)
If the final "true" clip ends at the end of the recording, there is no
need for the sentinel, but the standard Python library does not
provide the ability to extract
data (including duration) from movie files.  Rather than linking to an
external library or attempting to parse movie files directly, we
always include the sentinel.  If it is unneeded, it does no harm.

If the start index is greater than zero, the **previous button** is
activated.  It links to edit.*i-n/2*.
If the end index is less than the transcript length plus one, the
**next button** is activated.  It links to edit.*i+n/2*.
