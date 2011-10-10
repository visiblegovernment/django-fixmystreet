Titanium.include("/js/utils/form.js");
Titanium.include("/js/utils/win_wrapper.js")
Titanium.include('/js/defs/settings_def.js')

var isAndroid = (Titanium.Platform.name == 'android');

function SetIdWin()
{
	that = new WinWrapper( Titanium.UI.createWindow({  
				id: 'setid',
				title:'First, tell us about yourself...',
				barColor:'black',
		//		fullscreen: false,
				backgroundColor: '#000',
				orientationModes: [ 	Titanium.UI.PORTRAIT,Titanium.UI.UPSIDE_PORTRAIT	],
					}) );

	that.form = new Form("Who",300);
	for (var i=0;i< SETTINGS.length;i++)
	{
		var setting = SETTINGS[i];
		Titanium.API.info("SetId: creating " + setting.id );
		var field = that.form.addTextField(setting.id,setting.label,setting.keypad);
		var val = Titanium.App.Properties.getString(setting.label);
		if( val != null )
		{
			val.value = val;
		}
		if( 'format' in setting )
		{
			that.form.addFormatter(setting.id, setting.format);
		}
		if( 'validate' in setting )
		{
			that.form.addValidator(setting.id, setting.validate);		
		}
	}

	that.buttons = that.form.addButtonRow(['Save','Cancel']);

	that.onOpen = function()
	{
		for (var i=0;i< SETTINGS.length;i++)
		{
			var val = Titanium.App.Properties.getString(SETTINGS[i].label);
			if( val != null )
			{
				that.form.fields[SETTINGS[i].id].set(val);
			}
		}
		if( ! isAndroid )
		{
			that.win.backButtonTitle = '';	
		}

	}

	that.onSave = function(e)
	{
		var error = null;
		if( ! that.form.validate() )
		{
			Titanium.API.info("new report: got errors.");
			for ( var id in that.form.errors )
			{
				error = that.form.errors[id];
				break;
			}	
		}

		if( error )
		{	
			var alertDialog = Titanium.UI.createAlertDialog({
	  		    title: 'Oops.',
   		 		message: error,
   		 		buttonNames: ['OK']
			});
			alertDialog.show();
			return;
		}
	
		var values = that.form.getValues();
	
		Titanium.App.Properties.setString('Name',  values['name']);
		Titanium.App.Properties.setString('Phone', values['phone']);
		Titanium.App.Properties.setString('Email', values['email']);
		Titanium.App.Properties.setBool('IdSet', true );

		Titanium.API.info("SetId: save " + JSON.stringify(values));
		//Titanium.App.fireEvent('app_id_set', {});
		that.win.close();
	}

	that.onCancel = function(e)
	{
		that.form.clear();
		if( isAndroid )
		{
			Titanium.API.info("SetId: closing window");
			that.view.hide();
		}
		//else
		//{
			Titanium.App.fireEvent('app_request_tabchange', { 'tab': 0 });
		//}
	}
	
	that.onClick = function(e)
	{
		that.form.fields['phone'].item.blur();
	}


	that.view = that.form.getView();
	that.scrollView =  Ti.UI.createScrollView({
		top: 0,
		left: 0,
		contentWidth: that.view.width,
		contentHeight: that.view.height,
		height: that.view.height+50,
		width: Titanium.Platform.displayCaps.platformWidth,
		});

	that.scrollView.add(that.view);
	that.win.add(that.scrollView);
	that.win.addEventListener('open',that.onOpen);
	that.win.addEventListener('click', that.onClick);
	that.buttons[0].addEventListener('click',that.onSave);
	that.buttons[1].addEventListener('click',that.onCancel);
	
	return( that );

}

