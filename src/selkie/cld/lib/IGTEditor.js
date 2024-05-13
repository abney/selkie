
import Factory from "/.lib/util.js";
import Ajax from "/.lib/ajax.js";

var make = new Factory();


//==============================================================================
//  IGTEditor.js
//==============================================================================
//
//  The page is produced by seal.cld.ui.igt.IGTEditor.edit()
//  The URL ends with: text.T/page/igt.P.I/edit
//    - P is the paragraph number
//    - I is the displayed token index.  It is None before the user selects a token.
//
//  The main portion of the page looks like this:
//  +-------------------------------+
//  |              |  TOKEN PANEL   |
//  |  TEXT PANEL  +----------------+
//  |              |  LEXENT PANEL  |
//  |              |                |
//  +--------------+----------------+
//
//     * TEXT PANEL - displays the text with interlinear glosses
//           The trans div will be missing if the text has no translation
//     * TOKEN PANEL - displays the selected token, with buttons
//           and links for lexical entries (and other ancillary items)
//     * LEXENT PANEL - displays a stack of lexical entries and other items,
//           with the currently selected item at the top
//  
//  The text panel (id = 'textsDiv') consists of
//   - a div with class 'igtparagraphs', representing words and glosses:
//      - span with class 'glossed' contains the word and
//         - embedded span with class 'gloss'
//   - a div with class 'trans', for the sentence translation
//

//  Here is an example of the original HTML.  It is identical whether token
//  index is supplied or not:
//
//  <h1>Untitled</h1>
//  <table class="grid">
//    <tr>
//      <td>
//        <h3>Paragraph 0</h3>
//        <input  type="button" value="Prev" disabled/>
//        <input  type="button" value="Next" onclick="window.location='../igt.1/edit'"/>
//        <div id="textsDiv">
//          <div class="igtparagraphs bordered" data-ascii="das ist ein Beispiel">
//            <span class="glossed" data-index="0" data-ascii="das" data-seqno="0">
//              das
//              <br />
//              <span class="gloss">this</span>
//            </span>
//            <span class="glossed" data-index="1" data-ascii="ist" data-seqno="0">
//              ist
//              <br />
//              <span class="gloss">is</span>
//            </span>
//            ...
//          </div>
//          <div class="trans bordered">this is an example</div>
//        </div>
//        <input  type="button" value="Prev" disabled/>
//        <input  type="button" value="Next" onclick="window.location='../igt.1/edit'"/>
//      </td>
//      <td id="col2">
//        <div class="groupingDiv" id="lexentViewer"></div>
//      </td>
//    </tr>
//  </table>
//





//
//  <table class="grid">
//    <tr>
//
//      <!-- TEXT PANEL -->
//      <td>
//        <h3>Paragraph 0</h3>
//        <input type="button" value="Prev" .../> <... "Next" .../>
//        <div id="textsDiv">
//          <div class="igtparagraphs bordered" data-ascii=""> ... </div>
//          <div class="trans bordered"> ... </div>
//        </div>
//        <input type="button" value="Prev" .../> <... "Next" .../>
//      </td>
//
//      <!--  second column -->
//      <td id="col2">
//
//        <!--  TOKEN PANEL  -->
//        <div class="groupingDiv" id="lexentViewer"></div>
//
//      </td>
//    </tr>
//  </table>
//


//  The page ends with the following script:
//
//  <script>
//    var lexentViewer = new LexentPanel('edit/lexentViewer','/langs/lang.deu',true);
//    IGTEditor('0',null,true);
//  </script>
//
//  If the user has selected a token, the only change is e.g.:
//
//    IGTEditor('0','3',true);
//


//        <div class="bordered">
//          <form name="token">
//            <table class="lemmaTable"> ... </table>
//          </form>
//        </div>
//

export default function IGTEditor (lexentViewer, parno, index, writable) {
    var editor = this;
    var lexentViewer = lexentViewer;
    var parno = parno;
    var writable = writable;
    var fetchForm = new FormData();

    var tokens = null;
    var textsDiv = null;
    var textEditor = null;

    var currentToken = null;
    var currentLemma = null;
    var currentSeqno = null;

    tokens = initializeTokens();
    textsDiv = initializeTextsDiv();
    textEditor = createTextEditor();
    if (index !== null) selectToken(tokens[index]);

    //
    //  Returns the collection of word+gloss elements (class = 'glossed').
    //  Also assigns a click listener to each.
    //
    function initializeTokens () {
	var tokens = document.getElementsByClassName('glossed');
	for (var i = 0; i < tokens.length; ++i) {
	    var token = tokens[i];
	    token.index = token.getAttribute('data-index');
	    token.addEventListener('click', tokenClickHandler);
	}
	return tokens;
    }

    //
    //  Click handler for a word+gloss element (class = 'glossed').
    //  When it is clicked, a new page is fetched with the corresponding
    //  token selected.
    //
    function tokenClickHandler (evt) {
	window.location = '../igt.' + parno + '.' + this.index + '/edit';
    }

    //
    //  Fetches and returns the glossed-sentence box (id = 'textsDiv').
    //  If the text is writable, also inserts a little 'edit' button.
    //
    function initializeTextsDiv () {
	var textsDiv = document.getElementById('textsDiv');
	var orig = textsDiv.children[0];
	if (writable) {
	    var button = make.LittleButton('edit', openTextEditor, orig);
	    button.style.float = 'right';
	    orig.insertBefore(button, orig.firstChild);
	}
	return textsDiv;
    }

    //
    //  Creates and returns a form element.  Does not insert it anywhere.
    //
    function createTextEditor () {
	var orig = textsDiv.children[0].getAttribute('data-ascii');
	var form = document.createElement('form');

	form.action = 'save_text';
	form.method = 'POST';
	form.enctype = 'multipart/form-data';
	form.appendChild(make.TextArea('orig', orig));

	if (textsDiv.children.length > 1) {
	    var trans = textsDiv.children[1].textContent;
	    form.appendChild(make.TextArea('trans', trans));
	}

	form.appendChild(make.SubmitButton('save'));
	form.appendChild(document.createTextNode(' '));
	form.appendChild(make.Button('cancel', closeTextEditor));
	return form;
    }

    //
    //  The action for the 'edit' button in the glossed-sentence box.
    //  It replaces the glossed-sentence box with a textarea for editing.
    //  Callback is 'IGTEditor.save_text(parno,orig,trans,submit)'.
    //
    function openTextEditor (evt) {
	textsDiv.parentNode.replaceChild(textEditor, textsDiv);
    }

    //
    //  The action for the 'cancel' button in the text editor.
    //  Replaces the editor with the glossed-sentence box.
    //
    function closeTextEditor (evt) {
	textEditor.parentNode.replaceChild(textsDiv, textEditor);
    }

    function setToken (unicode, ascii) {
	currentToken.setAttribute('data-ascii', ascii);
	currentToken.firstChild.nodeValue = unicode;
    }

    //
    //  Called if there is a selected token.
    //  token is a span with class 'glossed'.
    //  This assumes that lexentViewer (type LexentPanel) is defined.
    //
    function selectToken (token) {
	if (currentToken !== null) currentToken.className = 'glossed';
	currentToken = token;
	currentToken.className = 'glossed tokenSelected';
	currentLemma = currentToken.getAttribute('data-ascii');
	currentSeqno = currentToken.getAttribute('data-seqno');
	var index = currentToken.index;
	lexentViewer.displayForm(currentLemma, currentSeqno);
    }
}

console.log('IGTEditor.js is loaded');
