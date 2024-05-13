
export default Element = {};

Element.htmlValueDecodeTable = {'&amp;': '&', '&quot;': '"'};

Element.htmlValueDecode = function (s) {
    return s.replace(/&amp;|&quot;/g, function (t) {
	    return Element.htmlValueDecodeTable[t];
	});
};

Element.button = function (text, onclick, control) {
    var button = document.createElement('button');
    button.type = 'button';
    button.appendChild(document.createTextNode(text));
    button.addEventListener('click', onclick);
    button.control = control;
    return button;
};

Element.littleButton = function (text, onclick, control) {
    var button = document.createElement('span');
    button.className = 'littleButton';
    button.appendChild(document.createTextNode(text));
    button.onclick = onclick;
    button.control = control;
    return button;
};

Element.par = function (cnts) {
    var p = document.createElement('p');
    p.appendChild(cnts);
    return p;
};

Element.replace = function (oldElt, newElt) {
    var parent = oldElt.parentNode;
    parent.replaceChild(newElt, oldElt);
};

console.log('element.js loaded');
