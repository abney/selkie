
import Ajax from "/.lib/ajax.js";
import Element from "/.lib/element.js";

//==============================================================================
//  PlainTextPanel.js
//==============================================================================


//--  EditBox  -----------------------------------------------------------------
//
//  The EditBox is only displayed when editing a paragraph.  It is its own
//  controller.  Start by calling open().  User types into the textarea.  
//  Three ways of finishing:
//
//      (1) onkeypress() receives Enter.  Hands off to commit().
//
//      (2) Commit button is clicked, generating onclickcommit() call.
//          Hands off to commit().
//
//      (3) Cancel button is clicked, generating onclickcancel() call.
//          Hands off to cancel().
//
//  These generate one of two calls:
//
//      (1) commit().  If the text has not changed, hands off to cancel().
//          Otherwise, calls text.save().  That does a server.requestSave(),
//          which calls text.finishSave() on completion, which calls my close().
//          
//      (2) cancel().  Just hands off to close().
//
//  In either case, close() is eventually called.  It inserts the text element
//  back in place of the textarea, sets text to null, and passes focus on to
//  the next element in line.
//
function EditBox () {

    var textboxElt = document.createElement("textarea");
    textboxElt.rows = 10;
    textboxElt.style.width = "100%";
    textboxElt.style.marginBottom = "3px";
    textboxElt.addEventListener('keypress', EditBox.onkeypress);
    textboxElt.control = this;

    var parElt = document.createElement('p');
    parElt.appendChild(textboxElt);
    parElt.appendChild(Element.button('Commit', EditBox.onclickcommit, this));
    parElt.appendChild(Element.button('Cancel', EditBox.onclickcancel, this));

    var editbox = this;

    this.textboxElt = textboxElt;
    this.parElt = parElt;
    this.text = null;
}

//
//  open(text) - If I already have a text, close it.  Insert my textarea in place
//  of text, set my contents to text.ascii, get focus, move cursor to end.
//
EditBox.prototype.open = function (text) {
    if (this.text !== null) this.commit();
    this.text = text;
    this.textboxElt.value = text.ascii;
    Element.replace(text.elt, this.parElt);
    this.textboxElt.focus();
    var i = text.ascii.length;
    this.textboxElt.setSelectionRange(i,i);
};

//
//  onkeypress() - If the key is Enter, call commit().
//
EditBox.onkeypress = function (evt) {
    if (evt.key === 'Enter') {
	var editbox = evt.target.control;
	editbox.commit();
	return false;
    }
    else return true;
};

//
//  onclickcommit() - The callback from the Commit button.  Call commit().
//
EditBox.onclickcommit = function (evt) {
    var editbox = evt.target.control;
    editbox.commit();
};

//
//  onclickcancel() - The callback from the Cancel button.  Call cancel().
//
EditBox.onclickcancel = function (evt) {
    var editbox = evt.target.control;
    editbox.cancel();
};

//
//  The commit action.  If the text has not changed, invoke cancel() instead.
//  Otherwise, call the text's save() method with the new ascii.
//
EditBox.prototype.commit = function () {
    var ascii = this.textboxElt.value.trim();
    var oldAscii = this.text.ascii;
    if (ascii === oldAscii) {
	this.cancel();
    }
    else {
	this.text.save(ascii);
    }
};

//
//  The cancel action.  Just calls close().
//
EditBox.prototype.cancel = function () {
    this.close();
};

//
//  The close action.  

EditBox.prototype.close = function () {
    console.log('close');
    var text = this.text;
    if (text !== null) {
	Element.replace(this.parElt, text.elt);
	this.text = null;
	// need this.text to be null before calling delete; it will call close() again
	var next;
	if (text.status() === 'new') {
	    next = text.nextRow();
	    text.delete();
	}
	else {
	    next = text.next();
	}
	if (next === null) text.panel.plusButton.focus();
	else next.focus();
    }
};


//--  Server  ------------------------------------------------------------------

function Server () {
    this.form = new FormData();
    this.ajax = new Ajax();
}

Server.prototype.requestSave = function (text, ascii) {
    var form = this.form;
    var op = (text.status() === 'new' ? 'insert' : 'replace');
    form.set('op', op);
    form.set('i', text.i);
    form.set('j', text.j);
    form.set('text', ascii);
    console.log('requestSave(', op, text.i, text.j, ')...');
    this.ajax.call('edit_par', form, function (unicode) {
	    console.log('... received response');
	    text.finishSave(ascii, unicode);
	});
};

Server.prototype.requestDelete = function (text) {
    console.log('requestDelete...');
    var form = this.form;
    form.set('op', 'delete');
    form.set('i', text.i);
    form.set('j', text.j);
    form.set('text', '');
    this.ajax.call('edit_par', form, function (unicode) {
	    console.log('... received response');
	    text.finishDelete();
	});
};


