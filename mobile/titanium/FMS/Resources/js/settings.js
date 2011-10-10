Titanium.include('/js/defs/settings_def.js')
Titanium.include("/js/utils/sliding_edit_view.js");

var win = Ti.UI.currentWindow;
var isAndroid = (Titanium.Platform.name == 'android');
var mytabindex = 3;
var valTextArray = [];
var rowEdit = -1;

var editWindow  = Titanium.UI.createWindow({  
//				backgroundColor:'#000',
//				opacity:0.7,
				title: 'Edit Settings'
				});
				


var editField = Titanium.UI.createTextField({
			backgroundColor:'#fff',
			borderColor: '#bbb',
			borderRadius: 5,
			color:'#336699',
			top: 20,
			width: 	Titanium.Platform.displayCaps.platformWidth - 20,
			left: 10,
			height: 35,
			font: {fontSize:16,fontWeight:'bold', fontFamily:'Arial'},
		});
					
var editCloseButton = Titanium.UI.createButton({
		title:'Done',
		height:30,
		width:150,
		top: 80,
});

function onEditWindowOpen()
{
	if( ! isAndroid && 'format' in SETTINGS[rowEdit ])
	{
		editField.addEventListener( 'change',SETTINGS[ rowEdit ].format );
	}
	
	editField.focus();
}

function closeEditWindow()
{
	if( isAndroid && 'format' in SETTINGS[rowEdit] )
	{
		// format now.
		SETTINGS[rowEdit].format( {'source': editField });
	}

	if( 'validate' in SETTINGS[rowEdit] )
	{
		err = SETTINGS[rowEdit].validate( editField.value );
		if( err )
		{
			var alertDialog = Titanium.UI.createAlertDialog({
	  		    title: 'Oops.',
   		 		message: err,
   		 		buttonNames: ['OK']
			});
			alertDialog.show();
			return;
		}		
	}

	if( ! isAndroid && 'format' in SETTINGS[rowEdit ])
	{
		editField.removeEventListener( 'change',SETTINGS[ rowEdit ].format );
	}
	valTextArray[rowEdit].text = editField.value;
	editWindow.close();
}

editCloseButton.addEventListener('click', closeEditWindow );
editField.addEventListener('blur',closeEditWindow);
//editWindow.addEventListener('click',closeEditWindow);
editWindow.addEventListener('open',onEditWindowOpen);
editWindow.add(editField);
editWindow.add(editCloseButton);

function onRowClick(e )
{
	Titanium.API.info("settings - onRowClick index=" + e.index);
	editField.value = valTextArray[e.index].text;
	editField.keyboardType = SETTINGS[e.index].keypad;
	rowEdit = e.index;
	Titanium.UI.currentTab.open(editWindow,{animated:true});
}

function createRow( setting )
{
	var row = Ti.UI.createTableViewRow();
	row.selectedBackgroundColor = '#fff';
	row.height = 35;
//	row.className = 'datarow';
//	row.clickName = 'row';

	var label = Ti.UI.createLabel({
		color:'#576996',
		font: {fontSize:16,fontWeight:'bold', fontFamily:'Arial'},
		left:10,
		top:0,
		height:35,
		width:65,
		clickName:setting.label,
		text: setting.label
	});
	
	row.add(label);

	val = Titanium.App.Properties.getString(setting.label);

	var valText = Ti.UI.createLabel({
		color:'#336699',
		font: {fontSize:16,fontWeight:'bold', fontFamily:'Arial'},
		left:75,
		top:0,
		height:35,
		width:215,
		textAlign: 'right',
		clickName: setting.label,
		text: val
	});
	valTextArray.push(valText);
	row.add(valText);
	row.addEventListener('click',onRowClick);
	return( row );
}

data = [];
for (var i=0;i< SETTINGS.length;i++)
{
	var row = createRow(SETTINGS[i]);
	data.push(row);
}

var tableView = Ti.UI.createTableView({
	data:data,
	style: Titanium.UI.iPhone.TableViewStyle.GROUPED
});


win.add(tableView);
