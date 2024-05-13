//==============================================================================
//  util.js
//==============================================================================

export default class Factory {

    //--  HTML value  --------------------------------------------------------------

    htmlValueDecodeTable = {'&amp;': '&', '&quot;': '"'};

    htmlValueDecode (s) {
	s.replace(/&amp;|&quot;/g, function (t) { return htmlValueDecodeTable[t]; });
    }


    //--  Elements  ----------------------------------------------------------------

    LittleButtonBar () {
	var span = document.createElement('span');
	span.style.float = 'right';
	return span;
    }

    LittleButton (text, callback, target) {
	var button = document.createElement('span');
	button.className = 'littleButton';
	button.appendChild(document.createTextNode(text));
	button.onclick = callback;
	button.target = target;
	return button;
    }

    SubmitButton (value) {
	var button = document.createElement('input');
	button.type = 'submit';
	button.name = 'submit';
	button.value = value;
	return button;
    }

    Button (text, callback, target) {
	var button = document.createElement('input');
	button.type = 'button';
	button.value = text;
	button.onclick = callback;
	button.target = target;
	return button;
    }

    TextBox (name, value) {
	var box = document.createElement('input');
	box.type = 'text';
	box.size = 60;
	box.name = name;
	box.value = value;
	return box;
    }

    TextArea (name, value) {
	var elt = document.createElement('textarea');
	elt.rows = 10;
	elt.cols = 57;
	elt.name = name;
	elt.value = value;
	return elt;
    }
}

console.log('util.js is loaded');
