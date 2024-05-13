import ajax
    ;

//==============================================================================
// XScript.js
//==============================================================================
//
// Initialization: XScript(offset)
//


//--  Utility  -----------------------------------------------------------------

function removeChildren (elt) {
    while (elt.childNodes.length > 0) {
	elt.removeChild(elt.childNodes[0]);
    }
}


//--  Media  -------------------------------------------------------------------

function Media (xscript) {
    var media = this;
    var player = document.getElementById("mediaPlayer");
    this.player = player;
    this.clip = null;
    this._startAt = null;
    this._stopAt = null;

    player.ondurationchange = function () {
	xscript._setDuration(player.duration);
    }

    player.ontimeupdate = function () {
	if (media._stopAt !== null) {
	    if (player.currentTime >= media._stopAt) {
		player.pause();
		media._startAt = null;
		media._stopAt = null;
		if (media.clip !== null) {
		    media.clip.atEnd();
		    media.clip = null;
		}
	    }
        }
    }
}
    
Media.prototype.time = function () {
    return this.player.currentTime;
};

Media.prototype.duration = function () {
    return this.player.duration;
};

Media.prototype.startPlaying = function (clip) {
    this.playSpan(clip.start, null);
};

Media.prototype.stop = function () {
    this.player.pause();
};

Media.prototype.playClip = function (clip) {
    this.clip = clip;
    this.playSpan(clip.start, clip.end);
};

Media.prototype.playSpan = function (start, end) {
    //console.log('playSpan', start, end);
    var media = this;
    var player = this.player;
    media._startAt = start;
    media._stopAt = end;
    player.currentTime = start;
    player.play();

    // media.player.oncanplay = function () { media.player.play(); }
};


//--  NavCell  -----------------------------------------------------------------

var NavCell = { elt: document.getElementById('navCell') };

NavCell.update = function (start, clipsPerPage, totalNClips) {
    removeChildren(NavCell.elt);

    // we assume that start is a multiple of clipsPerPage!
    var currPage = start / clipsPerPage;
    var rmdr = totalNClips % clipsPerPage;
    var lastPage = (totalNClips - rmdr) / clipsPerPage;

    NavCell.current = currPage;
    NavCell.clipsPerPage = clipsPerPage;

    var i;
    if (currPage > 0) {
	NavCell.button(0);
	i = currPage - 5;
	if (i > 1) NavCell.ellipsis();
	else i = 1;
	while (i < currPage) NavCell.button(i++);
    }
    NavCell.addCurrent();
    i = currPage + 1;
    if (i <= lastPage) {
	var stop = i + 5;
	if (stop > lastPage) stop = lastPage;
	while (i < stop) NavCell.button(i++);
	if (i < lastPage) NavCell.ellipsis();
	NavCell.button(lastPage);
    }
};

NavCell.button = function (i) {
    var start = i * NavCell.clipsPerPage;
    var button = document.createElement('input');
    button.type = 'button';
    button.className = 'thinbutton';
    button.value = i;
    button.onclick = function () { window.location = 'edit.' + start; }
    NavCell.elt.appendChild(button);
};

NavCell.ellipsis = function () {
    NavCell.elt.appendChild(document.createTextNode('...'));
};

NavCell.addCurrent = function (i) {
    NavCell.elt.appendChild(document.createTextNode(' < '));
    var button = document.createElement('input');
    button.type = 'button';
    button.className = 'thinbutton';
    button.value = NavCell.current;
    button.disabled = true;
    NavCell.elt.appendChild(button);
    NavCell.elt.appendChild(document.createTextNode(' > '));
};


//--  NavigationFrame  ---------------------------------------------------------

function NavigationFrame (xscript) {
    this.xscript = xscript;
}

