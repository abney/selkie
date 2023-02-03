
import React from 'react';
/* import ReactDOM from 'react-dom'; */
/* import logo from './logo.svg'; */
import './App.css';
import Corpus from './corpus.js';
import Menu from './menu.js';

class ViewMenu extends Menu {

    constructor (props) {
	super(props);
	this.title = 'View';
	this.items = ['Foo', 'Bar'];
    }
}

class LanguageList extends React.Component {

    render () {
	const langs = this.props.langs;
	const items = langs.map((lang,i) => {
	    const nm = lang.name;
	    return (
		<li key={i}>
		    <span className="App-link" onClick={() => this.selectLang(i)}>{nm}</span>
		</li>
	    );
	});
	return (
	    <div className="LanguageList">
		<h1>Languages</h1>
		<ul>{items}</ul>
	    </div>
	);
    }

    selectLang (i) {
	const langs = this.props.langs;
	console.log('** langs[i]=', langs[i]);
	window.app.fetchSetPage(Language, '/lang/' + langs[i].langid);
    }
}

class Language extends React.Component {
    render () {
	const langid = this.props.langid;
	const name = this.props.name;
	return (
	    <div>
		<h1>{langid} — {name}</h1>
		<Toc langid={langid} />
	    </div>
	);
    }
}

class Toc extends React.Component {

    constructor (props) {
	super(props);
	this.state = {'toc': []};
	this.fetchState();
    }

    async fetchState () {
	const langid = this.props.langid;
	const state = await window.app.fetch('/toc/' + langid);
	this.setState(state);
    }

    render () {
	const toc = this.state.toc;
	console.log('** Toc toc:', toc);
    
	const rows = toc.map((ent, i) => (
	    <tr key={i}>
		<td>{ent.textid}</td>
		<td>{ent.text_type}</td>
		<td>{ent.author}</td>
		<td>{ent.title}</td>
	    </tr>
	));
	return (
	    <table>
		{rows}
	    </table>
	);
    }
}


/* var application = null; */


class App extends React.Component {
    
    constructor (props) {
	super(props);
	window.app = this;
	this.state = {
	    page: '',
	};
	this.corpus = new Corpus();
    }

    componentDidMount () {
	this.fetchSetPage(LanguageList, '/langs');
    }

    async fetchSetPage (cls, uri) {
	const props = await this.fetch(uri);
	console.log('** fetchSetPage props:', props);
	this.setPage(cls, props);
    }
    
    async fetch (uri) {
	const resp = await this.corpus.get(uri);
	console.log('** fetch resp:', resp);
	if (resp['status'] === 'ok') {
	    return resp['value'];
	} else {	    
	    console.log('** FAILURE:', resp);
	}
    }

    async setPage (cls, props) {
	console.log('** setPage', cls, props);
	this.setState({
	    page: React.createElement(cls, props, null)
	});
    }

    render () {
	return (
	    <div className="App">
		<header className="MenuBar">
		    <ViewMenu />
		</header>
		{this.state.page}
	    </div>
	);
    }
}

export default App;
