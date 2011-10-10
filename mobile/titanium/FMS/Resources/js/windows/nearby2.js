var win = Titanium.UI.currentWindow;
var isAndroid = (Titanium.Platform.name == 'android');
Titanium.include('/js/fmsapi.js');
var db = Titanium.Database.open('FMSdb.sqlite');


win.orientationModes = [ 	Titanium.UI.PORTRAIT,
							Titanium.UI.UPSIDE_PORTRAIT,
							Titanium.UI.LANDSCAPE_LEFT,
							Titanium.UI.LANDSCAPE_RIGHT	];
			
var pins = [];
var locationResolved = false;
var inFocus = true;
var DEF_LAT=32.8351302;
var DEF_LON=-117.2776668;
var mytabindex = 0;
var mapview = 	Titanium.Map.createView({
    		mapType: Titanium.Map.STANDARD_TYPE,
    		location: {latitude:DEF_LAT, longitude:DEF_LON, 
            latitudeDelta:0.01, longitudeDelta:0.01},
    		animate:true,
    		touchEnabled: true,
    		regionFit:true,
    		bottom:0,
	});
	
var targetPin = Titanium.Map.createAnnotation({
		animate:false,
		myid:0,
		touchEnabled: true,
		image: "/images/target_32.png"
});

if(isAndroid)
{
	targetPin.rightButton = '/images/disclosure.png';
	targetPin.title = "New Report";
}


function makePin( id, title, lat, lon, is_fixed )
{
	var pin = Titanium.Map.createAnnotation({
		latitude: lat,
		longitude:lon,
		title:title,
		pincolor : is_fixed ? Titanium.Map.ANNOTATION_GREEN : Titanium.Map.ANNOTATION_RED,
		animate:false,
		myid:id
	});
	if (isAndroid )
	{
		pin.image = is_fixed ? "/images/map-pin-red.png" : "/images/map-pin-green.png";
	} 
	return( pin );
};


function makePins()
{

	var reportQ = db.execute('SELECT id,title,lat,lon,is_fixed FROM reports');
	Titanium.API.info("NEARBY: making pins " + reportQ.rowCount);

	while (reportQ.isValidRow())
	{
		var pin = makePin( 	reportQ.fieldByName('id'),
							reportQ.fieldByName('title'),
							reportQ.fieldByName('lat'),
							reportQ.fieldByName('lon'),
							(reportQ.fieldByName('is_fixed') == 1));
		pins.push(pin);
  		
  		reportQ.next();
	}
	reportQ.close();	
}
	
function drawPins()
{
	for (i=0;i<pins.length;i++)
	{
		mapview.addAnnotation(pins[i]);			
	}
	
//	targetPin.latitude = mapview.location.latitude;
//	targetPin.longitude = mapview.location.longitude;

	mapview.addAnnotation(targetPin);
}

function targetMovedAlot()
{
	resolvedLocation = FMSApi.getResolvedLocation();
	Titanium.API.info("NEARBY: lat:" + resolvedLocation.latitude + "=" + targetPin.latitude + " lon:" + resolvedLocation.longitude + "=" + targetPin.longitude);
	latDelta = Math.abs( resolvedLocation.latitude - targetPin.latitude );
	lonDelta = Math.abs( resolvedLocation.longitude - targetPin.longitude );

	return ( lonDelta > 0.01 || latDelta > 0.01 );
}

function onDoubleTap( e )
{
	Titanium.API.info("NEARBY: on map evt=" + e.type + " annotation " + e.annotation.title + "  id " + e.annotation.myid );
	if (e.annotation.title == targetPin.title)
	{
		Titanium.App.fireEvent('app_request_tabchange', { 'tab': 1 });
		resolvedLocation = FMSApi.getResolvedLocation();
		Titanium.API.info("NEARBY: lat:" + resolvedLocation.lat + "=" + targetPin.latitude + " lon:" + resolvedLocation.lon + "=" + targetPin.longitude);
	}
}

function onReverseGeocode(e)
{
	Titanium.API.info("NEARBY: reverse geocode complete" );

	if( e.places && e.places.length != 0)
	{
		var place = e.places[0];
	
		address = place.address.replace(/,.*/,'');
		targetInfo = { 'lat': targetPin.latitude,
				   'lon' : targetPin.longitude,
				   'locationStr': address };
		Titanium.App.Properties.setString('TargetLocation', JSON.stringify(targetInfo));
		Titanium.App.fireEvent('target_changed',targetInfo)
	}
	else
	{
		Titanium.API.info("NEARBY: no geocode result!" );	
	}
}		

function onRegionChange( e )
{
	Titanium.API.info("NEARBY: on region change  lat=" + e.latitude + " lon=" + e.longitude  );

	targetPin.latitude = e.latitude;
	targetPin.longitude = e.longitude;
	
	if( locationResolved )
	{	
		mapview.removeAnnotation(targetPin);
		mapview.addAnnotation(targetPin);
		Titanium.Geolocation.reverseGeocoder( targetPin.latitude, targetPin.longitude, onReverseGeocode);
	
		if( targetMovedAlot() )
		{
			FMSApi.resolveLocation(targetPin.latitude, targetPin.longitude );			
		}
	}
}

function onFMSResolveStart( coords )
{
	Titanium.API.info("NEARBY: on resolve start"  );

	mapview.location = {latitude:coords.latitude, longitude:coords.longitude, 
            latitudeDelta:0.01, longitudeDelta:0.01};
            
    mapview.touchEnabled = false;

	// get rid of any existing pins
	for (i=0;i<pins.length;i++)
	{
		mapview.removeAnnotation(pins[i]);			
	}
	pins = [];
	
}

function onFMSResolveEnd( e )
{
	Titanium.API.info("NEARBY: on resolve end"  );
	
	var locationData = FMSApi.getResolvedLocation();

	mapview.location = {latitude:locationData.latitude, longitude:locationData.longitude, 
            latitudeDelta:0.01, longitudeDelta:0.01};
            
    targetPin.latitude = locationData.latitude;
    targetPin.longitude = locationData.longitude;


	makePins();
	drawPins();
	locationResolved = true;
    mapview.touchEnabled = true;

	Titanium.Geolocation.reverseGeocoder( targetPin.latitude, targetPin.longitude, onReverseGeocode);
}

var DEBUG_LAT = 45.41871143486507;
var DEBUG_LON = -75.69395542144775;

function  onLocation(e) 
{
	if( e.coords ) 
	{	
		if( FMSApi.DEBUG )
		{	
			e.coords.latitude = DEBUG_LAT;
			e.coords.longitude = DEBUG_LON;
		}

		FMSApi.resolveLocation(e.coords.latitude, e.coords.longitude );	
		Titanium.Geolocation.removeEventListener('location',onLocation);
	}
}	

// tab group open event
win.addEventListener('open', function(e)
{
	Titanium.Geolocation.purpose = 'Check for nearby reports.';
	Titanium.Geolocation.getCurrentPosition(onLocation);
	Titanium.Geolocation.addEventListener('location',onLocation);

});

mapview.addEventListener('regionChanged',onRegionChange);
mapview.addEventListener('doubletap',onDoubleTap);
mapview.addEventListener('dblclick',onDoubleTap);
mapview.addEventListener('click',onDoubleTap);

win.add(mapview);

Titanium.App.addEventListener('resolving_location',onFMSResolveStart);
Titanium.App.addEventListener('location_resolved',onFMSResolveEnd);

