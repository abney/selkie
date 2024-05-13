
//==============================================================================
//  ajax.js
//==============================================================================

//
//  Usage:
//
//      var ajax = Ajax();
//      ajax.call('page', form, myCallback);
//
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

export default function Ajax () {
    var ajax = {};
    var request = new XMLHttpRequest();
    var callback = null;
    var queue = [];

    ajax.toString = function () { return "[Ajax]"; }

    function receive () {
        if (request.readyState === XMLHttpRequest.DONE) {
            if (request.status === 200) {
		var f = callback;
		callback = null;
		if (f !== null)
		    f(request.responseText);
		while (callback === null && queue.length > 0) {
		    f = queue.shift();
		    f();
		}
            }
        }
    }

    request.onreadystatechange = receive;

    ajax.call = function (url, form, f) {
        callback = f;
        request.open('POST', url);
        request.send(form);
    }

    ajax.next = function (f) {
	if (callback === null) f();
	else queue.push(f);
    }

    return ajax;
}

//ajax = Ajax();

console.log('ajax.js loaded');
