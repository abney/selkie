import ajax

function Transcriber (offset, spec) {
    console.log('offset=', offset)
    var ajax = Ajax();
    var trs = document.getElementsByClassName('transcription');
    for (var i = 0; i < trs.length; ++i) {
	tr = trs[i];
        tr.index = offset + i;
	tr.ascii = spec[i];
	tr.onclick = editTranscription;
    }
    var box = document.createElement('input');
    box.type = 'text';
    box.size = 70;
    box.onkeypress = keypressHandler;
    box.onblur = cancelEdit;
    var elt = null;
    var form = new FormData();

    function editTranscription (evt) {
        if (elt !== null) finishEdit();
	ajax.next(function () {
		elt = evt.target;
		box.value = elt.ascii;
		elt.parentNode.replaceChild(box, elt);
		box.focus();
	    });
    }

    function keypressHandler (evt) {
	if (evt.key === 'Enter') finishEdit();
    }

    function finishEdit () {
        form.set('index', elt.index);
        form.set('text', box.value);
        ajax.call('savetrans', form, function (response) {
		elt.ascii = box.value;
		elt.textContent = response;
		box.parentNode.replaceChild(elt, box);
		elt = null;
	    });
    }

    function cancelEdit () {
	box.parentNode.replaceChild(elt, box);
	elt = null;
    }
}
