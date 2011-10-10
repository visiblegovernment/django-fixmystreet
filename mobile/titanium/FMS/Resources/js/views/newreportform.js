Titanium.include("/js/utils/form.js");
Titanium.include("/js/views/addphotoform.js")
Titanium.include('/js/fmsapi.js');

var isAndroid = (Titanium.Platform.name == 'android');

function NewReportForm()
{
	var that = new Form('details',Titanium.Platform.displayCaps.platformWidth - 20);
	that.db = Titanium.Database.open('FMSdb.sqlite');

	that.scrollView = Ti.UI.createScrollView({
		top: 0,
		left: 0,
		contentWidth: 320,
		contentHeight: 710,
		height: 480,
		width: Titanium.Platform.displayCaps.platformWidth,
	});
	
	that.inputSize = that.scrollView.width - 20;
	that.currentImageAdded = false;
	that.addTextField('title',"What's the Problem?", Titanium.UI.KEYBOARD_DEFAULT);
	that.locationField = that.addRightButtonField('location',"Where's the Problem?");

	if( isAndroid )
	{
		that.categoryField = that.addCustomSelect('category','Problem category:',30);
	}	 
	else
	{
		that.categoryField = that.addCustomPicker('category','Problem category:', 'Please select a category.');
	}

	that.addTextArea('desc',"More details:", 60);
	that.detailsView = that.getView();
	that.scrollView.add(that.detailsView);

	that.photoForm = new AddPhotoForm(that.inputSize);
	that.photoForm.view.top = that.detailsView.top + that.detailsView.height + 10;
	that.scrollView.add(that.photoForm.view);	

	that.clearButton = new GreenButton( 'Clear' );
	that.clearButton.setTop( that.photoForm.view.top + that.photoForm.view.height + 10 );
	that.saveButton = new GreenButton( 'Send Report' );
	that.saveButton.setTop( that.photoForm.view.top + that.photoForm.view.height + 10 );
	that.setRowWidth([ that.clearButton, that.saveButton ], that.scrollView.width);

	that.clearButton.addToView(that.scrollView);
	that.saveButton.addToView(that.scrollView);

	that.onCategoryChange = function( e )
	{
		Titanium.API.info("new report: on set category: " + e.value );
		if ( e.value != '' )
		{
			// show hint text as a pop-up.
			var categoryQ = that.db.execute('SELECT hint_text FROM categories where name="' + e.value + '"');
			while (categoryQ.isValidRow())
			{
				var alertDialog = Titanium.UI.createAlertDialog({
			  //  title: 'Hello',
   				 message: categoryQ.fieldByName('hint_text'),
   				 buttonNames: ['OK']
				});
				alertDialog.show();
  				categoryQ.next();
			}
			categoryQ.close();	
		}
	}

	that.onChangeLocation = function( e )
	{
		Titanium.API.info("new report: change location field focused");
		that.locationField.field.blur();
		Titanium.App.fireEvent('app_request_tabchange', { 'tab': 0 });
	}

	that.setLocationField = function()
	{
		var targetStr = Titanium.App.Properties.getString('TargetLocation');
		if( targetStr != "" )
		{
			targetData = JSON.parse(targetStr);
			that.locationField.set( targetData.locationStr );
		}
	}

	that.onTargetChanged = function( e )
	{
		that.setLocationField();
	}

	that.resetCategoryOptions = function()
	{
		var options = [];
		var categoryQ = that.db.execute('SELECT id,name,group_name FROM categories');
		while (categoryQ.isValidRow())
		{
  			options.push( { 'name' : categoryQ.fieldByName('name'),
  							'value' : categoryQ.fieldByName('id'),
  							'group' : categoryQ.fieldByName('group_name') } );
  			categoryQ.next();
		}
		categoryQ.close();	
		that.categoryField.setOptions( options );
	}

	that.onFMSResolveEnd = function( e )
	{
		that.resetCategoryOptions();
	}


	that.onClear = function()
	{
		Titanium.API.info("new report: onClear");
		that.photoForm.removeCurrentPhoto();
		that.clear();
		that.setLocationField();
	}


	that.onSendReportComplete = function( status, status_text )
	{
		var alertDialog = Titanium.UI.createAlertDialog({
   		 	  message: status_text,
   		 	  buttonNames: ['OK']
		});
		if( status == FMS_SUCCESS )
		{
			alertDialog.addEventListener('click', function(e) {
				that.onClear();
				Titanium.App.fireEvent('app_request_tabchange', { 'tab': 0 });
			});
		}
		alertDialog.show();	
	
	}


	that.onSubmit = function()
	{
		Titanium.API.info("new report: onSubmit");

		var data = that.getValues();
		var isValid = that.validate();
		if( ! isValid )
		{
			Titanium.API.info("new report: got errors.");
			for ( var id in that.errors )
			{
				var error = "Please check field " + that.labels[id].getText() + "\n";
				error += that.errors[id];
				var alertDialog = Titanium.UI.createAlertDialog({
		  		    title: 'Oops.',
   			 		message: error,
   			 		buttonNames: ['OK']
				});
				alertDialog.show();
				return;
			}	
		}
	
		// add location info.
		var targetStr = Titanium.App.Properties.getString('TargetLocation');
		var targetData = JSON.parse(targetStr);
		data['lat'] = targetData.lat;
		data['lon'] = targetData.lon;
		data['location'] = targetData.locationStr;
		
		// add id settings.
		data['author'] = Titanium.App.Properties.getString('Name');
		data['phone'] = Titanium.App.Properties.getString('Phone' );
		data['email'] = Titanium.App.Properties.getString('Email');

		// add photo info
		// TODO
		
		FMSApi.sendReport(data, that.onSendReportComplete);
	
	}


	that.open = function( win )
	{
		win.title = "New Report";

		var locationData = Titanium.App.Properties.getString('LocationData');

		if( locationData != "" )
		{
			that.resetCategoryOptions();
		}	
 
		Titanium.App.addEventListener('location_resolved',that.onFMSResolveEnd);
		Titanium.App.addEventListener('target_changed',that.onTargetChanged);

		that.setLocationField();
		win.add(that.scrollView);

		if ( ! isAndroid )
		{
			// add custom picker slider to window.
			that.categoryField.addToWin(win);
		}
	}

	that.locationField.addEventListener('focus',that.onChangeLocation);
	that.categoryField.addEventListener('custom_change',that.onCategoryChange);
	that.saveButton.addEventListener('click', that.onSubmit);
	that.clearButton.addEventListener('click', that.onClear);
	
	return( that );
};
