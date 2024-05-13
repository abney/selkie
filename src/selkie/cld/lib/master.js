
h1 = document.createElement('H1');
document.body.appendChild(h1);

h1Text = document.createTextNode('Testing');
h1.appendChild(h1Text);

button = document.createElement('button');
document.body.appendChild(button);

buttonText = document.createTextNode('Hi');
button.appendChild(buttonText);
button.addEventListener('click', hi1);

ajax = new XMLHttpRequest();
ajax.onreadystatechange = ajaxReceive;

ajaxHandler = hi2;

function ajaxReceive () {
    if (request.readyState === XMLHttpRequest.DONE && request.status === 200) {
	ajaxHandler(request.responseText);
    }
}

function hi1 (event) {
    console.log('Got a click');
    var form = new FormData();
    form.append('foo', '42');
    form.append('bar', 'yes');
    ajax.open('POST', 'callback');
    ajax.send(form);
    return false;
}

function hi2 (text) {
    console.log('Received:', text);
}
