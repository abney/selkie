
//
//  See editable-test.html for an example of usage
//


//--  Utility functions  -------------------------------------------------------

var htmlValueDecodeTable = {'&amp;': '&', '&quot;': '"'};

function htmlValueDecode (s) {
    return s.replace(/&amp;|&quot;/g, function (t) { return htmlValueDecodeTable[t]; });
}

function makeButton (text, onclick) {
    var btn = document.createElement('button');
    btn.setAttribute('type', 'button');
    btn.appendChild(document.createTextNode(text));
    btn.addEventListener('click', onclick);
    return btn;
}

function makePar (cnts) {
    var p = document.createElement('p');
    p.appendChild(cnts);
    return p;
}

function makeRow () {
    return document.createElement('tr');
}

function getCell (row, j) {
    return row.children[j];
}

function newCell (row, cnts) {
    var cell = document.createElement('td');
    cell.appendChild(cnts);
    row.appendChild(cell);
    return cell;
}

function replaceElement (oldElt, newElt) {
    var parent = oldElt.parentNode;
    parent.replaceChild(newElt, oldElt);
}


//--  Ajax  --------------------------------------------------------------------
//
//  Usage:
//
//      var ajax = Ajax();
//      ajax.call('handleEdit', 'edit', '1', 'my text', myCallback);
//
//  The ajax object calls the URL 'handleEdit' with the form data
//
//      [command = 'edit', elt = '1', text = 'my text'].
//
//  The commands are:
//      edit   - change the contents of an existing element
//      insert - insert a new element at the given position
//               position may be end of list
//      delete - delete the element at the given position
//  
//  When ajax receives a response, it calls:
//
//      myCallback(responseText)
//

function Ajax () {
    var ajax = {};
    var request = new XMLHttpRequest();
    var callback = null;
    var queue = [];
    var form = new FormData();

    ajax.toString = function () { return "[Ajax]"; }

    function receive () {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
		var f = callback;
		callback = null;
                f(request.responseText);
		while (callback === null && queue.length > 0) {
		    f = queue.shift();
		    f();
		}
            }
        }
    }

    request.onreadystatechange = receive;

    ajax.call = function (url, cmd, idx, rom, text, f) {
        callback = f;

	form.set('command', cmd);
	form.set('idx', idx);
	form.set('rom', rom);
        form.set('text', text);
    
        request.open('POST', url);
        request.send(form);
    }

    ajax.next = function (f) {
	if (callback === null) f();
	else queue.push(f);
    }

    return ajax;
}


//--  Multi-column container  --------------------------------------------------
//
//  selected(elt) - called when the user clicks on an element
//  appended(i)   - called when a new (empty) row is appended
//

