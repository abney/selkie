
import Ajax from "/.lib/ajax.js";
import Factory from "/.lib/util.js";

var make = new Factory();


//==============================================================================
//  LexentViewer.js
//==============================================================================

//--  Server  ------------------------------------------------------------------
//
//  var server = new Server(viewerURL);
//  server.call('page', form, myCallback);
//

function Server (viewerURL) {
    this.ajax = new Ajax();
    this.form1 = new FormData();
    this.form2 = new FormData();
    this.viewerURL = viewerURL;
}

//
//  Issues a get_contents request, routes the response to panel.finishContents.
//
Server.prototype.requestContents = function (panel, form, sense, gloss) {
    var args = this.form1;
    args.set('form', form);
    args.set('sense', sense);
    args.set('gloss', gloss);
    this.ajax.call(this.viewerURL + '/get_contents', args, function (spec) {
	    panel.finishContents(JSON.parse(spec));
	});
};


//  The ajax object calls the URL 'page' with the given form data.
//  To create a form:
//
//      var form = new FormData();
//      form.set('x', x);
//      form.set('y', y);
//  
//  When ajax receives a response, it calls:
//
//      myCallback(responseText)
//
//  ajax.call() returns immediately.  To arrange for a function to be
//  called after the the response is received and processed:
//
//      ajax.next(f)
//

// function Ajax () {
//     var ajax = {};
//     var request = new XMLHttpRequest();
//     var callback = null;
//     var queue = [];
// 
//     ajax.toString = function () { return "[Ajax]"; }
// 
//     function receive () {
//         if (request.readyState === XMLHttpRequest.DONE) {
//             if (request.status === 200) {
// 		var f = callback;
// 		callback = null;
// 		if (f !== null)
// 		    f(request.responseText);
// 		while (callback === null && queue.length > 0) {
// 		    f = queue.shift();
// 		    f();
// 		}
//             }
//         }
//     }
// 
//     request.onreadystatechange = receive;
// 
//     ajax.call = function (url, form, f) {
//         callback = f;
//         request.open('POST', url);
//         request.send(form);
//     }
// 
//     ajax.next = function (f) {
// 	if (callback === null) f();
// 	else queue.push(f);
//     }
// 
//     return ajax;
// }
// 
// ajax = Ajax();
// 
// console.log('ajax.js loaded');


//--  Lexical fields  ----------------------------------------------------------

var lexicalFieldNames = ['gloss', '=', 'morph', 'variety', 'source', 'variants', 'derived'];
var lexicalFieldEditable = [true, true, true, true, true, false, false];
var lexicalFieldIsXRef = [false, true, true, false, false, true, true];


//--  Lexent object  -----------------------------------------------------------
//
//  A Lexent object is built from a LexentFields object (from ajax, JSON.parse)
//  It contains a LexentBoxElement, which contains:
//    - LexentViewerElement
//    - LexentEditorElement
//  One is always hidden.
//  
//  <div class="lemmaBox bordered">
//    FORM.SENSE [edit/view button] [close button]<br/>
//    <div class="lemmaEditor"> ... </div>
//    <div class="lemmaViewer"> ... </div>
//  </div>

function Lexent (panel, fields) {
    this.panel = panel;
    this.index = fields.index;
    this.lemma = fields.lemma;
    this.seqno = fields.seqno;
    delete fields.index;
    delete fields.lemma;
    delete fields.seqno;
    this.fields = fields;
    this.visible = false;
    this.editing = false;
    this.element = null;
    this.toggles = [];

    var key = this.lemma + '.' + this.seqno;
    var xref = panel.lexents[key];
    if (xref !== undefined) {
	if (XRef.prototype.isPrototypeOf(xref)) {
	    var toggles = xref.toggles;
	    for (var i = 0; i < toggles.length; ++i) {
		var toggle = toggles[i];
		this.toggles.push(toggle);
		toggle.lexent = this;
	    }
	}
	else console.log('Duplicate:', this);
    }
    panel.lexents[key] = this;
    this.element = this.makeRootDiv();
}

