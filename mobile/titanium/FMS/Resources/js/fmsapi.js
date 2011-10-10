
DEBUG = true;
DEBUG_URL = "http://technoutopians.com/";
FMS_SUCCESS = 0;
FMS_LOCATION_NOT_SUPPORTED = 1;
FMS_SERVER_ERROR = 2;
FMS_LOADING_MSG = 'Looking up location....';

function resolve_status_text(status)
{
	switch( status )
	{
		case FMS_SUCCESS: return('');
		case FMS_SERVER_ERROR: return( 'Could not communicate with server at FixMyStreet.ca.  Please try again later.')
		case FMS_LOCATION_NOT_SUPPORTED: return('Location not supported by FixMyStreet.ca')
	}	
}

function send_status_text(status)
{
	switch( status )
	{
		case FMS_SUCCESS: 
			var email = Titanium.App.Properties.getString('Email');
			return('Thanks for submitting your report to FixMyStreet.ca.  A confirmation email has been sent to ' + email + '.' );
		case FMS_SERVER_ERROR: return( 'Could not communicate with server at FixMyStreet.ca.  Please try again later.')
	}	
}


function InitLocationData( status, lat, lon )
{
	var data = { latitude: lat,
	longitude: lon,
	status: status,
	error_text: resolve_status_text(status) };
	return( data );
};

//----------------------------------------------------------------------------------
// Mock API Used in Debugging
//----------------------------------------------------------------------------------


var DEBUG_LAT = 	45.4095879999999994;
var DEBUG_LON = 	-75.7102699999999942;

