//==============================================================================
//  util.js
//==============================================================================

//--  HTML value  --------------------------------------------------------------

var htmlValueDecodeTable = {'&amp;': '&', '&quot;': '"'};

function htmlValueDecode (s) {
    s.replace(/&amp;|&quot;/g, function (t) { return htmlValueDecodeTable[t]; });
}


//--  Elements  ----------------------------------------------------------------

function makeLittleButtonBar () {
    var span = document.createElement('span');
    span.style.float = 'right';
    return span;
}

function makeLittleButton (text, callback, target) {
    var button = document.createElement('span');
    button.className = 'littleButton';
    button.appendChild(document.createTextNode(text));
    button.onclick = callback;
    button.target = target;
    return button;
}

function makeSubmitButton (value) {
    var button = document.createElement('input');
    button.type = 'submit';
    button.name = 'submit';
    button.value = value;
    return button;
}

function makeButton (text, callback, target) {
    var button = document.createElement('input');
    button.type = 'button';
    button.value = text;
    button.onclick = callback;
    button.target = target;
    return button;
}

function makeTextBox (name, value) {
    var box = document.createElement('input');
    box.type = 'text';
    box.size = 60;
    box.name = name;
    box.value = value;
    return box;
}

function makeTextArea (name, value) {
    var elt = document.createElement('textarea');
    elt.rows = 10;
    elt.cols = 57;
    elt.name = name;
    elt.value = value;
    return elt;
}
