import ajax
    ;


//--  RomEditor  ---------------------------------------------------------------

function RomEditor (rom) {
    var editor = this;

    this.rom = rom;
    this.table = document.getElementById('main_table');
    this.plusButton = document.getElementById('plus_button');
    this.insertHandler = function (event) { editor.insertRow(event.target.index); }
    this.deleteHandler = function (event) { editor.deleteRow(event.target.index); }
    this.valueChangeHandler = function (event) { editor.valueChanged(event.target); }
    this.ajax = Ajax();
    this.form = new FormData();

    this.form.set('rom', rom);

    var button = this.plusButton;
    button.onclick = function () { editor.appendRow(); }
    button.disabled = false;

    this.activateButtons();
}

RomEditor.prototype.activateButtons = function (cls, handler) {
    var rows = this.table.rows;
    for (var i = 1; i < rows.length; i++) {

	var button = rows[i].cells[0].firstChild;
	button.index = i;
	button.value = '^';
	button.onclick = this.insertHandler;
	button.disabled = false;

	button = rows[i].cells[1].firstChild;
	button.index = i;
	button.value = 'x';
	button.onclick = this.deleteHandler;
	button.disabled = false;

	var valuebox = rows[i].cells[3].firstChild;
	valuebox.index = i;
	valuebox.onchange = this.valueChangeHandler;
    }
};

RomEditor.prototype.appendRow = function () {
    console.log('append row');
    this.insertRow(this.table.length);
};

RomEditor.prototype.insertRow = function (i) {
    console.log('insert row', i);
    var table = this.table;
    var row = table.insertRow(i);
    this.addButtonCell(row);
    this.addButtonCell(row);
    this.addTextboxCell(row, '*keys');
    this.addTextboxCell(row, '*values');
    this.addDecodeCell(row);
    this.activateButtons();
};
    
RomEditor.prototype.addTextboxCell = function (row, name) {
    var textbox = document.createElement('input');
    textbox.type = 'text';
    textbox.name = name;
    textbox.size = '20';
    var cell = row.insertCell(-1);
    cell.appendChild(textbox);
};

RomEditor.prototype.addButtonCell = function (row) {
    var button = document.createElement('input');
    button.type = 'button';
    var cell = row.insertCell(-1);
    cell.appendChild(button);
};

RomEditor.prototype.addDecodeCell = function (row) {
    var cell = row.insertCell(-1);
    cell.appendChild(document.createTextNode(''));
};

RomEditor.prototype.deleteRow = function (i) {
    this.table.deleteRow(i);
    this.activateButtons();
};

RomEditor.prototype.valueChanged = function (textbox) {
    var editor = this;
    // textbox, not index, in case it gets moved in the meantime
    var handler = function (unicode) { editor.setDecoded(textbox, unicode); }
    this.form.set('ascii', textbox.value);
    this.ajax.call('do_decode', this.form, handler);
    console.log('Sent ajax call');
};

RomEditor.prototype.setDecoded = function (textbox, unicode) {
    console.log('Received response');
    var row = this.table.rows[textbox.index];
    var cell = row.cells[4];
    cell.replaceChild(document.createTextNode(unicode), cell.firstChild);
    console.log('Done');
};