NavigationFrame.prototype.update = function (start, end, totalNClips) {
    var xscript = this.xscript;
    var clipsPerPage = xscript.clipsPerPage;
    var prevStart = start - clipsPerPage;
    var nextStart = start + clipsPerPage;

    NavCell.update(start, clipsPerPage, totalNClips);

    var prevButton = document.getElementById('prevButton');
    if (prevStart >= 0) {
	prevButton.onclick = function () { window.location = 'edit.' + prevStart; }
	prevButton.disabled = false;
    }
    else {
	prevButton.disabled = true;
    }

    var nextButton = document.getElementById('nextButton');
    if (nextStart < totalNClips) {
	nextButton.onclick = function () {
	    window.location = 'edit.' + nextStart;
	}
	nextButton.disabled = false;
    }
    else {
	nextButton.disabled = true;
    }
};


//--  PlayControls  ------------------------------------------------------------

var playSymbol = String.fromCharCode(9654); // U+25b6
var cutSymbol = String.fromCharCode(9986); // U+2702 - scissors
var stopSymbol = String.fromCharCode(9632); // U+25a0

// var cutSymbol = String.fromCharCode(9889); // U+26a1 - yellow lightning bolt
// var cutSymbol = String.fromCharCode(8224); // U+2020 dagger, too small
// var stopSymbol = String.fromCharCode(9724); // U+25fc too small


function PlayControls (cell, clip) {

    var controls = this;

    // The 'Play' button
    var button = document.createElement('button');
    cell.appendChild(button);
    button.type = 'button';
    button.className = 'thinbutton';
    var playLabel = document.createTextNode(playSymbol);
    button.appendChild(playLabel);
    button.onclick = function () { controls.togglePlay(); }

    // The 'Cut' button
    button = document.createElement('button');
    cell.appendChild(button);
    button.type = 'button';
    button.className = 'thinbutton';
    label = document.createTextNode(cutSymbol);
    button.appendChild(label);
    button.disabled = true;
    button.onclick = function () { controls.cut(); }

    this.xscript = clip.xscript;
    this.clip = clip;
    this._playing = false;
    this._playLabel = playLabel;
    this._cutButton = button;
}

PlayControls.prototype.togglePlay = function () {
    if (this._playing) this.stop();
    else this.start();
};

PlayControls.prototype.start = function () {
    //console.log('start');
    this._playing = true;
    this._playLabel.nodeValue = stopSymbol;
    this._cutButton.disabled = false;
    this.clip.play();
};

PlayControls.prototype.stop = function () {
    //console.log('stop');
    this.xscript.media.stop();
    this.stopped();
};

PlayControls.prototype.stopped = function () {
    this._playing = false;
    this._playLabel.nodeValue = playSymbol;
    this._cutButton.disabled = true;
};

PlayControls.prototype.cut = function () {
    // Should never be called otherwise, but just to be safe
    if (this._playing) {
	this.togglePlay();

	var t = this.xscript.media.time() - 0.5;
	this.clip.cut(t);
    }
};


//--  BoundaryControls  --------------------------------------------------------

function ThinButton (cell, label) {
    var button = document.createElement('button');
    cell.appendChild(button);
    button.type = 'button';
    button.className = 'thinbutton';
    button.appendChild(document.createTextNode(label));
    return button;
}

function BoundaryControls (cell, clip) {
    var controls = this;

    // The left boundary button
    var lbButton = ThinButton(cell, '[');
    lbButton.onclick = function () { controls.selectPlayLeftBoundary(); }

    // The right boundary button
    var rbButton = ThinButton(cell, ']');
    rbButton.onclick = function () { controls.selectPlayRightBoundary(); }

    cell.appendChild(document.createElement('br'));

    // The left nudge button
    var lnButton = ThinButton(cell, '<');
    lnButton.onclick = function () { controls.nudge('left'); }
    lnButton.disabled = true;

    // The right nudge button
    var rnButton = ThinButton(cell, '>');
    rnButton.onclick = function () { controls.nudge('right'); }
    rnButton.disabled = true;

    // The delete button
    var dButton = ThinButton(cell, 'X');
    dButton.onclick = function () { controls.merge(); }
    dButton.disabled = true;

    // The time
    //var endTimeBox = document.createTextNode(isRight ? clip.end : clip.start);
    //cell.appendChild(endTimeBox);

    this.clip = clip;
    this.boundary = null;
    //this._endTimeBox = endTimeBox;
    this._leftBoundaryButton = lbButton;
    this._rightBoundaryButton = rbButton;
    this._leftNudgeButton = lnButton;
    this._rightNudgeButton = rnButton;
    this._deleteButton = dButton;
}