function MCContainer (div, selected, appended) {
    var self = {};
    var roms = div.getAttribute('data-roms').split(',');
    var ncols = roms.length;
    var table = div.firstElementChild;
    self.deleteRow = deleteRow;
    if (table.firstElementChild !== null && table.firstElementChild.nodeName === 'TBODY')
	table = table.firstElementChild;
    init();
    return self;
    
    function init () {
	self.length = table.children.length;
	self.ncols = ncols;
	self.getEditable = getEditable;
	self.newEditable = newEditable;
	self.setText = setText;

	// Initialize existing editables
	for (var i = 0; i < table.children.length; ++i) {
	    for (var j = 0; j < ncols; ++j) {
		var elt = getEditable(i,j);
		initEditable(elt, elt.getAttribute('data-value'), i, j);
	    }
	}

	// Add-button
        var row = makeRow();
        var cell = newCell(row, makePar(makeButton('+', appendRow)));
        cell.setAttribute('colspan', ncols);
	table.appendChild(row);
    }

    function onclick () {
	selected(this);
    }

    // MCContainer: setText

    function setText (elt, ascii, text) {
	elt.ascii = ascii;
	if (ascii === '') elt.style.padding = '7';
	else elt.style.padding = '2';
	elt.textContent = text;
    }

    // MCContainer: getEditable

    function getEditable (i, j) {
	var row = table.children[i];
	var cell = row.children[j];
	return cell.children[0];
    }

    // MCContainer: newEditable
    // Create a new editable and insert it in the table.

    function newEditable (ascii, i, j) {
        var row = makeRow();
        var elt;
	var out;
        for (var t = 0; t < ncols; ++t) {
            if (t === j)
		out = elt = makeEditable(ascii, i, t);
            else
		elt = makeEditable('', i, t);
	    newCell(row, elt);
	}
	table.insertBefore(row, table.children[i]);
	++self.length;
	updateIndices(i+1);
	return out;
    }

    function makeEditable (ascii, i, j) {
	var elt = document.createElement('p');
	elt.setAttribute('class', 'editable');
	initEditable(elt, ascii, i, j);
	return elt;
    }

    function initEditable (elt, ascii, i, j) {
	if (ascii === '') elt.style.padding = '7';
	elt.addEventListener("click", onclick);
	elt.ascii = htmlValueDecode(ascii);
	elt.i = i;
	elt.j = j;
	elt.rom = roms[j];
    }

    // MCContainer: appendRow

    function appendRow () {
        var i = table.children.length - 1;
	var elt = newEditable('', i, 0);
        appended(elt);
    }

    // MCEditor: deleteRow

    function deleteRow (i) {
	table.removeChild(table.children[i]);
	updateIndices(i);
    }

    // MCEditor: updateIndices

    function updateIndices (i) {
	var rows = table.children;
	// last row is the '+' button
	while (i < rows.length - 1) {
	    for (var j = 0; j < ncols; ++j) {
		getEditable(i,j).i = i;
	    }
	    ++i;
	}
    }
}


//--  Multi-column editor  -----------------------------------------------------
//
//    <table>
//  0 <tr> <td><editable></td> <td><editable></td> </tr>
//  1 <tr> <td><editable></td> <td><editable></td> </tr>
//    ...
//    <tr> <td colspan="2"><button></td> </tr>
//    </table>
//

