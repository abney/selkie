

//--  Ajax  --------------------------------------------------------------------
//
//  Usage:
//
//      var ajax = Ajax();
//      ajax.call('edit_par', 'replace', '1', '0', 'my text', myCallback);
//
//  The ajax object calls the URL 'handleEdit' with the form data
//
//      [op = 'replace', i = '1', j = '0', text = 'my text'].
//
//  The ops are:
//      replace  - change the contents of an existing element
//      insert   - insert a new element at the given position
//                 position may be end of list
//      delete   - delete the element at the given position
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
		if (f !== null) f(request.responseText);
		while (callback === null && queue.length > 0) {
		    f = queue.shift();
		    f();
		}
            }
        }
    }

    request.onreadystatechange = receive;

    ajax.call = function (url, op, i, j, text, f) {
        callback = f;

	form.set('op', op);
	form.set('i', i);
	form.set('j', j);
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


//--  Elements  ----------------------------------------------------------------

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

function makeLittleButton (text, callback, target) {
    var button = document.createElement('span');
    button.className = 'littleButton';
    button.appendChild(document.createTextNode(text));
    button.onclick = callback;
    button.target = target;
    return button;
}

// Editables

function makeEditable (container, ascii, i, j) {
    var elt = document.createElement('p');
    elt.className = 'editable';
    initEditable(container, elt, ascii, i, j);
    return elt;
}

function editableClick (evt) {
    var elt = evt.target;
    elt.container.callbacks.clicked(elt);
}

function editableKeypress (evt) {
    var elt = evt.target;
    if (evt.key === 'Enter') {
	elt.container.callbacks.clicked(elt);
	return false;
    }
    else return true;
}

function editableFocus (evt) {
    var elt = evt.target;
}

function initEditable (container, elt, ascii, i, j) {
    if (ascii === '') elt.style.padding = '7';
    elt.container = container;
    elt.setAttribute('tabindex', 0);
    elt.onfocus = editableFocus;
    elt.onclick = editableClick;
    elt.onkeypress = editableKeypress;
    elt.ascii = htmlValueDecode(ascii);
    elt.i = i;
    elt.j = j;
    if (j === 0)
	elt.insertBefore(makeEditableButtonBar(container, elt), elt.firstChild);
}

function clickLittlePlus (evt) {
    var button = evt.target;
    var elt = button.target;
    var container = elt.container;
    elt = container.newEditable('', elt.i, 0);
    container.callbacks.created(elt);
    evt.stopPropagation();
    return false;
}

function clickLittleX (evt) {
    var button = evt.target;
    var elt = button.target;
    var container = elt.container;
    container.deleteRow(elt.i);
    container.callbacks.deleted(elt.i);
    evt.stopPropagation();
    return false;
}

function clickLittleIgt (evt) {
    var button = evt.target;
    var elt = button.target;
    window.location = '../igt/edit.' + elt.i;
    evt.stopPropagation();
    return false;
}

function makeEditableButtonBar (container, elt) {
    var bar = document.createElement('span');
    bar.appendChild(makeLittleButton('+', clickLittlePlus, elt));
    bar.appendChild(makeLittleButton('IGT', clickLittleIgt, elt));
    bar.appendChild(makeLittleButton('X', clickLittleX, elt));
    bar.style.float = 'right';
    return bar;
}

function setEditableText (elt, ascii, text) {
    elt.ascii = ascii;
    if (ascii === '') elt.style.padding = '7';
    else elt.style.padding = '2';
    if (elt.j === 0) {
	var buttonBar = elt.children[0];
	elt.textContent = text;
	elt.insertBefore(buttonBar, elt.firstChild);
    }
    else elt.textContent = text;
}

// Box, BoxPar

function makeBox (onkeypress) {
    var box = document.createElement("textarea");
    box.rows = 10;
    box.style.width = "100%";
    box.style.marginBottom = "3px";
    box.addEventListener('keypress', onkeypress);
    return box;
}

function makeBoxPar (box, oncommit, oncancel) {
    var boxpar = document.createElement('p');
    boxpar.appendChild(box);
    boxpar.appendChild(makeButton('Commit', oncommit));
    boxpar.appendChild(makeButton('Cancel', oncancel));
    return boxpar;
}


//--  Multi-column container  --------------------------------------------------
//
//  onclick(elt)  - called when the user clicks on an element
//  onappend(elt) - called when a new row is appended
//

function Container (div, callbacks) {
    var container = this;
    var table = div.firstElementChild;
    var tbody = ((table.firstElementChild !== null &&
		  table.firstElementChild.nodeName === 'TBODY') ?
		 table.firstElementChild :
		 table);
    var ncols = (table.className === 'ParallelText') ? 2 : 1;

    this.tbody = tbody;
    this.ncols = ncols;
    this.length = tbody.children.length;
    this.callbacks = callbacks;

    // Initialize existing editables
    for (var i = 0; i < tbody.children.length; ++i) {
	for (var j = 0; j < ncols; ++j) {
	    var elt = this.getEditable(i,j);
	    initEditable(this, elt, elt.getAttribute('data-value'), i, j);
	}
    }

    // Add-button
    var row = makeRow();
    var cell = newCell(row, makePar(makeButton('+', addButtonClick)));
    cell.setAttribute('colspan', ncols);
    tbody.appendChild(row);

    function addButtonClick (evt) {
	var elt = container.appendRow();
        container.callbacks.created(elt);
    }
}

Container.prototype = {

    // MCContainer: getEditable

    getEditable (i, j) {
	var row = this.tbody.children[i];
	var cell = row.children[j];
	return cell.children[0];
    },

    // Create a new editable and insert it in the table.

    newEditable (ascii, i, j) {
	var tbody = this.tbody;
        var row = makeRow();
        var elt, out;
        for (var t = 0; t < this.ncols; ++t) {
            if (t === j)
		out = elt = makeEditable(this, ascii, i, t);
            else
		elt = makeEditable(this, '', i, t);
	    newCell(row, elt);
	}
	tbody.insertBefore(row, tbody.children[i]);
	++this.length;
	this.updateIndices(i+1);
	return out;
    },

    nextEditable (elt) {
	var i = elt.i;
	var j = elt.j + 1;
	if (j >= this.ncols) {
	    ++i;
	    j = 0;
	}
	if (i >= this.length) return null;
	else return this.getEditable(i,j);
    },

    appendRow () {
        var i = this.tbody.children.length - 1;
	return this.newEditable('', i, 0);
    },

    deleteRow (i) {
	var tbody = this.tbody;
	tbody.removeChild(tbody.children[i]);
	this.updateIndices(i);
    },

    updateIndices (i) {
	var rows = this.tbody.children;
	// last row is the '+' button
	while (i < rows.length - 1) {
	    for (var j = 0; j < this.ncols; ++j) {
		this.getEditable(i,j).i = i;
	    }
	    ++i;
	}
    }
};


//--  Multi-column editor  -----------------------------------------------------
//
//    <table>
//  0 <tr> <td><editable></td> <td><editable></td> </tr>
//  1 <tr> <td><editable></td> <td><editable></td> </tr>
//    ...
//    <tr> <td colspan="2"><button></td> </tr>
//    </table>
//

function Edit () {
    var callbacks = {clicked: editableClicked,
		     created: editableCreated,
		     deleted: editableDeleted};

    var div = document.getElementById('textdiv');
    var container = new Container(div, callbacks);
    var ajax = Ajax();

    var element = null;      // the element replaced by the boxpar
    var elementIsNew = null;

    var box = makeBox(boxKeypress);                // the actual textbox
    var boxpar = makeBoxPar(box, commit, cancel);  // the textbox plus controls


    // Handlers
    
    function boxKeypress (evt) {
        if (evt.key === 'Enter') {
	    commit();
            return false;
        }
        else return true;
    }

    function eltKeypress (evt) {
	if (evt.key === 'Enter') {
	    editableClicked(evt.target);
	}
	else return true;
    }

    function editableClicked (elt) {
        if (element !== null) commit();
	openBox(elt, false);
        var i = box.value.length;
        box.setSelectionRange(i,i);
    }
 
    function editableCreated (elt) {
	editableClicked(elt);
	elementIsNew = true;
    }
    
    function editableDeleted (i) {
	ajax.call('edit_par', 'delete', i, 0, '', null);
    }

    function commit (evt) {
	var ascii = box.value.trim();
	var savedValue = element.ascii;
	var next = container.nextEditable(element);
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
	if (next !== null) select(next);
    }

    function cancel () {
	var next = container.nextEditable(element);
	closeBox();
	if (next !== null) select(next);
    }

    function deleteElt () {
	if (elementIsNew === false) {
	    ajax.call('edit_par', 'delete', element.i, element.j, '', function (text) {
		    container.deleteRow(element.i);
		    element = null;
		    elementIsNew = null;
		});
	}
	else closeBox();
    }


    // Box

    function openBox (elt, isNew) {
        element = elt;
	elementIsNew = isNew;
        box.value = element.ascii;
	replaceElement(element, boxpar);
        box.focus();
    }

    function closeBox () {
	replaceElement(boxpar, element);
	if (elementIsNew === true) {
	    container.deleteRow(element.i);
	}
	element = null;
	elementIsNew = null;
    }

    function saveAndClose (ascii) {
	saveElt(ascii);
	ajax.next(closeBox);
    }


    // Only does the ajax call; does not modify screen

    function saveElt (ascii) {
	var op;
	if (elementIsNew) op = 'insert';
	else op = 'replace';
	ajax.call('edit_par', op, element.i, element.j, ascii, function (text) {
		setEditableText(element, ascii, text);
		elementIsNew = false;
	    });
    }


    // Selection

    function select (elt) {
	elt.focus();
    }
}


Edit();