BoundaryControls.prototype.selectPlayLeftBoundary = function () {
    this.selectLeftBoundary();
    this.clip.playHead();
};

BoundaryControls.prototype.selectPlayRightBoundary = function () {
    this.selectRightBoundary();
    this.clip.playTail();
};

BoundaryControls.prototype.setDisabled = function (value) {
    this._leftNudgeButton.disabled = value;
    this._rightNudgeButton.disabled = value;
    this._deleteButton.disabled = value;
};

BoundaryControls.prototype.selectLeftBoundary = function () {
    this.boundary = 'left';
    this._leftBoundaryButton.className = 'thinbutton selected';
    this._rightBoundaryButton.className = 'thinbutton';
    this.setDisabled(false);
};

BoundaryControls.prototype.selectRightBoundary = function () {
    this.boundary = 'right';
    this._leftBoundaryButton.className = 'thinbutton';
    this._rightBoundaryButton.className = 'thinbutton selected';
    this.setDisabled(false);
};

BoundaryControls.prototype.nudge = function (dir) {
    //console.log('BoundaryControls.nudge', dir);
    var clip = this.clip;
    var xscript = clip.xscript;
    this.setDisabled(true);
    // Call back will play the bit just after the boundary
    xscript.server.nudge(clip, this.boundary, dir === 'left' ? -0.25 : +0.25);
};

// Callback, via Clip._nudged

BoundaryControls.prototype._nudged = function (boundary) {
    if (boundary === 'left')
	this.selectPlayLeftBoundary();
    else
	this.selectPlayRightBoundary();
};

BoundaryControls.prototype.merge = function () {
    var clip = this.clip;
    clip.merge(this.boundary);
};


//--  TextEditBox  -------------------------------------------------------------

function TextEditBox (xscript) {
    var controls = this;
    var box = document.createElement('input');
    box.type = 'text';
    box.size = 57;
    box.onkeypress = function (evt) { controls._keypress(evt); }
    box.onblur = function () { controls.cancelEdit(); }
    this.box = box;
    this.clip = null;
}

TextEditBox.prototype.editClip = function (clip) {
    if (this.clip) this.cancelEdit();
    var p = clip.pElt;
    this.clip = clip;
    var box = this.box;
    box.value = clip.ascii;
    p.parentNode.replaceChild(box, p);
    box.focus();
};

TextEditBox.prototype._keypress = function (evt) {
    if (evt.key === 'Escape') this.cancelEdit();
    else if (evt.key === 'Enter') this.finishEdit();
};

TextEditBox.prototype.cancelEdit = function () {
    var p = this.clip.pElt;
    var box = this.box;
    box.parentNode.replaceChild(p, box);
    this.clip = null;
};

TextEditBox.prototype.finishEdit = function () {
    var clip = this.clip;
    var ascii = this.box.value;
    this.cancelEdit();
    clip.setText(ascii);
};


//--  Clip  --------------------------------------------------------------------

var Types = ['W', 'S', 'F'];


