var widgetAPI = new Common.API.Widget();
var tvKey     = new Common.API.TVKeyValue();

var letters = [[",", ".", "/", "-", "_", ":", ";", "(", ")"], ["a","b","c"], ["d","e","f"], ["g","h","i"], ["j","k","l"], ["m","n","o"], ["p","q","r"], ["s","t","u"], ["v","w","x"], ["y","z"]];
var overviewLetters = [", . / - _ : ; ( )", "a, b, c", "d, e, f", "g, h, i", "j, k, l", "m, n, o", "p, q, r", "s, t, u", "v, w, x", "y, z"]
var buttonValues = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "shift", "type"];
var buttons = new Array('#zero', '#one', '#two', '#three', '#four', '#five', '#six', '#seven', '#eight', '#nine', '#shift', '#type');
var labels = new Array('#zeroletters', '#oneletters', '#twoletters', '#threeletters', '#fourletters', '#fiveletters', '#sixletters', '#sevenletters', '#eightletters', '#nineletters');

var keyStates = {
	OVERVIEW:0,
	SELECTION:1
};

var letterType = {
	LETTERS:0,
	NUMBERS:1
}

var shiftState = {
	OFF:0,
	ON:1
};

var shift = 0;
var selection = -1;
var type = 0;
var keyState = keyStates.OVERVIEW;

function init() {
	
	alert("Search init() called");
	
	for(var i = 0; i < buttons.length; i++){
		$(buttons[i]).sfButton({text:buttonValues[i]});
	}
	
	resetLetters();
	/*
	$('#one').sfButton({text:'1'});
	$('#two').sfButton({text:'2'});
	$('#three').sfButton({text:'3'});
	$('#four').sfButton({text:'4'});
	$('#five').sfButton({text:'5'});
	$('#six').sfButton({text:'6'});
	$('#seven').sfButton({text:'7'});
	$('#eight').sfButton({text:'8'});
	$('#nine').sfButton({text:'9'});
	$('#zero').sfButton({text:'0'});
	$('#shift').sfButton({text:'Shift', width:'100px'});
	$('#type').sfButton({text:'Type', width:'100px'});
	
	$('#oneletters').sfLabel({text:'a, b, c'});
	$('#twoletters').sfLabel({text:'d, e, f'});
	$('#threeletters').sfLabel({text:'g, h, i'});
	$('#fourletters').sfLabel({text:'j, k, l'});
	$('#fiveletters').sfLabel({text:'m, n, o'});
	$('#sixletters').sfLabel({text:'p, q, r'});
	$('#sevenletters').sfLabel({text:'s, t, u'});
	$('#eightletters').sfLabel({text:'v, w, x'});
	$('#nineletters').sfLabel({text:'y, z'});
	$('#zeroletters').sfLabel({text:', . / - _ : ; ( )'});
	*/
	
	this.enableKeys();
	widgetAPI.sendReadyEvent();
	alert("Search init() completed");
}

function enableKeys(){
	
	document.getElementById("anchor").focus();
}

function keyDown() {
	
	var keyCode = event.keyCode;
	switch(keyCode){
		case tvKey.KEY_RETURN:
			widgetAPI.blockNavigation();
			alert("RETURN pressed");
			gotoMain();
			break;
		case tvKey.MENU:
			alert("MENU pressed");
			gotoMain();
			break;
		case tvKey.KEY_PRECH:
			shift = (shift + 1) % 2;
			updateLetters();
		case tvKey.KEY_1:
			letterSelection(1);
			break;
		case tvKey.KEY_2:
			letterSelection(2);
			break;
		case tvKey.KEY_3:
			letterSelection(3);
			break;
		case tvKey.KEY_4:
			letterSelection(4);
			break;
		case tvKey.KEY_5:
			letterSelection(5);
			break;
		case tvKey.KEY_6:
			letterSelection(6);
			break;
		case tvKey.KEY_7:
			letterSelection(7);
			break;
		case tvKey.KEY_8:
			letterSelection(8);
			break;
		case tvKey.KEY_9:
			letterSelection(9);
			break;
		case tvKey.KEY_0:
			letterSelection(0);
			break;
		case tvKey.KEY_EMPTY:
			document.getElementById("searchBar").value = searchBarValue + " ";
			break;
		case tvKey.KEY_MUTE:
			var searchVal = document.getElementById("searchBar").value;
			document.getElementById("searchBar").value = searchVal.substring(0, searchVal.length-2);
			break;
		case tvKey.KEY_ENTER:
			// SEARCH!
			break;
		default:
			alert("Ignore Unhandled Key");
			break;
	}
}

function letterSelection(number){
	
	if(keyState == keyStates.OVERVIEW) {
		
		selection = number;
		updateLetters();
		keyState = keyStates.SELECTION;
	}
	else if(keyState == keyStates.SELECTION) {
	
		if(number <= letters[selection].length && number > 0) {
			
			var searchBarValue = document.getElementById("searchBar").value;
			// send selected letter to searchbar here
			if(shift == shiftState.OFF){
				document.getElementById("searchBar").value = searchBarValue + letters[selection][number-1];
			}
			else{
				document.getElementById("searchBar").value = searchBarValue + letters[selection][number-1].toUpperCase();
			}
			selection = -1;
			updateLetters();
			keyState = keyStates.OVERVIEW;
		}
	}
}

function updateLetters() {
	
	if(selection == -1) {
		resetLetters();
	}
	else{
		for(var j = 1; j < letters[selection].length+1; j++) {
			if(shift == shiftState.OFF){
				$(labels[j]).sfLabel({text:letters[selection][j-1]});
			}
			else{
				$(labels[j]).sfLabel({text:letters[selection][j-1].toUpperCase()});
			}
		}
		for(var i = letters[selection].length+1; i < labels.length; i++) {
			$(labels[i]).sfLabel({text:" "});
		}
	}
}

function resetLetters(){
	for(var j = 0; j < buttons.length; j++){
		if(shift == shiftState.OFF){
			$(labels[j]).sfLabel({text:overviewLetters[j]});
		}
		else{
			$(labels[j]).sfLabel({text:overviewLetters[j].toUpperCase()});
		}
	}
}

function gotoMain(){
	window.location = "index.html";
}

