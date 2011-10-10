Titanium.include('js/fmsapi.js');
Titanium.include('js/windows/setid.js');
Titanium.include('js/windows/mapprompt.js');

var isAndroid = (Titanium.Platform.name == 'android');
var winId = null;
var isLoading = false;

// this sets the background color of the master UIView (when there are no windows/tab groups on it)
Titanium.UI.setBackgroundColor('#000');

Titanium.App.Properties.setString('CurrentLocation', '');
Titanium.App.Properties.setString('LocationData', '');
Titanium.App.Properties.setString('TargetLocation', '');
Titanium.App.Properties.setBool('IdSet', false);

var db = Titanium.Database.open('FMSdb.sqlite');
//db.execute('drop table reports;');
db.execute('CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, group_name VARCHAR(32) not null, hint_text VARCHAR(250))');
db.execute('CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, category integer, title VARCHAR(64) NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL, desc VARCHAR(250), is_fixed INTEGER)');
db.close();

// create tab group
var tabGroup = Titanium.UI.createTabGroup();

var winNearby = Titanium.UI.createWindow({  
    url: 'js/windows/nearby2.js',
	title:'Nearby',
    backgroundColor:'#fff'
});


var tabViewReports = Titanium.UI.createTab({  
    icon:'images/icon_view.png',
    title:'Nearby',
	window: winNearby
});

var winNewReports = Titanium.UI.createWindow({  
    url: 'js/windows/newreport3.js',
	title:'New Report',
    backgroundColor:'#fff'
});



var tabNewReport = Titanium.UI.createTab({  
    icon:'images/icon_new.png',
    title:'New Report',
    window: winNewReports
});


var winAbout = Titanium.UI.createWindow({  
    url: 'js/about.js',
	title:'About',
    backgroundColor:'#fff'
});

var tabAbout = Titanium.UI.createTab({  
    icon:'images/icon_about.png',
    title:'About',
    window:winAbout
});

var winSettings = Titanium.UI.createWindow({  
    url: 'js/settings.js',
	title:'Settings',
    backgroundColor:'#fff'
});

var tabSettings = Titanium.UI.createTab({  
    icon:'images/icon_settings.png',
    title:'Settings',
    window:winSettings
});

var noConnectionAlert = Titanium.UI.createAlertDialog({
			title:'No network connection detected.',
			buttonNames:['Try again.']
});
    
function  onNetworkEvent(e) 
{
  	if ( ! Titanium.Network.online )
	{
		noConnectionAlert.show();
	}
};


var loadingWindow = Titanium.UI.createWindow({
			touchEnabled:false,
			backgroundColor:'#000',
			height:70,
			borderRadius:10,
			width:300,
			bottom:200,
			opacity: isAndroid ? 0 : 0.7,
});


var loadingInd = Titanium.UI.createActivityIndicator({
	textAlign: 'center', 
	height:50,
	color: '#fff',
	message: 'Looking up location....',
	style:Titanium.UI.iPhone.ActivityIndicatorStyle.PLAIN
});

var promptWin = new MapPrompt();

function showPrompt()
{
	Titanium.API.info("NEARBY: showing prompt" );
	promptWin.open();

	setTimeout(function()
	{
		promptWin.close({opacity:0,duration:500});
		Titanium.API.info("NEARBY: done showing prompt" );
	},2000);
			
}


loadingWindow.add(loadingInd);

function onLoadingStart( e )
{
	isLoading = true;
	promptWin.close();
	loadingInd.message = e.text;
	loadingWindow.open();
	loadingInd.show();
	tabGroup.touchEnabled = false;
}

function onLoadingEnd( e )
{
	if( e.text == loadingInd.message )
	{
		loadingInd.hide();
		loadingWindow.close();
	}
	isLoading = false;
	tabGroup.touchEnabled = true;

}

function onRequestTabChange( e )
{
	tabGroup.setActiveTab( e.tab );
}

function onIdSet( e )
{
	Titanium.API.info("APP: onIdSet");
	tabGroup.addTab(tabSettings);	
}

function onFMSError( locationData )
{
	Titanium.API.info("APP: on FMS error" );

	tabGroup.setActiveTab( 0 );
	var alertDialog = Titanium.UI.createAlertDialog({
	  		  title: 'Oops.',
   		 	  message: locationData.error_text,
   		 	  buttonNames: ['OK']
		});
	alertDialog.show();	
}

function onFMSResolveEnd( e )
{
	if( e.status != FMS_SUCCESS )
	{
		onFMSError(e);
		if( e.status == FMS_SERVER_ERROR )
		{
//			Titanium.API.info("APP: exiting app?");
//			Titanium.App.exit();
		}
	}
	else
	{
		if( tabGroup.activeTab.window.title == "Nearby")
		{
			showPrompt();	
		}
	}
}

function onTabFocus( e )
{
	Titanium.API.info("APP: onTabFocus index=" + e.index );
//	Titanium.App.fireEvent('app_tab_changed', e);
	var locationData = FMSApi.getResolvedLocation();

	if( e.index == 0 )
	{
		if( ! isLoading )
		{
			if ( locationData.status == FMS_SUCCESS )
			{
				showPrompt();
			}
		}
	}	
	else
	{
		promptWin.close();
		if( e.index == 1 )
		{
			if( locationData.status != null && locationData.status != FMS_SUCCESS )
			{
				Titanium.API.info("APP: FMS error detected.");
				onFMSError( locationData );
			}
		}
	}
	Titanium.API.info("APP: onTabFocus index=" + e.index + " complete ");
	
}

//
//  add tabs
//
tabGroup.addTab(tabViewReports);  
tabGroup.addTab(tabNewReport);  
tabGroup.addTab(tabAbout);

if( Titanium.App.Properties.getBool('IdSet') ) 
{
	tabGroup.addTab(tabSettings);
}

Titanium.Network.addEventListener('change',onNetworkEvent);
noConnectionAlert.addEventListener('click',onNetworkEvent);
tabGroup.addEventListener('focus', onTabFocus );


Titanium.App.addEventListener('app_loading_start',onLoadingStart);
Titanium.App.addEventListener('app_id_set',onIdSet);
Titanium.App.addEventListener('app_loading_end',onLoadingEnd);
Titanium.App.addEventListener('app_request_tabchange',onRequestTabChange);
Titanium.App.addEventListener('location_resolved',onFMSResolveEnd);

onNetworkEvent(null);

tabGroup.open();


