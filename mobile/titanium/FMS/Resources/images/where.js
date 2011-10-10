
var win = Ti.UI.currentWindow;
var isAndroid = false;
var locationData = null;
var mapView = null;

if (Titanium.Platform.name == 'android') {
	isAndroid = true;
}

Titanium.include('what.js');

var selectButtonBar = Titanium.UI.createButtonBar({
	labels:['Use Current Location']
});

var flexSpace = Titanium.UI.createButton({
	systemButton:Titanium.UI.iPhone.SystemButton.FLEXIBLE_SPACE
});

var backButton = Ti.UI.createButton({
    title:'Back'        
});             
 
backButton.addEventListener('click', function(){
    win.remove(scrollView);
	win.add(mapview);
	win.setToolbar([selectButtonBar]);
	win.leftNavButton = null;
});
 
selectButtonBar.addEventListener('click', function(e)
{
	win.setToolbar([]);
	win.remove(mapview);
	win.add(scrollView);
	win.leftNavButton = backButton;
});

var loadingToolbar = Titanium.UI.createActivityIndicator();
loadingToolbar.style = Titanium.UI.iPhone.ActivityIndicatorStyle.PLAIN;
loadingToolbar.font = {fontFamily:'Helvetica Neue', fontSize:15,fontWeight:'bold'};
loadingToolbar.color = 'white';
loadingToolbar.message = 'Confirmimg location...';

var promptWin = Titanium.UI.createWindow({
	height:30,
	width:250,
	bottom:70,
	borderRadius:10,
	touchEnabled:false,

	orientationModes : [
	Titanium.UI.PORTRAIT,
	Titanium.UI.UPSIDE_PORTRAIT,
	Titanium.UI.LANDSCAPE_LEFT,
	Titanium.UI.LANDSCAPE_RIGHT
	]
});

var promptView = Titanium.UI.createView({
	id:'messageview',
	height:30,
	width:250,
	borderRadius:10,
	backgroundColor:'#000',
	opacity:0.7,
	touchEnabled:false
});

var promptLabel = Titanium.UI.createLabel({
	id:'messagelabel',
	text:'Double-tap map to move pin.',
	color:'#fff',
	width:250,
	height:'auto',
	font:{
		fontFamily:'Helvetica Neue',
		fontSize:13
	},
	textAlign:'center'
});

promptWin.add(promptView);
promptWin.add(promptLabel);

function drawMap(lat, lon)
{	
	mapview = Titanium.Map.createView({
    	mapType: Titanium.Map.STANDARD_TYPE,
    	region: {latitude:lat, longitude:lon, 
            latitudeDelta:0.01, longitudeDelta:0.01},
    	animate:false,
    	regionFit:true,
    	userLocation:true
	});
	win.add(mapview);
	
	var currentLocation = Titanium.Map.createAnnotation({
		latitude:lat,
		longitude:lon,
		title:"Here",
		pincolor: isAndroid ? "orange" : Titanium.Map.ANNOTATION_RED,
		animate:true,
		myid:1 // CUSTOM ATTRIBUTE THAT IS PASSED INTO EVENT OBJECTS
	});
	mapview.addAnnotation(currentLocation);

}

function onResolvingLocation( coords )
{
	drawMap( coords.latitude, coords.longitude);
}


function onLocationResolved( e )
{
	var locationData = JSON.parse(Titanium.App.Properties.getString('LocationData'));
	loadingToolbar.hide();
	Titanium.API.info(JSON.stringify(locationData.categories));
	setCategoryOptions(locationData.categories);
	win.setToolbar([selectButtonBar]);
}



Titanium.App.addEventListener('resolving_location',onResolvingLocation);
Titanium.App.addEventListener('location_resolved',onLocationResolved);

var currentLocationString = Titanium.App.Properties.getString('CurrentLocation');

if (currentLocationString == '') {
	win.setToolbar([loadingToolbar],{animated:true});
	loadingToolbar.show();
}
else {
	Titanium.API.info(currentLocationString);
	var currentLocation = JSON.parse(currentLocationString);
	var locationDataString = Titanium.App.Properties.getString('LocationData');
	if (locationDataString == '') {
		drawMap(currentLocation.latitude, currentLocation.longitude);
		win.setToolbar([loadingToolbar],{animated:true});
		loadingToolbar.show();
	}
	else {
		var locationData = JSON.parse(locationDataString);
		drawMap(locationData.lat, locationData.lon);
		setCategoryOptions(locationData.categories);
		win.setToolbar([selectButtonBar]);
	}
}