function DebugFMSApi()
{	
	
	this.resolveCount = 0;
	this.sendCount = 0;
	this.reports = [ 
				{
			"service_request_id":20,
            "service_code": 6, 
            "title": "Tagging - 314 Booth", 
            "lon": -75.7102699999999942,
			"lat": 45.4065879999999994, 
            "status": true, 
            "desc": "Tagging has appeared on North facing construction barriers at the site at 314 Booth St at Eccles St. \r\n\r\nThe graffiti at 300 Booth is still there on the South wall, facing the barriers mentioned above"
       },
		{
			"service_request_id": 21,
            "service_code": 9, 
            "title": "Large Pothole (Utility Cut Sinking)", 
            "lon": -75.6870889663999975,
			"lat": 45.4043333270000034, 
            "status": false, 
            "desc": "The utility road cut in front of 77 2nd Ave is sinking, resulting in a pothole that is approx 3-4 inches at its deepest and runs almost the width of the street. Due to the nature of the cut, when traveling east on 2nd Ave, vehicles actually hit the \"knife\"/step like edge of the road cut.  During rain, this pothole catches water and creates a small lake that does not drain. The result is that passing cars splash water approx. 8-10 feet in the air and wet pedestrians on both sides of the road."
        }, 
 	   {
 	   		"service_request_id": 22,
            "service_code": 6, 
            "title": "Tagging - side of 752 Somerset St W", 
            "lon":-75.7081880000000069,
			"lat": 45.4104239999999990, 
            "status": false, 
            "desc": "Tagging on side of 752 Somerset St W, at the corner of Bell St N.  The tagging is on the Bell St side"
        }
 		]; 
		this.categories = [ { 'service_code': 20, 'service_name' : 'Branches Blocking Signs or Intersection', 'group':'Trees' },
				{ 'service_code':6, 'service_name' :'Graffiti on Private Property', 'group':'Grafitti' },
				{ 'service_code':5, 'service_name' : 'Graffiti On City Property', 'group':'Grafitti' },
				{ 'service_code':7,'service_name':'Graffiti  on Utility Boxes/Transformers/Mailboxes', 'group':'Grafitti' },
				{ 'service_code':15, 'service_name': 'Bus Shelter Damaged', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':16, 'service_name': 'Debris/Litter in Bus Shelter', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':11, 'service_name': 'Debris or Litter on Road/Sidewalk/Pathway', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':8, 'service_name': 'Blocked or damaged Catch basin / Manhole', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':9, 'service_name': 'Pothole', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':10, 'service_name': 'Damaged Curb', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':12, 'service_name': 'Blocked or Damaged Culvert', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':13, 'service_name': 'Damaged Guardrails', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':14, 'service_name': 'Full or Overflowing Garbage Cans', 'group':'Roads/Sidewalks/Pathways' },
{ 'service_code':4, 'service_name': 'Debris or Litter in Park', 'group':'Parks' },
{ 'service_code':3, 'service_name': 'Lights Malfunctioning in Park', 'group':'Parks' },
{ 'service_code':1, 'service_name': 'Broken or Damaged Equipment/Play Structures', 'group':'Parks' },
{ 'service_code':2, 'service_name': 'Full or Overflowing Garbage Cans ', 'group':'Parks' },
{ 'service_code':17, 'service_name': 'Street Lights Out or Malfunctioning', 'group':'Traffic Signals' },
{ 'service_code':18, 'service_name': 'Faded/Damaged/Missing Pavement Markings', 'group':'Traffic Signals' },
{ 'service_code':19, 'service_name': 'Bent/Damaged/Missing Street Signs', 'group':'Traffic Signals' }
 ];	
	
	var hintText = "Let’s face it – programming on mobile devices is hard: everything’s much more complicated to accomplish than it is on the web or the desktop and, since the platform is fairly new, tools and frameworks are scarce and poorly refined. Plus, if you need your application to run on more than one target OS (iOS, Android, Blackberry) you’re pretty much forced to write a different application for each one of them.";
	for (var i = 0; i < this.categories.length; i++) 
	{
		this.categories[i]['description'] = hintText;
	}
	
	this.onResolveTimeout = function( lat, lon, callback )
	{
		Titanium.API.info("DEBUG FMSAPI: resolving #: " + this.resolveCount );		
		var status = this.resolveCount % 3;
		var locationData = InitLocationData(status, lat,lon);
		this.resolveCount = this.resolveCount+ 1;
		callback( locationData, this.reports, this.categories );
	}
	
	this.onSendTimeout = function( callback )
	{
		var status = 0;
		if( this.sendCount % 2 == 0 )
		{
			status = FMS_SUCCESS;
		}		
		else
		{
			status = FMS_SERVER_ERROR;
		}
		this.sendCount = this.sendCount + 1;
		callback( status, send_status_text( status ) );

	}

	this.resolveLocation = function( lat, lon, callback )
	{
		var instance = this;
		setTimeout(function()
		{
			instance.onResolveTimeout(lat,lon,callback);
		},5000);		

	};
	
	this.sendReport = function( report_dict, callback )
	{
		Titanium.API.info("DEBUG FMSAPI: sending report " + JSON.stringify(report_dict));
		var instance = this;
		setTimeout(function()
		{
			instance.onSendTimeout( callback );
		},2000);		

	};
	
};

function ParalellXMLRequest( url, timeout )
{
	var that = this;
	that.status = null;
	that.data = null;
	that.xhr = null;
				
	that.onLoad = function( e )
	{
    	if( that.xhr.status == 200 )
    	{
        	that.data = that.xhr.responseXML;
    	}			
    	else
    	{
			Titanium.API.info("REAL FMSAPI: http load error " + that.xhr.status + " " + that.xhr.responseText ); 
    		that.data = that.xhr.responseText;
    	}
    	that.status = that.xhr.status;
	};
	
	that.onError = function( e )
	{
		Titanium.API.info("REAL FMSAPI: http error " + that.xhr.status ); 
		that.data = that.xhr.responseText;
		that.status = that.xhr.status;
	};
	

	that.xhr = Ti.Network.createHTTPClient({   			
    			onload: function(e) {   that.onLoad(e); },
    			timeout:timeout,
	    		ontimeout : function(e) { that.onError(e); },    		
    			onerror: function(e) { that.onError(e); },
			});
			
	that.xhr.open("GET", url);
	that.xhr.send();	

	return( that );
	
};

