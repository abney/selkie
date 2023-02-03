##  @package seal.cld.corpus.media
#   Media.

import os
from seal.core import sh
from seal.core.io import split_suffix, get_suffix, redirect
from seal.app import RawFile
from seal.cld.db.disk import writer
from seal.cld.db.file import File
from seal.cld.db.dir import Directory, Structure


#--  The media directory  ------------------------------------------------------

##  The actual media file.

class RawMediaFile (object):

    ##  Constructor.

    def __init__ (self, media, user, fname):
        self._media = media
        self._user = user
        self._fname = fname

    ##  The name of the owner.

    def username (self): return self._user.name()

    ##  The file name, excluding directory.

    def fname (self): return self._fname

    ##  The pathname, relative to the media directory.  It has the form
    #   USER/FNAME.

    def filename (self): return self._user.name() + '/' + self._fname

    ##  The texts that contain a logical MediaFile pointing to this physical one.

    def textids (self): return self._user.media.get(self._fname)

    ##  String representation.

    def __repr__ (self):
        return '<RawMediaFile %s %s>' % (self._user.name(), self._fname)


##  A media directory.

class MediaDirectory (object):

    ##  Constructor.

    def __init__ (self, dirname, env):

        ##  The environment.
        self.env = env

        self._dirname = dirname

    ##  The directory name.

    def dirname (self):
        return self._dirname

    ##  The filename for a particular physical media file.

    def media_filename (self, username, fname):
        return os.path.join(self._dirname, username, fname)

    ##  The list of files for the given user.  If a user name is not explicitly
    #   provided, the authenticated user is assumed.

    def files (self, username=None):
        return list(self.iter_files(username))

    ##  Iterate over the files for the given user.

    def iter_files (self, user=None):
        if isinstance(user, str):
            user = self.env.get_user(user, allow_unknown=False)
        if user is not None:
            uname = user.name()
            dir = os.path.join(self._dirname, uname)
            if os.path.exists(dir):
                for fname in os.listdir(dir):
                    yield RawMediaFile(self, user, fname)

    ##  Add a new physical media file.  N.b., this is not protected 
    #   by locking or file backup.

    def add (self, username, fname, contents):
        assert '/' not in fname
        dir = os.path.join(self._dirname, username)
        if not os.path.exists(dir):
            sh.mkdir(dir)
        fn = os.path.join(dir, fname)
        with open(fn, 'bw') as f:
            f.write(contents)

    ##  List the directory.  For debugging convenience.

    def ls (self):
        sh.ls(self._dirname)

    ##  String representation.

    def __repr__ (self):
        return '<MediaDirectory %s>' % self._dirname


#--  MediaFile  ----------------------------------------------------------------

##  A logical media file.  Essentially, it is a symbolic link to a physical
#   media file.  More precisely, it is a group of related files differing by
#   file suffix, representing different versions of the same content.

