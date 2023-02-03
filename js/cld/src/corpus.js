
import React from 'react';
import './App.css';

class Corpus {

    constructor () {
	const port = 8844;
	const socket = new WebSocket(`ws://localhost:${port}/websocket`);
	this.socket = socket;
	this.requests = [];
	this.readyflag = false;
    }

    get (uri) {
	return this._call('get', uri);
    }

    set (uri) {
	return this._call('put', uri);
    }

    del (uri) {
	return this._call('delete', uri);
    }

    _call (method, uri) {
	const corpus = this;
	return new Promise((resolve, reject) => {
	    corpus.requests.push([method, uri, resolve]);
	    if (corpus.requests.length === 1) {
		corpus._run()
	    }
	});
    }

    async _run () {
	while (this.requests.length > 0) {
	    const [method, uri, resolve] = this.requests[0];
	    await this._processRequest(method, uri, resolve);
	    this.requests.shift();
	}
    }

    _processRequest (method, uri, caller) {
	this._isready().then(ready => {
	    const socket = this.socket;
	    return new Promise((processed, notprocessed) => {
		socket.onmessage = (evt => {
		    console.log('[Socket] RESP', evt.data);
		    const resp = JSON.parse(evt.data);
		    processed(true);
		    caller(resp);
		})
		console.log('[Socket] REQ', uri);
		socket.send(JSON.stringify({method: method, uri: uri}));
	    });
	});
    }

    _isready () {
	const runner = this;
	return new Promise((resolve, reject) => {
	    if (runner.readyflag) {
		resolve(true);
	    } else {
		runner.socket.onopen = (() => {
		    runner.readyflag = true;
		    resolve(true);
		});
	    }
	});
    }
}

export default Corpus;