Lexent.prototype = {

    key () { return this.lemma + '.' + this.seqno; },
    gloss () { return this.fields['0']; },

    makeRootDiv () {
	var div = document.createElement('div');
	div.lexent = this;
	div.className = 'lemmaBox bordered';
	div.appendChild(document.createTextNode(this.lemma + '.' + this.seqno));

	var writable = this.panel.writable;

	var bar = make.LittleButtonBar();
	if (writable)
	    bar.appendChild(make.LittleButton('edit', this.toggleEditView, this));
	bar.appendChild(make.LittleButton('goto', this.gotoEntry, this));
	bar.appendChild(make.LittleButton('conc', this.concordance, this));
	if (writable)
	    bar.appendChild(make.LittleButton('X', this.closeLexent, this));
	div.appendChild(bar);

	div.editor = this.makeLexentEditor();
	div.viewer = this.makeLexentViewer();
        div.appendChild(div.viewer);
	return div;
    },

    makeLexentEditor () {
	var fields = this.fields;
	var row, cell, cell2, box, button, hidden;
        var div = document.createElement('div');
	div.className = 'lemmaEditor';
	var form = document.createElement('form');
	form.action = this.panel.viewerURL + '/save_lemma';
	form.method = 'POST';
	form.enctype = 'multipart/form-data';
	var table = document.createElement('table');
	table.className = 'lemmaTable';
	for (var key in fields) {
	    var idx = parseInt(key);
	    var value = fields[key];
	    row = document.createElement('tr');
	    cell = document.createElement('td');
	    cell.appendChild(document.createTextNode(lexicalFieldNames[idx]));
	    row.appendChild(cell);
	    cell = document.createElement('td');
	    if (lexicalFieldEditable[idx]) {
		box = document.createElement('input');
		box.type = 'text';
		box.name = idx;
		box.value = value;
		box.size = '60';
		if (idx === 1) {
		    box.pattern = '\\S*';
		}
		cell.appendChild(box);
	    }
	    else cell.appendChild(this.makeViewField(idx, value));
	    row.appendChild(cell);
	    table.appendChild(row);
        }

	// the add-field row
	row = document.createElement('tr');
	cell = document.createElement('td');
	button = document.createElement('select');
	for (var i = 0; i < lexicalFieldNames.length; ++i) {
	    if (lexicalFieldEditable[i] && fields[i] === undefined) {
		var name = lexicalFieldNames[i];
		button.options.add(new Option(name, i));
	    }
	}
	cell.appendChild(button);
	row.appendChild(cell);
	cell = document.createElement('td');
	button = document.createElement('input');
	button.type = 'button';
	button.value = 'add field';
	button.lexent = this;
	button.onclick = this.addField;
	cell.appendChild(button);
	row.appendChild(cell);
	table.appendChild(row);

	// the save button row
	row = document.createElement('tr');
	cell = document.createElement('td');
	cell.setAttribute('colspan', '2');
	button = document.createElement('input');
	button.type = 'submit';
	button.name = 'submit';
	button.value = 'save';
	cell.appendChild(button);

	row.appendChild(cell);
	table.appendChild(row);
	form.appendChild(table);

	hidden = document.createElement('input');
	hidden.type = 'hidden';
	hidden.name = 'lemma';
	hidden.value = this.lemma;
	form.appendChild(hidden);
	hidden = document.createElement('input');
	hidden.type = 'hidden';
	hidden.name = 'seqno';
	hidden.value = this.seqno;
	form.appendChild(hidden);
        div.appendChild(form);
	return div;
    },

    makeLexentViewer () {
	var fields = this.fields;
	var row, cell, cell2, box, button, hidden;
        var div = document.createElement('div');
	div.className = 'lemmaEditor';
	var table = document.createElement('table');
	table.className = 'lemmaTable';
	for (var key in fields) {
	    var idx = parseInt(key);
	    var value = fields[key];
	    row = document.createElement('tr');
	    cell = document.createElement('td');
	    cell.appendChild(document.createTextNode(lexicalFieldNames[idx]));
	    row.appendChild(cell);
	    cell = document.createElement('td');
	    cell.appendChild(this.makeViewField(idx, value));
	    row.appendChild(cell);
	    table.appendChild(row);
        }
        div.appendChild(table);
	return div;
    },

    makeViewField (idx, value) {
	if (lexicalFieldIsXRef[idx]) {
	    var xrefs = value.split(' ');
	    var span = document.createElement('span');
	    var panel = this.panel;
	    for (var i = 0; i < xrefs.length; ++i) {
		var label = xrefs[i];
		var lexent = panel.internLexent(label);
		var toggle = new LexentToggle(panel, label, lexent);
		if (i > 0) span.appendChild(document.createTextNode(' '));
		span.appendChild(toggle.element);
	    }
	    return span;
	}
	else {
	    return document.createTextNode(value);
	}
    },

    toggleEditView (evt) {
	// this: the edit/view button
	var lexent = this.target;
	if (lexent.editing) {
	    this.firstChild.nodeValue = 'edit';
	    var div = lexent.element;
	    div.replaceChild(div.viewer, div.editor);
	    lexent.editing = false;
	}
	else {
	    this.firstChild.nodeValue = 'view';
	    var div = lexent.element;
	    div.replaceChild(div.editor, div.viewer);
	    lexent.editing = true;
	}
    },

    concordance (evt) {
	// this: the conc button
	var lexent = this.target;
	//window.location = lexent.panel.langURL + 'conc.' + lexent.index;
	window.location = 'conc.' + lexent.index;
    },

    gotoEntry (evt) {
	// this: the button
	var lexent = this.target;
	window.location = lexent.panel.langURL + '/lexicon/entry.' + lexent.index;
    },

    closeLexent (evt) {
	// this: the closeButton
	var lexent = this.target;
	var panel = lexent.panel;
	lexent.deactivate();
    },

    addField (evt) {
	// this: the 'add field' button
	var button = this;
	var lexent = button.lexent;

	var addButtonRow = button.parentNode.parentNode;
	var select = addButtonRow.children[0].children[0];
	var i = select.selectedIndex;
	var code = select.options[i].value;
	select.options.remove(i);
	var row = document.createElement('tr');
	var cell = document.createElement('td');
	cell.appendChild(document.createTextNode(lexicalFieldNames[code]));
	row.appendChild(cell);
	cell = document.createElement('td');
	var box = document.createElement('input');
	box.type = 'text';
	box.size = '60';
	box.name = code;
	cell.appendChild(box);
	row.appendChild(cell);
	addButtonRow.parentNode.insertBefore(row, addButtonRow);
    },

    activate () {
	if (this.visible) console.log('Already visible:', this);
	else {
	    this.panel.element.appendChild(this.element);
	    this.visible = true;
	    var toggles = this.toggles;
	    for (var i = 0; i < toggles.length; ++i) {
		toggles[i].element.className = 'toggleSpan selected';
	    }
	}
    },

    deactivate () {
	if (this.visible) {
	    this.panel.element.removeChild(this.element);
	    this.visible = false;
	    var toggles = this.toggles;
	    for (var i = 0; i < toggles.length; ++i) {
		toggles[i].element.className = 'toggleSpan';
	    }
	}
	else console.log('Not visible:', this);
    }
};