//--  Text  --------------------------------------------------------------------
//
//  The cells of the HTML table element are assigned a 'text' member that points
//  to one of these.  Each represents one paragraph of text.
//
//  A pair of Texts is a Par (see below).  A Par may be old (already exists on
//  disk), new (not yet), or being saved (waiting for server response).
//

function Text (par, j, ascii, elt) {
    this.panel = par.panel;
    this.par = par;
    this.elt = elt;  // a paragraph
    this.ascii = ascii;
    this.i = par.i;
    this.j = j;
    this.buttonBar = new ButtonBar(this);

    if (elt === undefined) {
	elt = document.createElement('p');
	elt.className = 'editable';
	this.elt = elt;
    }

    if (ascii === '') elt.style.padding = '7';
    elt.setAttribute('tabindex', 0);
    //elt.onfocus = focusHandler;
    elt.onclick = Text.onclick;
    elt.onkeypress = Text.onkeypress;
    elt.control = this;
    elt.insertBefore(this.buttonBar.elt, elt.firstChild);
}

Text.onclick = function (evt) {
    var text = evt.target.control;
    if (text.isEditable()) text.edit();
    else text.gotoIGT();
};

Text.onkeypress = function (evt) {
    var text = evt.target.control;
    if (evt.key === 'Enter') {
	text.edit();
	return false;
    }
    else return true;
};

Text.prototype.status = function () {
    return this.par.status;
};

Text.prototype.isEditable = function () {
    return this.panel.writable;
};

Text.prototype.isTranscription = function () {
    return this.panel.transcribed;
};

Text.prototype.isTranslation = function () {
    return (this.j > 0);
};

Text.prototype.gotoIGT = function () {
    window.location = 'igt.' + this.i + '/edit';
};

Text.prototype.editAudio = function () {
    window.location = 'xscript/edit.' + this.i;
};

Text.prototype.edit = function () {
    this.panel.editbox.open(this);
};

Text.prototype.save = function (ascii) {
    this.panel.server.requestSave(this, ascii);
};

// callback from server
Text.prototype.finishSave = function (ascii, unicode) {
    this.setContents(ascii, unicode);
    this.par.finishSave();
    this.endEdit();
};

Text.prototype.endEdit = function () {
    var box = this.panel.editbox;
    if (box.text === this) {
	box.close();
    }
};

Text.prototype.setContents = function (ascii, unicode) {
    this.ascii = ascii;
    var elt = this.elt;
    if (ascii === '') elt.style.padding = '7';
    else elt.style.padding = '2';
    elt.textContent = unicode;
    if (this.buttonBar) {
	elt.insertBefore(this.buttonBar.elt, elt.firstChild);
    }
};

Text.prototype.insertBefore = function () {
    return this.panel.insertText('', this.i);
};

Text.prototype.delete = function () {
    if (this.par.status === 'new')
	this.finishDelete();
    else
	this.panel.server.requestDelete(this);
};

// callback from server
Text.prototype.finishDelete = function () {
    this.endEdit();
    this.panel.deleteRow(this.i);
};

Text.prototype.next = function () {
    return this.panel.nextText(this.i, this.j);
};

Text.prototype.nextRow = function () {
    return this.panel.nextRowText(this.i);
};

Text.prototype.focus = function () {
    this.elt.focus();
};


//--  ButtonBar  ---------------------------------------------------------------

function ButtonBar (text) {
    this.text = text;
    this.elt = document.createElement('span');

    var bar = this.elt;
    if (text.isTranslation()) {
	if (text.isEditable()) {
	    bar.appendChild(Element.littleButton('edit', ButtonBar.clickLittleEdit, text));
	}
    }
    else if (text.isTranscription()) {
	bar.appendChild(Element.littleButton('audio', ButtonBar.clickLittleAudio, text));
	bar.appendChild(Element.littleButton('igt', ButtonBar.clickLittleIgt, text));
    }
    else if (text.isEditable()) {
	bar.appendChild(Element.littleButton('+', ButtonBar.clickLittlePlus, text));
	bar.appendChild(Element.littleButton('edit', ButtonBar.clickLittleEdit, text));
	bar.appendChild(Element.littleButton('igt', ButtonBar.clickLittleIgt, text));
	bar.appendChild(Element.littleButton('X', ButtonBar.clickLittleX, text));
    }
    bar.style.float = 'right';
}

ButtonBar.clickLittlePlus = function (evt) {
    var text = evt.target.control;
    text.insertBefore().edit();
    evt.stopPropagation();
    return false;
};

ButtonBar.clickLittleEdit = function (evt) {
    var text = evt.target.control;
    text.edit();
    evt.stopPropagation();
    return false;
};