function Clip (table, spec) {
    var clip = this;

    this.xscript = table.xscript;
    this.index = Number(spec.i);
    this.ascii = spec.ascii;
    this.start = Number(spec.start);
    this.end = Number(spec.end);
    this.para = spec.para;

    var media = table.xscript.media;

    var row = document.createElement('tr');
    table.element.appendChild(row);
    
    // clip number
    var cell = document.createElement('td');
    row.appendChild(cell);
    cell.className = 'segno';
    cell.appendChild(document.createTextNode(spec.i));
    
    // play controls
    cell = document.createElement('td');
    row.appendChild(cell);
    var playControls = new PlayControls(cell, this);
    
    // boundary controls
    cell = document.createElement('td');
    cell.className = 'recctls';
    row.appendChild(cell);
    var boundaryControls = new BoundaryControls(cell, clip);

    // new-par checkbox
//     cell.appendChild(document.createTextNode(String.fromCharCode(182)));
//     var checkBox = document.createElement('input');
//     cell.appendChild(checkBox);
//     checkBox.type = 'checkbox';
//     checkBox.checked = (spec.para == 1);
//     checkBox.onchange = function () { clip.setPara(checkBox.checked ? 1 : 0); }
    
    // drop-down menu
    cell = document.createElement('td');
    row.appendChild(cell);
    var dropDown = document.createElement('select');
    cell.append(dropDown);
    for (var i = 0; i < Types.length; ++i) {
	var item = document.createElement('option');
	item.className = 'thinoption';
	item.text = Types[i];
	if (item.text === this.para) item.selected = true;
	dropDown.add(item);
    }
    
    dropDown.onchange = function () { clip.setType(Types[dropDown.selectedIndex]); }

    // text par
    cell = document.createElement('td');
    row.appendChild(cell);
    var p = document.createElement('p');
    cell.appendChild(p);
    var textNode = document.createTextNode(spec.unicode);
    p.className = 'transcription';
    p.appendChild(textNode);
    p.onclick = function () { clip.editText(); }

    this.pElt = p;
    this._playControls = playControls;
    this._boundaryControls = boundaryControls;

    table.clips.push(this);
}

Clip.prototype.prevClip = function () {
    return this.xscript.table.getClip(this.index - 1);
};

Clip.prototype.nextClip = function () {
    return this.xscript.table.getClip(this.index + 1);
};

Clip.prototype.play = function () {
    this.xscript.media.playClip(this);
    this._boundaryControls.selectLeftBoundary();
};

// Called when playback reaches the end

Clip.prototype.atEnd = function () {
    this._playControls.stopped();
    this._boundaryControls.selectRightBoundary();
};

Clip.prototype.playHead = function () {
    var start = this.start;
    var end = this.end;
    var t = start + 0.75;
    if (t > end) t = end;
    this.xscript.media.playSpan(start, t);
};

Clip.prototype.playTail = function () {
    var start = this.start;
    var end = this.end;
    var t = end - 0.75;
    if (t < start) t = start;
    this.xscript.media.playSpan(t, end);
};

Clip.prototype.setText = function (text) {
    this.ascii = text;
    this.xscript.server.setText(this);
};

// Handles callback from server.setText()

Clip.prototype._updateUnicode = function (unicode) {
    this.pElt.textContent = unicode;
};

// Handles callback from server.nudge()

Clip.prototype._nudged = function (boundary, actual) {
    //console.log('Clip._nudged', boundary, actual, '(clip-' + this.index + ')');
    if (boundary === 'left') {
	this.start = actual;
	var prev = this.prevClip();
	if (prev !== null) prev.end = actual;
    }
    else {
	this.end = actual;
	var next = this.nextClip();
	if (next !== null) next.start = actual;
    }
    this._boundaryControls._nudged(boundary);
};

// Clip.prototype.setPara = function (value) {
//     this.para = value;
//     this.xscript.server.setPara(this.index, value);
// };

Clip.prototype.setType = function (value) {
    this.xscript.server.setType(this.index, value);
};

Clip.prototype.editText = function () {
    this.xscript.editBox.editClip(this);
};

// Server response will rebuild table.

Clip.prototype.cut = function (t) {
    this.xscript.server.cut(this, t);
};

Clip.prototype.merge = function (boundary) {
    var index = boundary === 'left' ? this.index - 1 : this.index;
    this.xscript.server.merge(index);
};


//--  ClipTable  ---------------------------------------------------------------

function ClipTable (xscript) {
    this.xscript = xscript;
    this.element = document.getElementById('clipTable');
    this.clips = null;
    this.start = null;
    this.end = null;
    this.totalNClips = null;
}

ClipTable.prototype.getClip = function (index) {
    var clips = this.clips;
    var i = index - this.xscript.clip0;
    if (i >= 0 && i < clips.length)
	return clips[i];
    else
	return null;
};

ClipTable.prototype.setDuration = function (duration) {
    this.xscript.server.setDuration(duration);
};

// Handles the callback from the server
// spec: json list, elements have atts: i start end ascii unicode

