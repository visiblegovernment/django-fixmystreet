Titanium.include("/js/views/newreportform.js");
Titanium.include('/js/views/setidform.js');

var win = Titanium.UI.currentWindow;
var isAndroid = (Titanium.Platform.name == 'android');
var modes = [ 		Titanium.UI.PORTRAIT, Titanium.UI.UPSIDE_PORTRAIT	];
			

win.backgroundColor = '#000';
win.orientationModes = modes;
	
var idView = null;
var newReportView = new NewReportForm();

function onIdSet()
{
	Titanium.API.info("nearby3: onIdSet");
	idView.close(win);
	newReportView.open(win);
}

var idSet = Titanium.App.Properties.getBool('IdSet');
if( idSet ) 
{
	newReportView.open(win);
}
else
{
	idView = new SetIdForm();
	idView.open(win);
}

Titanium.App.addEventListener('app_id_set',onIdSet);