ButtonBar.clickLittleAudio = function (evt) {
    var text = evt.target.control;
    text.editAudio();
    evt.stopPropagation();
    return false;
};

ButtonBar.clickLittleX = function (evt) {
    var text = evt.target.control;
    text.delete();
    evt.stopPropagation();
    return false;
};

ButtonBar.clickLittleIgt = function (evt) {
    var text = evt.target.control;
    text.gotoIGT();
    evt.stopPropagation();
    return false;
};


//--  Par  ---------------------------------------------------------------------
//
//  A Par is a pair of Texts.  It is the unit of interchange with the server.
//
//  A Par's status may be:
//   - old (already exists on disk)
//   - new (just added, not yet saved)
//   - saving (waiting for server response).
//

function Par (panel, i, status) {
    this.panel = panel;
    this.i = i;
    this.texts = new Array();  // a list: [text1, text2]
    // 'old' = on disk; 'new' = not on disk; 'saving' = waiting for response
    this.status = status;
}

// Passed on from one of the cells

Par.prototype.finishSave = function () {
    this.status = 'old';
};


//--  PlainTextPanel  ----------------------------------------------------------
//
// Entry point: new PlainTextPanel(w,t)
//  - w is true if this is an original text (not derived from a
//    transcription) and the user has write permission.
//  - t is true if this text is derived from a transcription.  If t is true,
//    then w must be false.
//

export default function main (writable, transcribed) {
    new PlainTextPanel(writable, transcribed);
}

export function PlainTextPanel (writable, transcribed) {

    var div = document.getElementById('textdiv');
    var table = div.firstElementChild;
    var ncols = table.rows[0].cells.length;

    this.writable = writable;
    this.transcribed = transcribed;
    this.elt = table;
    this.ncols = ncols;
    this.plusButton = null;
    this.server = new Server();
    this.editbox = new EditBox();

    // Initialize existing cells
    var rows = table.rows;
    for (var i = 0; i < rows.length; ++i) {
	var cells = rows[i].cells;
	var par = new Par(this, i, 'old');
	// cell 0 contains the row number
	for (var k = 1; k < cells.length; ++k) {
	    var cell = cells[k];
	    var p = cell.firstChild;
	    var ascii = Element.htmlValueDecode(p.getAttribute('data-value'));
	    var text = new Text(par, k-1, ascii, p);
	    cell.text = text;
	    par.texts[k-1] = text;
	}
    }

    // Add-button
    if (writable) {
	var button = Element.button('+', PlainTextPanel.clickPlusButton, this);
	div.appendChild(Element.par(button));
	this.plusButton = button;
    }
}

PlainTextPanel.clickPlusButton = function (evt) {
    var table = evt.target.control;
    var text = table.appendRow();
    text.edit();
};

PlainTextPanel.prototype.insertText = function (ascii, i) {
    var row = this.elt.insertRow(i);

    var cell = row.insertCell(-1);
    cell.appendChild(document.createTextNode('' + i));
    cell.className = 'parno';

    var tgtText;
    var par = new Par(this, i, 'new');
    for (var k = 1; k < this.ncols; ++k) {
	var text = new Text(par, k-1, ascii);
	par.texts[k-1] = text;
	if (k === 1) tgtText = text;
	ascii = '';
	cell = row.insertCell(-1);
	cell.className = 'par';
	cell.appendChild(text.elt);
	cell.text = text;
    }
    this.updateIndices(i+1);
    return tgtText;
};

PlainTextPanel.prototype.appendRow = function () {
    var i = this.elt.rows.length;
    return this.insertText('', i);
};

PlainTextPanel.prototype.deleteRow = function (i) {
    this.elt.deleteRow(i);
    this.updateIndices(i);
};

PlainTextPanel.prototype.updateIndices = function (i) {
    var rows = this.elt.rows;
    while (i < rows.length) {
	var cells = rows[i].cells;
	// cell 0 shows the row number
	cells[0].firstChild.textContent = i;
	for (var k = 1; k < this.ncols; ++k) {
	    var cell = cells[k];
	    cell.text.i = i;
	}
	++i;
    }
};

PlainTextPanel.prototype.nextText = function (i, j) {
    var k = j+1;
    k += 1;
    if (k >= this.ncols) {
	i += 1;
	k = 1;
    }
    var rows = this.elt.rows;
    if (i >= rows.length) return null;
    return rows[i].cells[k].text;
};

PlainTextPanel.prototype.nextRowText = function (i) {
    i += 1;
    var rows = this.elt.rows;
    if (i >= rows.length) return null;
    return rows[i].cells[1].text;
};

console.log('PlainTextPanel.js loaded');