function RealFMSApi( url ) {
	
	this.url = url;
	
	this.xmlToJSON = function( xml )
	{

	 	if (xml.nodeType == 3) 
	 	{ // text
    		return( xml.text );
  		}

		// Create the return object
  		var obj = {};

  		// do children
  		if ( xml.childNodes ) 
  		{
  			var  item;
    		for(var i = 0; i < xml.childNodes.length; i++) 
    		{
    			if( i == 0)
    			{
    				item = xml.firstChild;
    			}
    			else
    			{
    				item = item.nextSibling;
    			}
      			//var item = xml.childNodes.item(i);
      			if( item.nodeName == 'text')
      			{
      				return( item.text )
      			}
        		obj[item.nodeName] = this.xmlToJSON(item);
      		}
      	} 
      	
      	Titanium.API.info("REAL FMSAPI: got json " + JSON.stringify(obj));
  		return( obj );
	}
	
	
	this.onResolveTimeout = function( lat, lon, requests, callback )
	{
		var json_reports = [];
		var json_categories = [];
		var status = FMS_SERVER_ERROR;
		
		for( key in requests )
		{
			if( requests[key].status == 404 && requests[key].data == "lat/lon not supported")
			{
				status = FMS_LOCATION_NOT_SUPPORTED;
			}
		}
		
		if( requests.reports.status == 200 && requests.categories.status == 200 )
		{
			// parse XML?
			var reports = requests.reports.data.documentElement.getElementsByTagName("request");
			if( reports )
			{
			 	Titanium.API.info("REAL FMSAPI: resolved " + reports.item.length + " reports " ); 

				for ( var i = 0; i < reports.item.length; i++ )
				{
					json_reports.push( this.xmlToJSON(reports.item(i)));
				}
			}
			var categories = requests.categories.data.documentElement.getElementsByTagName("service");
			if( categories )
			{
		 		Titanium.API.info("REAL FMSAPI: resolved " + categories.item.length + " categories " ); 

				for ( var i = 0; i < categories.item.length; i++ )
				{
					xml = categories.item(i);
					if( xml )
					{
						json_categories.push( this.xmlToJSON(xml));					
					}
				}			
			}
			status = FMS_SUCCESS;
		}
		var locationData = InitLocationData(status, lat, lon);			
		callback( locationData, json_reports, json_categories );
	}

	this.resolveLocation = function( lat, lon, callback )
	{
		var requests = {};
		var http_timeout = 5000;
		requests[ 'categories'] = new ParalellXMLRequest( this.url + "open311/v2/services.xml?lat=" + lat + ";lon=" + lon, http_timeout);
		requests[ 'reports'] = new ParalellXMLRequest(this.url + "open311/v2/requests.xml?lat=" + lat + ";lon=" + lon, http_timeout);
		var instance = this;
		setTimeout(function()
		{
			instance.onResolveTimeout(lat,lon,requests,callback);
		},7000);		

	};	
	
	this.sendReport = function( report_dict, callback )
	{
		Titanium.API.info("REAL FMSAPI: sending report " + JSON.stringify(report_dict));
		var url = this.url + "reports/";
	
		var xhr = Ti.Network.createHTTPClient({
    		onload: function(e) {
        		// this.responseText holds the raw text return of the message (used for JSON)
        		// this.responseXML holds any returned XML (used for SOAP web services)
        		// this.responseData holds any returned binary data
	    		if( this.status == 200 )
	    		{
	    			callback( FMS_SUCCESS, send_status_text( FMS_SUCCESS ) );
	    		}
	    		else
	    		{
	    			Titanium.API.info("REAL FMSAPI: got error " + this.status + " " + this.responseText);
	    			callback( FMS_SERVER_ERROR, send_status_text( FMS_SERVER_ERROR ) );	    			
	    		}
    		},
 
    		ontimeout : function(e) {
    			Titanium.API.info("REAL FMSAPI: HTTP timeout " + url );
	    		callback( FMS_SERVER_ERROR, send_status_text( FMS_SERVER_ERROR ) );
    		},    		
    		onerror: function(e) {
    			Titanium.API.info("REAL FMSAPI: HTTP error " + url );
	    		callback( FMS_SERVER_ERROR, send_status_text( FMS_SERVER_ERROR ) );
    		},
    		timeout:5000
		});
 
		xhr.open("post", url);
		xhr.send(report_dict);	
	};

};