ClipTable.prototype._rebuild = function (spec) {
    //console.log('ClipTable._rebuild');
    var nav = this.xscript.nav;
    var elt = this.element;
    removeChildren(elt);
    this.clips = [];
    spec = JSON.parse(spec);
    this.start = Number(spec['start']);
    this.end = Number(spec['end']);
    this.totalNClips = Number(spec['total']);
    var clips = spec['clips'];
    for (i = 0; i < clips.length; ++i) {
	new Clip(this, clips[i]);
    }
    nav.update(this.start, this.end, this.totalNClips);
};


//--  Server  ------------------------------------------------------------------

function Server (xscript) {
    var server = this;
    this.xscript = xscript;
    this.ajax = new Ajax();
    this._loadForm = new FormData();
    this._textForm = new FormData();
    this._typeForm = new FormData();
    //this._clipForm = new FormData();
    this._nudgeForm = new FormData();
    this._cutForm = new FormData();
    this._mergeForm = new FormData();
    this._clip = null;
    this._boundary = null;
    // Callback functions
    this._updateUnicode = function (unicode) { server._clip._updateUnicode(unicode); }
    this._rebuild = function (spec) { server.xscript.table._rebuild(spec); }
    this._nudged = function (actual) { server._clip._nudged(server._boundary, Number(actual)); }
}

Server.prototype.setDuration = function (duration) {
    var xscript = this.xscript;
    var form = this._loadForm;
    form.set('clip0', xscript.clip0);
    form.set('clips_per_page', xscript.clipsPerPage);
    form.set('duration', duration);
    this.ajax.call('set_duration', form, this._rebuild);
};

// Server.prototype.setClip = function (clip) {
//     var xscript = this.xscript;
//     var form = this._clipForm;
//     form.set('index', clip.index);
//     form.set('start', clip.start);
//     form.set('end', clip.end);
//     form.set('clip0', xscript.clip0);
//     form.set('clips_per_page', xscript.clipsPerPage);
//     ajax.call('set_clip', form, this._rebuild);
// };

Server.prototype.nudge = function (clip, boundary, delta) {
    //console.log('Server.nudge', 'clip(' + clip.index + ' ' + clip.start + ' ' + clip.end + ')', boundary, delta);
    this._clip = clip;
    this._boundary = boundary;
    var form = this._nudgeForm;
    form.set('index', boundary === 'left' ? clip.index - 1 : clip.index);
    form.set('delta', delta);
    this.ajax.call('nudge', form, this._nudged);
};

Server.prototype.cut = function (clip, t) {
    this._clip = clip;
    var xscript = this.xscript;
    var form = this._cutForm;
    form.set('index', clip.index);
    form.set('t', t);
    form.set('clip0', xscript.clip0);
    form.set('clips_per_page', xscript.clipsPerPage);
    this.ajax.call('cut', form, this._rebuild);
};

Server.prototype.merge = function (index) {
    var xscript = this.xscript;
    var form = this._mergeForm;
    form.set('index', index);
    form.set('clip0', xscript.clip0);
    form.set('clips_per_page', xscript.clipsPerPage);
    //console.log('Server.merge', index);
    this.ajax.call('merge', form, this._rebuild);
};

Server.prototype.setText = function (clip) {
    this._clip = clip;
    var form = this._textForm;
    form.set('index', clip.index);
    form.set('text', clip.ascii);
    this.ajax.call('set_text', form, this._updateUnicode);
};

Server.prototype.setType = function (index, value) {
    var form = this._typeForm;
    form.set('index', index);
    form.set('value', value);
    this.ajax.call('set_para', form, null);
};


//--  XScript  -----------------------------------------------------------------

function XScript (clip0, clipsPerPage) {
    this._initialized = false;
    this.clip0 = clip0;
    this.clipsPerPage = clipsPerPage;
    this.server = new Server(this);
    this.media = new Media(this);
    this.nav = new NavigationFrame(this);
    this.table = new ClipTable(this, clip0, clipsPerPage);
    this.editBox = new TextEditBox(this);

    this._initialized = true;
    this._setDuration(this.media.duration());
}

XScript.prototype._setDuration = function (duration) {
    if (this._initialized && !(duration === null || isNaN(duration))) {
	this.table.setDuration(duration);
    }
}
