
function Conc () {

    initialize_pars();

    function initialize_pars () {
	var pars = document.getElementsByClassName('textpar');
	for (var i = 0; i < pars.length; ++i) {
	    var par = pars[i];
	    par.onclick = handleParClick;
	}
    }

    function handleParClick (evt) {
	var par = this;
	var value = par.getAttribute('data-value');
	window.location = value;
    }
}


Conc();