function ApiWrapper( api ) {	
	
	this.api = api;
	this.DEBUG = DEBUG;
	
	this.getResolvedLocation = function()
	{
		var locationStr = Titanium.App.Properties.getString('LocationData');
		if( locationStr == '' )
		{
			return( {} );
		}
		var locationData = JSON.parse(locationStr);
		return( locationData );
	},
	
	
	this.locationResolvedCallback = function( locationData, reports, categories )
	{
			Titanium.API.info("FMSAPI: location resolved " + JSON.stringify(locationData));
			var db = Titanium.Database.open('FMSdb.sqlite');
			for (var i = 0; i < categories.length; i++) 
			{
				db.execute('INSERT OR REPLACE INTO categories (id,name,group_name, hint_text) VALUES (?,?,?,?)',categories[i].service_code,categories[i].service_name,categories[i].group,categories[i].description);
			}

			for (var i = 0; i < reports.length; i++) 
			{
				is_fixed = (reports[i].status == 'closed')
				db.execute('INSERT OR REPLACE INTO reports (id,category,title,desc,lat,lon,is_fixed) VALUES (?,?,?,?,?,?,?)',
					reports[i].service_request_id,
					reports[i].service_code,
					reports[i].title,
					reports[i].desc,
					reports[i].lat,
					reports[i].lon,
					is_fixed);
			}
			
			db.close();
			Titanium.App.Properties.setString('LocationData', JSON.stringify(locationData ));
			Titanium.App.fireEvent('app_loading_end', {'text':FMS_LOADING_MSG});
			Ti.App.fireEvent('location_resolved', locationData );
			
	}
	
	this.resolveLocation  = function( lat, lon )
	{	
		var db = Titanium.Database.open('FMSdb.sqlite');
		var locationString =  Titanium.App.Properties.getString('CurrentLocation');
		if ( locationString != null && locationString != "")
		{
			var prevCoords = JSON.parse(locationString);
			if( prevCoords.latitude == lat && prevCoords.longitude == lon )
			{
				return;
			}
		}
		
		
		Titanium.API.info("resolving location" + lat + " " + lon );
		db.execute('delete from categories;');
		db.execute('delete from reports;');
		db.close();

		var coords = { 'latitude':lat, 'longitude':lon };
		Titanium.App.Properties.setString('CurrentLocation', JSON.stringify(coords ));

		Titanium.App.fireEvent('resolving_location', coords);
		Titanium.App.fireEvent('app_loading_start', {'text':FMS_LOADING_MSG});

		this.api.resolveLocation(lat,lon, this.locationResolvedCallback );
		
	};
	
	
	this.sendReport = function( report_dict, callback )
	{
		Titanium.API.info("FMSAPI: sending report " + JSON.stringify(report_dict));
		var db = Titanium.Database.open('FMSdb.sqlite');
		var categoryQ = db.execute('SELECT id FROM categories where name=\'' + report_dict['category'] + '\'');
		while (categoryQ.isValidRow())
		{
			report_dict['category'] = categoryQ.fieldByName('id');
  			categoryQ.next();
		}
		categoryQ.close();	
		db.close();
		this.api.sendReport( report_dict, callback );
	}
	
};

var FMSApi = new ApiWrapper( new RealFMSApi(DEBUG_URL));