//--  XRef  --------------------------------------------------------------------
//
//  An XRef is used for lexents that occur in a field of another lexent,
//  but are not in the initial group that came from fetching the token.
//
//  When we need the lexent element, we must fetch it from the server and
//  replace the XRef.
//

function XRef (panel, key) {
    var i = key.lastIndexOf('.');
    this.panel = panel;
    this.form = key.substring(0,i);
    this.sense = parseInt(key.substring(i+1, key.length));
    this.toggles = [];
    this.visible = false;

    if (panel.lexents[key]) console.log('Duplicate lexent', key);
    else panel.lexents[key] = this;
}

XRef.prototype = {

    activate () {
	this.panel.getLexent(this.form, this.sense);
    }
};


//--  LexentToggle  ------------------------------------------------------------

function LexentToggle (panel, label, lexent) {
    this.panel = panel;
    this.lexent = lexent;
    this.element = this.makeSpan(label);
    lexent.toggles.push(this);
}

LexentToggle.prototype = {

    makeSpan (label) {
	var span = document.createElement('span');
	if (this.lexent.visible) span.className = 'toggleSpan selected';
	else span.className = 'toggleSpan';
	span.toggle = this;
	span.appendChild(document.createTextNode(label));
	span.onclick = this.toggle;
	return span;
    },

    toggle (evt) {
	// this: the span
	var toggle = this.toggle;
	var lexent = toggle.lexent;
	if (lexent.visible) lexent.deactivate();
	else lexent.activate();
    }
};


//--  LexentPanel  -------------------------------------------------------------
//
//  igtEditor provides methods:
//      getKey() -> form '.' sense
//      getLocation(), fetchLexent()
//
//  'entlists' is the JSON rendering of the LexentPanel in cld/ui.py.
//
//  Renders in HTML as a list of header paragraphs followed by a list of Lexents.
//  The header paragraphs are: Senses, Sim.forms, Sim.glosses.
//

//
//  IGTEditor (seal.cld.corpus.igt) creates a LexentPanel with viewerURL
//  'edit/lexentViewer'.  In IGTEditor.js, clicking on a token in the IGT
//  generates a call to LexentPanel.displayForm(ascii_form, seqno).
//

export default function LexentPanel (viewerURL, langURL, writable) {
    this.title = null;
    this.viewerURL = viewerURL;
    this.langURL = langURL;
    this.writable = writable;
    this.lexents = {};
    this.toggles = [];
    this.element = null;
    this.getContentsData = new FormData();
    this.getLexentData = new FormData();
    this.div = document.getElementById('lexentViewer');
    this.ajax = Ajax();
}

