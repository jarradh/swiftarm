function SceneMain() {
	this.items_per_page = 4;
}

// Global variables.
var names           = new Array();
var trackers        = new Array();
var hashes          = new Array();
var playlist        = [];
var downloading     = false;
var download_path   = '/dtv/usb/sda1';

SceneMain.prototype.initialize = function () {
	this.data = [
		'Browse',
		'Downloads',
		'Player',
		'Settings',
	];
	
	var listdata = [];
	for (var i = 0; i < this.data.length; i++) {
		listdata.push(this.data[i]);
	}
	
	$('#scene_list').sfList({
		data: listdata,
		index: 0,
		itemsPerPage: this.items_per_page
	});
	
	$('#label').sfLabel({
		text: 'Swift P2P TV'
	});
	$('#label_video').sfLabel({text: ""});
	
	$('#label').sfLabel('hide');
	$('#label_video').sfLabel('hide');
	
	$('#app_layout').sfBackground({
		light: false,
		column: null,
		columnShadow: true,
		columnSize: 350
	});
	
	this.defaultOpts = {
		light: false,
		column: null,
		columnShadow: true,
		columnSize: 350 / 720 * curWidget.height
	}
}

SceneMain.prototype.handleShow = function (data) {
	$('#loading').sfLoading('show');
	// TODO: Show eyecandy while waiting for load.
	sf.scene.show('Browse');
	setTimeout(function() { sf.scene.hide('Browse'); sf.scene.show('Player');}, 3000);
	setTimeout(function() { sf.scene.hide('Player'); sf.scene.show('Settings');}, 5000);
	setTimeout(function() { sf.scene.hide('Settings'); sf.scene.show('Downloads');}, 7000);
	setTimeout(function() { sf.scene.hide('Downloads'); $('#loading').sfLoading('hide'); sf.scene.show('Start');}, 9000);
}

SceneMain.prototype.handleHide = function () {}

SceneMain.prototype.handleFocus = function () {
	var index = $('#scene_list').sfList('getIndex');
	// Hide whatever scene was focused on.
	sf.scene.hide(this.data[index]);
	
	// TODO: change to javascript variable.
	if ($('#label_redirect').sfLabel("get").text()) {
		$('#label_redirect').sfLabel('hide');
		
		// Redirect to Player scene.
		$('#scene_list').sfList('move', 2);
		sf.scene.show('Player');
		
		// Hide components of Main scene.
		$('#scene_list').sfList('blur'); 
		$('#scene_list').sfList('hide');
		$('#label').sfLabel('hide');
		$('#app_layout').sfBackground(this.defaultOpts);
		sf.scene.focus('Player');
	
	} else {
		$('#scene_list').sfList('focus');
		$('#label').sfLabel('show');
		$('#keyhelp_bar').sfKeyHelp({
			'enter': 'Enter',
			'move':'Move',
			'return': 'Quit',
		});
		
		$('#app_layout').sfBackground('option', 'column', 'left');
		$('#app_layout').sfBackground(this.defaultOpts);
		$('#app_layout').sfBackground('option', 'column', 'left');
	}
}

SceneMain.prototype.handleBlur = function () {
	$('#label').sfLabel('hide');
	$('#app_layout').sfBackground(this.defaultOpts);
}

SceneMain.prototype.handleKeyDown = function (keyCode) {
	switch (keyCode) {
		case sf.key.RIGHT:
		case sf.key.ENTER:
			$('#background_image').sfImage('hide');
			var index = $('#scene_list').sfList('getIndex');
			sf.scene.show(this.data[index]);
			$('#scene_list').sfList('blur');
			$('#scene_list').sfList('hide');
			$('#label').sfLabel('hide');
			$('#app_layout').sfBackground(this.defaultOpts);
			sf.scene.focus(this.data[index]);
			break;
		
		case sf.key.UP:
			$('#scene_list').sfList('prev');
			break;
		
		case sf.key.DOWN:
			$('#scene_list').sfList('next');
			break;
		
		case sf.key.RETURN:
			var _THIS_ = this;
			var exit = false;
			$('#popupExit').sfPopup({
					text:"Do you really want to exit the application?",
					buttons: ["Yes", "No"],
					defaultFocus: 1,
					keyhelp: {'return' : 'Return'},
					callback : function (selectedIndex){
						if (selectedIndex == 0) {
							exit = true;
						}
					}
			}).sfPopup('show');
			
			if (!exit)
				sf.key.preventDefault();
			else
				widgetApi.sendReturnEvent();
				//sf.core.exit(false);
			break;
			
		default:
			break;
	}
}

