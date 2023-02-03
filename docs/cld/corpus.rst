
Application and corpus
======================

foo::

   <h3 id="1.1">Overview</h3>
   <p>
   The object <tt>cld_app</tt> (in seal.cld.core) is an instance of <tt>SealApp</tt> that
   represents the CLD application.  Its contents are represented by the
   CLDRequestHandler class, which overrides only two methods of RequestHandler:</p>
   <ul>
   <li>open_file() - returns a Corpus</li>
   <li>make_root() - returns a CorpusEditor</li>
   </ul>
   <p>
   The cld_app is used as the application function in a CLDManager.
   It can be invoked as:</p>
   <pre class="source">
   $ cld corpus.cld
   </pre>
   
   <h3 id="1.2">Manually instantiating the corpus</h3>
   <p>
   The easiest way to get a Corpus instance is to use the CLDManager:</p>
   <pre class="python">
   >>> from seal.cld.toplevel import CLDManager
   >>> mgr = CLDManager('/tmp/corpus.cld')
   >>> corpus = mgr.corpus()
   >>> corpus
   &lt;Corpus /tmp/corpus.cld>
   </pre>
   
   <h2 id="2">Corpus and environment</h2>
   <p>
   <span class="todo">Out of date</span></p>
   
   <h3 id="2.1">The Corpus class</h3>
   <p>
   A <a href="../seal/cld/corpus.html#Corpus"><tt>Corpus</tt></a> is a
   Structure with the following signature.</p>
   <table class="display">
   <tr><td><tt>langs</tt></td> <td><tt>LanguageList</tt></td> <td>list of mono-lingual subcorpora</td></tr>
   <tr><td><tt>users</tt></td> <td><tt>UserList</tt></td> <td>a <tt>Collection</tt> with child type <tt>User</tt></td></tr>
   <tr><td><tt>roms</tt></td> <td><tt>Registry</tt></td> <td>the central registry of romanizations</td></tr>
   <tr><td><tt>glab</tt></td> <td><tt>GLabDirectory</tt></td> <td></td></tr>
   </table>
   <p>
   In addition, a corpus has a <tt>_meta</tt> member containing a
   PropList with general information, and, like all Files,
   an <tt>env</tt> member containing an Environment.</p>
   
   <h3 id="2.2">The Environment</h3>
   <p>
   The <tt>env</tt> member is inherited from File, but it gets set by the
   Corpus, inasmuch as the Corpus is the root of the disk hierarchy.  See
   the section <a href="toplevel.html#1">Environment</a> for general
   information on environments.  Corpus specializes Database,
   which specializes EnvRoot.</p>
   <p>
   When one reaches a Language when descending the hierarchy, a new copy
   of the Environment is created that is specific to that language.  The
   new copy is used by the Language and its descendants.</p>
   <p>
   An Environment instance has the following members:</p>
   <table class="display">
   <tr><td><tt>corpus</tt></td> <td>A backlink to the Corpus.</td></tr>
   <tr><td><tt>username</tt></td> <td>The authorized username, for the purpose of permissions</td></tr>
   <tr><td><tt>language</tt></td> <td>Set to the language, if within the scope of a language</td></tr>
   <tr><td><tt>parent</tt></td> <td>The original Environment, if this one belongs to a language.</td></tr>
   </table>
   <p>
   All Environments provide the following methods:</p>
   <table class="display">
   <tr><td><tt>for_language(lang)</tt></td> <td>Create a copy associated with the given language.</td></tr>
   <tr><td><tt>require_rom(name)</tt></td> <td>Returns the named
       Romanization.  Signals an error if not found.</td></tr>
   <tr><td><tt>find_rom(name)</tt></td> <td>Returns the named
       Romanization, or None if not found.</td></tr>
   </table>
   <p>
   Language-specific Environments provide the following methods:</p>
   <table class="display">
   <tr><td><tt>get_text(id)</tt></td> <td>Returns the text that has the
       given ID.</td></tr>
   <tr><td><tt>default_orthography()</tt></td> <td>Returns the default
       orthography for this language.</td></tr>
   <tr><td><tt>orthographies()</tt></td> <td>Returns the list of
       available orthographies for this language.</td>
   <tr><td><tt>romanization()</tt></td> <td>Returns the default orthography as a
   Romanization.</td>
   <tr><td><tt>deref_parid(parid)</tt></td> <td>Returns the paragraph with the
       given paragraph ID.</td></tr>
   </table>
   
   <h3 id="2.3">Example</h3>
   <p>
   An example of opening a corpus and accessing a couple of its members:</p>
   <pre class="source">
   >>> from seal.cld.corpus import Corpus
   >>> corpus = Corpus('corpus.cld')
   >>> corpus.media.filename()
   '/Users/abney/git/cld/media'
   >>> corpus.langs['oji']
   &lt;seal.cld.language.Language object at 0x10ac41fd0>
   </pre>
   
   <h2 id="3">User interface</h2>
   
   <h3 id="3.1">Corpus UI</h3>
   
   <h3 id="3.2">Metadata editor</h3>
   
   <h3 id="3.3">Catalog of pages</h3>
   <p>
   The relevant modules all belong to seal.cld.ui.</p>
   <table class="display">
   <tr>
   <th>URL</th>
   <th>Class (module)</th>
   </tr>
   
   <tr>
   <td>/home</td>
   <td><a href="#2b.1">CorpusEditor</a> (corpus)</td>
   </tr>
   
   <tr>
   <td>/langs</td>
   <td>LanguageListEditor (language)</td>
   </tr>
   
   <tr>
   <td>.../lang.xxx/home</td>
   <td>LanguageEditor (language)</td>
   </tr>
   
   <tr>
   <td>.../texts/home</td>
   <td>TocEditor (toc)
   </td>
   </tr>
   
   <tr>
   <td>.../page/edit</td>
   <td>PageEditor (page)</td>
   </tr>
   
   <tr>
   <td>.../audio/edit</td>
   <td>AudioEditor (audio)</td>
   </tr>
   
   </table>
   
   <h2 id="4">Corpus file format</h2>
   <p>
   The following table gives the corpus file format.  The root type is
   'Corpus.'</p>
   <p>
   All directories contain <tt>_children</tt> and <tt>_perm</tt>; they
   are not explicitly mentioned in the table.</p>
   <p>
   All files are in tab-separated format.</p>
   
   <table class="display">
   <tr><th>Filename</th> <th>Class</th> <th></th> <th>Contents</th></tr>
   <tr><td>_children</td> <td>Children</td> <td>F</td> <td><i>name suffix</i></td></tr>
   <tr><td>_config</td> <td>Config</td> <td>F</td> <td><i>key value</i></td></tr>
   <tr><td>_groups</td> <td>GroupsFile</td> <td>F</td> <td><i>usr grp</i>[<i>(sp)grp*</i>]</i></td></tr>
   <tr><td>_info</td> <td>PropDict</td> <td>F</td> <td><i>key value</i></td></tr>
   <tr><td>_meta</td> <td>PropDict</td> <td>F</td> <td><i>key value</i></td></tr>
   <tr><td>_perm</td> <td>Permissions</td> <td>F</td> <td><i>mode role usr</i>[<i>(sp)usr*</i>]</td></tr>
   <tr><td>*.cl</td> <td>ClipsFile</td> <td>F</td> <td><i>start end</i></td></tr>
   <tr><td>*.cld</td> <td>Corpus</td> <td>D</td> <td>_config _meta _groups<br/>glab.gd
       langs.ll roms.reg users.ul</td></tr>
   <tr><td>*.gd</td> <td>GLabDirectory</td> <td>D</td> <td><i>user</i>.gl*</td></tr>
   <tr><td>*.gl</td> <td>Library</td> <td>D</td> <td><i>n</i>.gn*</td></tr>
   <tr><td>*.gn</td> <td>Notebook</td> <td>F</td> <td>(GLab notebook format)</tr>
   <tr><td>*.lg</td> <td>Language</td> <td>D</td> <td>_index _info lexicon.lx texts.toc</td></tr>
   <tr><td>*.ll</td> <td>LanguageList</td> <td>D</td> <td><i>lang</i>.lg*</td></tr>
   <tr><td>*.lx</td> <td>Lexicon</td> <td>F</td> <td><i>form sno refs n=value*</td></tr>
   <tr><td>*.mf</td> <td>MediaFile</td> <td>F</td> <td><i>usr</i>/<i>name</i>.<i>suf</i></td></tr>
   <tr><td>*.mi</td> <td>MediaIndex</td> <td>F</td> <td><i>name</i>.<i>suf tid</i></td></tr>
   <tr><td>*.pd</td> <td>PropDict</td> <td>F</td> <td><i>key value</i></td></tr>
   <tr><td>*.pp</td> <td>ParagraphFile</td> <td>F</td> <td><i>bool</i></td></tr>
   <tr><td>*.reg</td> <td>Registry</td> <td>D</td> <td><i>name</i>.rom</td></tr>
   <tr><td>*.rom</td> <td>Romanization</td> <td>F</td> <td><i>ascii unicode</i></td></tr>
   <tr><td>*.tf</td> <td>TokenFile</td> <td>F</td> <td><i>sentno</i> |
       nxid <i>n</i> | <i>form sno lpunc rpunc</i></td></tr>
   <tr><td>*.toc</td> <td>Toc</td> <td>D</td> <td><i>id</i>.txt*</td></tr>
   <tr><td>*.txt</td> <td>Text</td> <td>D</td> <td>_info orig.tf trans.tr? |<br/>
    _info media.mf xscript.xs? trans.tr? |<br/>_info toc.toc</td></tr>
   <tr><td>*.xs</td> <td>Transcription</td> <td>D</td> <td>clips.cl paras.pp transcript.tf</td></tr>
   <tr><td>*.tr</td> <td>Translation</td> <td>F</td> <td><i>trans</i></td></tr>
   <tr><td>*.ul</td> <td>UserList</td> <td>D</td> <td><i>name</i>.usr*</td></tr>
   <tr><td>*.usr</td> <td>User</td> <td>D</td> <td>media.mi props.pd</td></tr>
   </table>
   
   <h2 id="5">CLDManager</h2>
   
   </body>
   </html>