class MediaFile (File):

    ##  Read the contents from file.

    def __read__ (self, f):
        self._default_suffix = ''
        self._table = tab = {}
        for line in f:
            line = line.rstrip('\r\n')
            if line.startswith('__default__'):
                self._default_suffix = line[12:]
            else:
                suffix = get_suffix(line)
                tab[suffix] = tuple(line.split('/'))

    ##  Write the contents to file.

    def __write__ (self, f):
        f.write('__default__')
        f.write('\t')
        f.write(self._default_suffix)
        f.write('\n')
        for value in self._table.values():
            f.write('/'.join(value))
            f.write('\n')

    ##  Get the text that this media file belongs to.

    def text (self): return self.parent()

    ##  Get the filename of the physical file.

    def media_filename (self, suffix=None):
        self.require_load()
        if suffix is None:
            suffix = self._default_suffix
        (username, fname) = self._table[suffix]
        media = self.env.media()
        return media.media_filename(username, fname)

    ##  Get the version corresponding to the given suffix.

    def __getitem__ (self, suf=None):
        self.require_load()
        suf = self._require_suffix(suf)
        return self.media_filename(suf)

    ##  Whether the given suffix is available.

    def __contains__ (self, suf):
        self.require_load()
        return self._table.__contains__(suf)

    ##  The number of different versions that are available.

    def __len__ (self):
        self.require_load()
        return self._table.__len__()

    ##  Iterate over the file suffixes.

    def __iter__ (self):
        self.require_load()
        return self._table.__iter__()

    def _require_suffix (self, suffix):
        if suffix and suffix != '__default__':
            return suffix
        elif self._default_suffix:
            return self._default_suffix
        else:
            raise Exception('No default suffix')

    ##  Get a version by suffix, returning None on failure.

    def get (self, suf=None):
        self.require_load()
        suf = self._require_suffix(suf)
        if self.__contains__(suf):
            return self.media_filename(suf)

    ##  An iteration over the filenames.

    def values (self):
        self.require_load()
        return self._table.values()

    ##  An iteration over pairs (suffix, filename).

    def items (self):
        self.require_load()
        return self._table.items()

    ##  A RawFile representing the contents of the physical media file.

    def data (self, suffix=None):
        self.require_load()
        suffix = self._require_suffix(suffix)
        return RawFile(self.media_filename(suffix), suffix)

    ##  Set the media file that this symbolic link points to.

    def set (self, username, fname):
        id = self.text().id()
        user = self.env.intern_user(username)
        rdx = user.media
        # if fname in rdx:
        #     raise Exception('fname is already associated with a text: %s' % fname)
        with writer(self, rdx):
            self.modified()
            suffix = get_suffix(fname)
            self._table[suffix] = (username, fname)
            if not self._default_suffix:
                self._default_suffix = suffix
            rdx.add(fname, id)

    ##  Get the default version.

    def get_default (self):
        self.require_load()
        return self._default_suffix

    ##  Set the default suffix.

    def set_default (self, suffix):
        with writer(self):
            if suffix not in self._table:
                raise Exception('No entry for suffix: %s' % repr(suffix))
            self.modified()
            self._default_suffix = suffix


#--  MediaIndex  ---------------------------------------------------------------

##  An index of logical media files referring to physical media files in a given
#   user's media directory.  Keys are file names and values are lists of TIDs.

class MediaIndex (File):

    ##  Read the contents from file.

    def __read__ (self, f):
        self._table = {}
        for line in f:
            (k,v) = line.rstrip('\r\n').split('\t')
            self._table[k] = v.split(',')

    ##  Write the contents to file.

    def __write__ (self, f):
        for (k,v) in self._table.items():
            f.write(k)
            f.write('\t')
            f.write(','.join(v))
            f.write('\n')

    ##  The number of entries.

    def __len__ (self):
        self.require_load()
        return len(self._table)

    ##  Whether there is an entry for the given key.

    def __contains__ (self, k):
        self.require_load()
        return self._table.__contains__(k)

    ##  Iterate over keys.

    def __iter__ (self):
        self.require_load()
        return self._table.__iter__()

    ##  Fetch an entry.

    def __getitem__ (self, k):
        self.require_load()
        return self._table[k]

    ##  Fetch an entry, returning None on failure.

    def get (self, k):
        self.require_load()
        return self._table.get(k)

    ##  Iterate over keys.

    def keys (self):
        self.require_load()
        return self._table.keys()

    ##  Iterate over values.

    def values (self):
        self.require_load()
        return self._table.values()

    ##  Iterate over items.

    def items (self):
        self.require_load()
        return self._table.items()

    ##  Add a new entry.  The key is an fname, that is, the last component
    #   of the pathname, of form NAME.SUFFIX.  The value is a TID.

    def add (self, fname, tid):
        with writer(self):
            if fname in self._table:
                lst = self._table[fname]
                if tid not in lst:
                    self.modified()
                    lst.append(tid)
            else:
                self.modified()
                self._table[fname] = [tid]

    ##  Delete a TID.  Also delete the entry for the fname if it is left
    #   with no TIDs.

    def delete (self, fname, tid):
        with writer(self):
            if fname in self._table:
                lst = self._table[fname]
                i = lst.find(tid)
                if i >= 0:
                    self.modified()
                    if len(lst) == 1:
                        del self._table[fname]
                    else:
                        del lst[i]

