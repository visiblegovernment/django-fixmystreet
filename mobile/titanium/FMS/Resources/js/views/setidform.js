Titanium.include("/js/utils/form.js");
Titanium.include('/js/defs/settings_def.js')

var isAndroid = (Titanium.Platform.name == 'android');

function SetIdForm()
{
	that = new Form("Who",300);
	for (var i=0;i< SETTINGS.length;i++)
	{
		var setting = SETTINGS[i];
		Titanium.API.info("SetId: creating " + setting.id );
		var field = that.addTextField(setting.id,setting.label,setting.keypad);
		var val = Titanium.App.Properties.getString(setting.label);
		if( val != null )
		{
			val.value = val;
		}
		if( 'format' in setting )
		{
			that.addFormatter(setting.id, setting.format);
		}
		if( 'validate' in setting )
		{
			that.addValidator(setting.id, setting.validate);		
		}

		var val = Titanium.App.Properties.getString(SETTINGS[i].label);
		if( val != null )
		{
			that.fields[SETTINGS[i].id].set(val);
		}

	}

	that.buttons = that.addButtonRow(['Save','Cancel']);

	that.onSave = function(e)
	{
		var error = null;
		if( ! that.validate() )
		{
			Titanium.API.info("new report: got errors.");
			for ( var id in that.errors )
			{
				error = that.errors[id];
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
	
		var values = that.getValues();
	
		Titanium.App.Properties.setString('Name',  values['name']);
		Titanium.App.Properties.setString('Phone', values['phone']);
		Titanium.App.Properties.setString('Email', values['email']);
		Titanium.App.Properties.setBool('IdSet', true );

		Titanium.API.info("SetId: save " + JSON.stringify(values));
		Titanium.App.fireEvent('app_id_set', {});
	}

	that.onCancel = function(e)
	{
		that.clear();
		Titanium.App.fireEvent('app_request_tabchange', { 'tab': 0 });
	}
	
/*	that.onClick = function(e)
	{
		for( id in that.fields )
		{
			that.fields[id].item.blur();		
		}
	}
*/	
	that.open = function( win )
	{
		win.title = "First, Tell Us About Yourself...";
		win.add(that.scrollView);
	}
	
	that.close = function( win )
	{
		win.remove(that.scrollView);
	}


	that.view = that.getView();
	that.scrollView =  Ti.UI.createScrollView({
		top: 0,
		left: 0,
		contentWidth: that.view.width,
		contentHeight: that.view.height,
		height: that.view.height+50,
		width: Titanium.Platform.displayCaps.platformWidth,
		});

	that.scrollView.add(that.view);
//	that.scrollView.addEventListener('click', that.onClick);		
	that.buttons[0].addEventListener('click',that.onSave);
	that.buttons[1].addEventListener('click',that.onCancel);
	
	return( that );

}