function MCEditor (div) {
    var self = {};
    var container = MCContainer(div, clickEditable, appendRow);
    var url = div.getAttribute("data-url");
    var ajax = Ajax();
    var element = null;   // the element replaced by the boxpar
    var elementIsNew = null;
    var boxpar = null;    // the textbox plus controls
    var box = null;       // the actual textbox
    var splitRemainder = null;
    self.toString = function () { return "[MCEditor, element=" + element + ", box=" + box + "]"; }
    init();
    return self;

    function init () {

	// Create box and boxpar

	box = document.createElement("textarea");
	box.rows = 10;
	box.style.width = "100%";
	box.style.marginBottom = "3px";
        box.addEventListener('keypress', keypress);

	boxpar = document.createElement('p');
	boxpar.appendChild(box);
	boxpar.appendChild(makeButton('Commit', commit));
	boxpar.appendChild(makeButton('Cancel', cancel));
	boxpar.appendChild(document.createTextNode(' | '));
	boxpar.appendChild(makeButton('Join', joinToPrev));
	boxpar.appendChild(makeButton('Delete', deleteElt));
    }
    
    // MCEditor: keypress
    // Key press handler
    
    function keypress (event) {
        if (event.key === 'Enter') {
            startNewParagraph();
            return false;
        }
	else if (event.key == 'Backspace' && box.selectionStart === 0) {
	    joinToPrev();
	    return false;
	}
        else return true;
    }

    // MCEditor: clickEditable
    // Click on an editable paragraph

    function clickEditable (elt) {
        if (element !== null) commit();
	openBox(elt, false);
        var i = box.value.length;
        box.setSelectionRange(i,i);
    }

    function openBox (elt, isNew) {
        element = elt;
	elementIsNew = isNew;
        box.value = element.ascii;
	replaceElement(element, boxpar);
        box.focus();
    }
 
    // MCEditor: appendRow
    // Click on the '+' button

    function appendRow (elt) {
	clickEditable(elt);
	elementIsNew = true;
    }

    // MCEditor: commit
    // Click the 'Commit' button
 
    function commit () {
	var ascii = box.value.trim();
	var savedValue = element.ascii;
	if (elementIsNew === true) {
	    if (ascii === '') container.deleteRow(element.i);
	    else saveAndClose(ascii);
	}
	else {
	    if (ascii === savedValue) cancel();
	    else if (ascii === '' && container.isDeletable(element))
		deleteElt();
	    else saveAndClose(ascii);
	}
    }

    // MCEditor: cancel

    function cancel () {
	closeBox();
    }

    // MCEditor: closeBox

    function closeBox () {
	replaceElement(boxpar, element);
	if (elementIsNew === true) {
	    container.deleteRow(element.i);
	}
	element = null;
	elementIsNew = null;
    }

    // MCEditor: saveAndClose

    function saveAndClose (ascii) {
	saveElt(ascii);
	ajax.next(closeBox);
    }

    // MCEditor: saveElt
    // Only does the ajax call; does not modify screen

    function saveElt (ascii) {
	var idx;
	if (container.ncols > 1) idx = '' + element.i + '.' + element.j;
	else idx = element.i;
	var action;
	if (elementIsNew === true) action = 'insert';
	else action = 'edit';
	ajax.call(url, action, idx, element.rom, ascii, function (text) {
		container.setText(element, ascii, text);
		elementIsNew = false;
	    });
    }
    
    // MCEditor: deleteElt
    // Click the 'Delete' button

    function deleteElt () {
	if (elementIsNew === false) {
	    ajax.call(url, 'delete', element.i, '', '', function (text) {
		    container.deleteRow(element.i);
		    element = null;
		    elementIsNew = null;
		});
	}
	else closeBox();
    }
    
    // MCEditor: startNewParagraph
    // Press Enter while editing
    // prefix is text before the cursor, suffix after
    //
    // If we are editing the first column, insert a new paragraph
    // If non-first col, and a para follows, move suffix to next para.
    // Else just commit.

    function startNewParagraph () {
 	var s = box.value;
 	var t = box.selectionStart;
	var i = element.i + 1;
	var j = element.j;

	if (j > 0 && i >= container.length) {
	    // editing translations, this is last one: do nothing more
	    saveAndClose(s);
	}
	else {
	    var prefix = s.substring(0,t).trim();
	    var suffix = s.substring(t).trim();

	    if (j === 0) {
		// insert new paragraph, containing the suffix
		saveAndClose(prefix);
		ajax.next(function () {
			var elt = container.newEditable(suffix, i, j);
			openBox(elt, true);
			t = suffix.length;
			box.setSelectionRange(t,t);
		    });
	    }
	    else {
		// edit the next paragraph, prepending the suffix
		saveAndClose(prefix);
		ajax.next(function () {
			var elt = container.getEditable(i,j);
			openBox(elt, false);
			var g = glue(suffix);
			t = suffix.length + g.length;
			box.value = suffix + g + box.value;
			box.setSelectionRange(t,t);
		    });
	    }
	}
    }

    // MCEditor: glue
    // Spaces to insert.

    function glue (s) {
	if (s.length === 0) return '';
	var c = s.charAt(s.length-1);
	var g = ' ';
	if (c === '.' || c === '?' || c === '!') g = '  ';
	else if (c === '"' || c === "'" || c === ')' || c === ']' || c === '}') {
	    var c2 = s.charAt(s.length-2);
	    if (c2 === '.' || c2 === '?' || c2 === '!') g = '  ';
	}
	return g;
    }

    // MCEditor: joinToPrev
    // Join to previous paragraph

    function joinToPrev () {
	if (element.i > 0) {
	    var ascii = box.value.trim();
	    var cursorPos = 0;
	    deleteElt();
	    ajax.next(function () {
		    var s = prev.ascii.trim();
		    var g = glue(s);
		    cursorPos = s.length + g.length;
		    ascii = s + g + ascii;
		    element = prev;
		    saveElt(ascii);
		});
	    ajax.next(function () {
		    box.value = ascii;
		    container.replaceChild(boxpar, element);
		    box.focus();
		    box.setSelectionRange(cursorPos, cursorPos);
		});
	}
    }
}


function activateEditables () {
    var lsts = document.getElementsByClassName('editorDiv');
    for (var i = 0; i < lsts.length; ++i) {
        MCEditor(lsts[i]);
    }
}

activateEditables();