//
//  The toplevel call.  Called by IGTEditor.js when a token is selected.
//

LexentPanel.prototype.displayForm = function (form, sense) {
    this.display1(form, sense, null);
};

LexentPanel.prototype.displayGloss = function (gloss) {
    this.display1(null, null, gloss);
};

//
//  Either gloss is null, or form and sense are null.
//
LexentPanel.prototype.display1 = function (form, sense, gloss) {
    if (this.element !== null) console.log('Lexents already set!');
    else {
	if (form === null) form = '';
	if (sense === null) sense = '';
	if (gloss === null) gloss = '';
	var panel = this;
	var data = this.getContentsData;
	data.set('form', form);
	data.set('sense', sense);
	data.set('gloss', gloss);
	this.ajax.call(this.viewerURL + '/get_contents', data, function (spec) {
		panel.setContents(JSON.parse(spec));
	    });
    }
};

// Do it from a JSON spec.  Callback, also called directly by
// seal.cld.ui.LexentViewer.
    
LexentPanel.prototype.setContents = function (spec) {
    var oldElement = this.element;
    this.title = spec.title;
    this.makeLexents(spec.lexents);
    this.element = this.makeDiv(spec);
    for (var i = 0; i < spec.senses.length; ++i) {
	this.toggles[i].lexent.activate(); // no-op if already active
    }
    if (oldElement === null) this.div.appendChild(this.element);
    else this.div.replaceChild(this.element, this.oldElement);
};

LexentPanel.prototype.makeLexents = function (specs) {
    for (var i = 0; i < specs.length; ++i) {
	new Lexent(this, specs[i]);
    }
};

LexentPanel.prototype.internLexent = function (key) {
    var lexent = this.lexents[key];
    if (lexent === undefined) return new XRef(this, key);
    else return lexent;
};

LexentPanel.prototype.makeDiv = function (spec) {
    var panel = this;
    var div = document.createElement('div');
    div.className = 'groupingDiv';

    if (this.title !== '') {
	var h3 = document.createElement('h3');
	h3.textContent = this.title;

	var button = document.createElement('input');
	button.type = 'button';
	button.value = 'Lexicon';
	button.onclick = function (evt) { window.location = panel.langURL + '/lexicon/search'; };
	button.style.float = 'right';
	h3.appendChild(button);

	div.appendChild(h3);
    }

    var p = document.createElement('p');
    p.appendChild(document.createTextNode('Senses:'));
    this.createToggles(p, spec.senses, false);
    div.appendChild(p);

    if (spec.similar.length > 0) {
	p = document.createElement('p');
	p.appendChild(document.createTextNode('Similar:'));
	this.createToggles(p, spec.similar, false);
	div.appendChild(p);
    }

    if (spec.glosses.length > 0) {
	p = document.createElement('p');
	p.appendChild(document.createTextNode('Glosses:'))
	this.createToggles(p, spec.glosses, true);
	div.appendChild(p);
    }

    return div;
};

LexentPanel.prototype.createToggles = function (p, specs, glosses) {
    var i, p, spec, key, label, toggle, gloss, prevGloss = null;
    for (i = 0; i < specs.length; ++i) {
	spec = specs[i];
	key = spec[0] + '.' + spec[1];
	if (i === 0 || spec[0] !== specs[i-1][0])
	    label = key;
	else
	    label = spec[1];
	toggle = this.makeToggle(label, key);
	if (glosses === true) {
	    gloss = toggle.lexent.gloss();
	    if (prevGloss === null || gloss !== prevGloss) {
		p.appendChild(document.createTextNode(" '" + gloss + "'"));
	    }
	    prevGloss = gloss;
	}
	p.appendChild(document.createTextNode(' '));
	p.appendChild(toggle.element);
    }
};

LexentPanel.prototype.makeToggle = function (label, key) {
    var lexent = this.lexents[key];
    var toggle = new LexentToggle(this, label, lexent);
    this.toggles.push(toggle);
    return toggle;
};

// when an XRef is clicked

LexentPanel.prototype.getLexent = function (form, sense) {
    var panel = this;
    var data = this.getLexentData;
    data.set('form', form);
    data.set('sense', sense);
    this.ajax.call(this.viewerURL + '/get_lexent', data, function (spec) {
	    var lexent = new Lexent(panel, JSON.parse(spec));
	    lexent.activate();
	});
};

console.log('LexentViewer.js is loaded');
