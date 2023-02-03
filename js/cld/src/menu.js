
import React from 'react';
import './App.css';

function MenuItems (props) {
    const specs = props.items;
    const classname = 'MenuItems ' + props.visibility;
    const items = specs.map((item, i) => {
	return (
	    <li className="App-link" key={i}>{item}</li>
	)
    });
    return (
	<ul className={classname}>
	    {items}
	</ul>
    );
}

class Menu extends React.Component {

    constructor (props) {
	super(props);
	this.state = {active: false};
    }

    toggleState () {
	const active = this.state.active;
	this.setState((state, props) => ({active: !active}));
    }

    hide () {
	this.setState({active: false});
    }

    render () {
	const title = this.title;
	const items = this.items;
	const onclick = ((e) => this.toggleState());
	const onblur = ((e) => this.hide());
	const visibility = this.state.active ? 'visible' : 'hidden';
	return (
	    <div className="Menu">
		<button
		    className="MenuTitle"
		    onClick={onclick}
		    onBlur={onblur}
		>
		    {title}
		</button>
		<MenuItems visibility={visibility} items={items} />
	    </div>
	);
    }
}

export default Menu;
