/**
 * @author user
 */

Titanium.include("/js/utils/sliding_edit_view.js");

var DEFAULT_BORDER_COLOR = '#bbb';
var DEFAULT_LR_MARGIN = 10;

isAndroid = (Titanium.Platform.name == 'android');

function ItemWrapper( item )
{
	this.item = item;
	this.setLeft = function( left )
	{
		this.item.left = left;
	}
	
	this.setWidth = function( width )
	{
		this.item.width = width;
	}
	
	this.setTop = function( top )
	{
		this.item.top = top;
	}
	
	this.getHeight = function()
	{
		return( this.item.height );
	}
	
	this.addToView = function ( view )
	{
		Titanium.API.info("form: ItemWrapper " + this.item + " top=" + this.item.top + " left=" + this.item.left + "w=" + this.item.width );
		view.add( this.item );
	}
		
	this.addEventListener = function( evtName, fcn )
	{
		Titanium.API.info("form: ItemWrapper add event listener " + this.item + " name=" + evtName );
		this.item.addEventListener(evtName,fcn);
	};
	


};

function Label( labelText )
{
	var that = new ItemWrapper( Titanium.UI.createLabel({
				color:'#fff',
				text: labelText,
				height:30 } ));
				
	that.getText = function()
	{
		return( that.item.text );
	}
	
	return( that );
}

function GreenButton( title )
{
	var that = new ItemWrapper ( Titanium.UI.createButton({
			color:'#fff',
			backgroundImage:'/images/BUTT_grn_off.png',
			height:57,
			font:{fontSize:20,fontWeight:'bold',fontFamily:'Helvetica Neue'},
			title: title
		}) );
		
	
	return( that );
}

function FieldBase( field )
{
	var that = new ItemWrapper( field );
	that.field = that.item;
	that.validator = null;
	that.formatter = null;
	
	that.addFormatter = function( formatFcn )
	{
		that.formatter = formatFcn;
		// on android, format at end
		if( ! isAndroid )
		{
			that.item.addEventListener( 'change', formatFcn );
		}
	}
	
	that.addValidator = function( validateFcn )
	{
		that.validator = validateFcn;
	}
	
	that.get = function()
	{
		return( that.item.value );
	}
	
	that.set = function( value )
	{
		that.item.value = value;
	}
	
	that.blur = function()
	{
		// do nothing by default.	  
	};
	
	that.clear = function()
	{
		that.item.value = '';
		that.clearError();
	}
	
	that.clearError = function()
	{		
		// clear error indication.
		that.item.borderColor = DEFAULT_BORDER_COLOR;
		that.item.borderWidth = 1;
	}
	
	that.showError = function()
	{
		that.item.borderColor = '#fbb';
		that.item.borderWidth = 2;
	}
	
	that.validate = function()
	{
		var value = that.get();

		// is it blank?		
		if( value == '')
		{
			return( 'Field can not be blank.' );
		}
		
		// do we have a formatter defined?  if so, run it now.
		if( isAndroid && ( that.formatter ) )
		{
			that.formatter( { 'source' : that.field } );
		}
		
		// do we have a validator defined?
		if ( that.validator )
		{
			err = that.validator( value );
			return( err );
		}
		
		return ( null );
	}
	
	return( that );
	
}


function TextField( keyboard )
{
	var that = new FieldBase( Titanium.UI.createTextField({
			height:35,
			backgroundColor:'#fff',
			keyboardType: keyboard,
			borderWidth: 1,
			borderColor: '#bbb',
			borderRadius: 5
		}) );
		
	that.blur = function()
	{
		that.item.blur();
	};

	return( that );
}


function TextAreaField(  height )
{
	var that = new FieldBase( Ti.UI.createTextArea({
			value: '',
			height: height,
			keyboardType: Ti.UI.KEYBOARD_ASCII,
			color: '#222',
			borderWidth: 1,
			borderColor: '#bbb',
			borderRadius: 5
		}) );

	that.blur = function()
	{
		that.item.blur();
	};

	return( that );
}

function RightButtonField()
{
	var that = new TextField( Titanium.UI.KEYBOARD_DEFAULT )
	var tr = Titanium.UI.create2DMatrix();
	tr = tr.rotate(90);
 	var fieldButton =  Titanium.UI.createButton({
			style:Titanium.UI.iPhone.SystemButton.DISCLOSURE,
			transform:tr
	});
	that.field.rightButton = fieldButton;
	that.field.rightButtonMode = Titanium.UI.INPUT_BUTTONMODE_ALWAYS;
	
	that.blur = function()
	{
	//	that.item.blur();
	};

	return that;
}

function CustomHtmlSelectField( id, height, width )
{
	var that = new ItemWrapper( Ti.UI.createWebView({
		width: width,
		height: height,
		left: 10 }) );


	that.value = '';
	that.id = id;
	that.width = width;
	
	that.blur = function()
	{
		
	}
	
	that.clear = function()
	{
		that.value = '';
		//that.item.reload();
		that.item.evalJS('document.getElementById(\'' + that.id + '\').value=\'\';');
	}
	
	that.get = function()
	{
		return( that.value );
	}
		
	that.setOptions = function( options )
	{
		var html = "<html><body bgcolor='#333' style='width: " + that.width + "px; margin: 0px; padding: 0px;' >";
		html += "<select id='" + that.id + "' style='width: " + (that.width) + "px; margin: 0px; padding: 0px; font-size: 14px; height: " + that.item.height + ";'>";
		html += "<option value='' >Please select a category</option>";
		optgroup = null;
		for (var i = 0; i < options.length; i++) 
		{
			var option = options[i];
			if (option.group != optgroup) {
				if (optgroup != null) {
					html += "</optgroup>";
				}
				html += "<optgroup label='" + option.group + "'>";
				optgroup = option.group;
			};
			html += "<option value='" + option.value + "'>" + option.name + "</option>";
		};
		html += "</select>";
		html += "</body>";
		html += "<script type='text/javascript'>";
		html += "document.getElementById('" + that.id + "').onchange = function(){ Titanium.API.info('about to fire custom event');Titanium.App.fireEvent('custom_select_value',{'value': this.options[this.selectedIndex].text, 'id': '" + that.id + "'}); };";
		html += "</script>";
		html += "</html>";
		that.item.html = html;
	};	
	
	that.jschange = function( e )
	{	
		Titanium.API.info("form: on valu change: " + e.value + ' id=' + e.id );
		if ( e.value != '' && e.id == that.id )
		{
			Titanium.API.info("form: setting value to: " + e.value );
			that.value = e.value;
			that.item.fireEvent('custom_change', {'source': that, 'value':e.value })
		}	
	}
	
	that.validate = function()
	{
		// is it blank?		
		if( that.value == '')
		{
			return( 'Field can not be blank.' );
		}
		
		return ( null );
	}

	Titanium.App.addEventListener('custom_select_value',that.jschange);
	return( that );
};


function CustomPickerField( id, hintText )
{
	var that = new RightButtonField();
	that.id = id;
	that.view = new SlidingEditView( 270, null );
	that.field.hintText = hintText;
	that.picker = null;
	that.changed = false;
	that.options = [];
	
	that.addToWin = function( win )
	{
		win.add(that.view.view);
	}
		
	that.onPickerChange = function(e)
	{
		Titanium.API.info("custom picker onPickerChange " + that + " " + e.row.myid );
		if( that.get() != e.row.myid )
		{
			that.set( e.row.myid );
			that.changed = true;
		}
	}
	
	that.clear = function()
	{
		Titanium.API.info("custom picker clear" );
		that.set( '' );
		that.clearError();
		that.changed = false;
		if( that.picker )
		{	
			Titanium.API.info("custom picker clear: setting row to 0" );
			if( that.options.length > 0 )
			{
				that.picker.setSelectedRow(0,0);
			}
		}
		Titanium.API.info("custom picker clear: donw" );
	}
	
	that.setOptions = function( options )	
	{
		that.options = options;
		if( isAndroid )
		{
			that.picker = Titanium.UI.createPicker({
				useSpinner: true, 
				visibleItems: 7,
				type : Ti.UI.PICKER_TYPE_PLAIN,
				top: 20, 
				height: 200,
				selectionIndicator:true, });
		}
		else 
		{
			that.picker = Titanium.UI.createPicker({
				top:20,
				selectionIndicator:true,
			});
		}	
		var optgroup = '';
		var rows = [];
		Titanium.API.info("custom picker setting options " + that );

		for (var i = 0; i < options.length; i++) 
		{
			var name = options[i].name;
	  		var group = options[i].group;
			if (group != optgroup )
			{
				var groupRow = Ti.UI.createPickerRow( {
	    			touchEnabled: false,
	    			myid: ''
 				});
    			
 		   		var label = Ti.UI.createLabel({
				    text:group,
				    font:{fontSize:16,fontWeight:'bold'},
				    color:'#ff5555',
				    textAlign: 'center',
				    width:'auto',
				    height:'auto'
					});
				groupRow.add(label);
				rows.push(groupRow);
				optgroup = group;
			}
		
			var row = Ti.UI.createPickerRow( { myid: name });

	    	var label = Ti.UI.createLabel({
			    text:name,
			    font:{fontSize:12},
			    width:'auto',
			    textAlign: 'center',
			    height:'auto'
				});

			row.add(label);
			rows.push(row);
 		}
		that.picker.add(rows);
		that.picker.addEventListener( 'change', function(e) { that.onPickerChange(e); } );
		that.view.setField(that.picker);

	};
	
	that.blur = function()
	{
	};


	that.view.done.addEventListener('click',function() {
		that.view.slideOut();
		if( that.changed )
		{
			that.item.fireEvent('custom_change', { 'source': that, 'value': that.get() } );
		}
	});

	
	that.field.addEventListener( 'focus', function(e)
		{
			Titanium.API.info("custom picker onFocus " + that );
			e.source.blur();
			that.view.slideIn();
		} );

	return( that );
};


function Form( name, width ) {
 	this.name = name;
	this.width = width;
	this.fields = {};
	this.labels = {};
	this.errors = {};
	this.items = [];
	this.isAndroid = (Titanium.Platform.name == 'android');

	
	this.curTop = 10;
	this.view = null;
	this.submitButton = null;

	/* resize a row of items. */	
	this.setRowWidth = function( row_items, width )
	{
		item_width = Math.round( (width - DEFAULT_LR_MARGIN * (row_items.length + 1) ) / row_items.length );
		
		for( var j = 0; j < row_items.length; j++ )
		{
			row_items[j].setWidth( item_width );
			row_items[j].setLeft( Math.round( DEFAULT_LR_MARGIN + j * (item_width + DEFAULT_LR_MARGIN) ) );		
		}						
	};
	
	
	this.setWidth = function( width )
	{
		this.width = width;
		
		for( var i = 0; i < this.items.length; i++ )
		{
			if (this.items[i] instanceof Array) 
			{
				this.setRowWidth( this.items[i], width );
			} else 
			{
				this.items[i].setWidth( width - DEFAULT_LR_MARGIN * 2 );
			}
		};
		
		if( this.view )
		{
			this.view.width = width;
		}
	};
	
	this.addItem = function( item, padding )
	{
		this.items.push(item);
		if ( item instanceof Array )
		{
		     for( var i = 0; i < item.length; i++ )
		     {
				item[i].setTop( this.curTop );
		     }
		     this.setRowWidth( item, this.width );
  		     this.curTop = this.curTop + item[0].getHeight() + padding;				     
		}
		else
		{
			item.setTop( this.curTop );
			item.setLeft( DEFAULT_LR_MARGIN );
			item.setWidth( this.width - DEFAULT_LR_MARGIN * 2 );
  		    this.curTop = this.curTop + item.getHeight() + padding;		
		}		
	};
	
	
	this.addLabel = function( id, labelText )
	{
		var label = new Label(labelText);
		this.labels[ id ] = label;
		this.addItem(label,-2);
		return (label );
	};
	
	this.addValidator = function( id, validation_fcn )
	{
		this.fields[id].addValidator( validation_fcn );
	}
	
	this.addFormatter = function ( id, format_fcn )
	{
		this.fields[id].addFormatter( format_fcn );
	}
		
	this.addField = function( id, field )
	{
		this.fields[ id ] = field;
		this.addItem(field,5);
	};
	
	this.addButtonRow = function( textArray )
	{
		var buttonArray = [];
		for( var i = 0; i < textArray.length; i++ )
		{
			var button = new GreenButton(textArray[i]);
			buttonArray.push(button);
		}
		
		this.curTop = this.curTop + 10;
		this.addItem(buttonArray,10);
		return( buttonArray );
	};
	
	this.addSubmitButton= function (text)
	{
		this.submitButton = new GreenButton(text);
		this.addItem(this.submitButton,5);
	};
	
	this.addFieldWithLabel =  function( id, label, field )
	{
		this.addLabel(id, label);
		this.addField( id, field );
		return field;
	}
		
	this.addTextField = function( id, label, keyboard )
	{
		return( this.addFieldWithLabel(id, label, new TextField( keyboard ) ) );
	};
	
	this.addRightButtonField = function( id, label )
	{
		return( this.addFieldWithLabel(id, label, new RightButtonField() ) );
	};
		
	this.addTextArea = function( id, label, height )
	{
		return( this.addFieldWithLabel(id, label, new TextAreaField( height ) ) );
	};
		
	this.addCustomSelect = function( id, label, height )
	{
		return( this.addFieldWithLabel(id, label, new CustomHtmlSelectField( id, height, this.width - DEFAULT_LR_MARGIN*2)  ) );
	};
	
	this.addCustomPicker = function( id, label, hint )
	{
		return( this.addFieldWithLabel(id, label, new CustomPickerField( id, hint ) ) );
	}
	
	this.getView = function()
	{
		if (this.view == null)
		{	
			this.view = Ti.UI.createView({
	  			top: 10,
 	  			left: 10,
 	  			width: this.width,
	  			height: this.curTop+10,
	  			backgroundColor:'#333',
	  			borderRadius:6
			});

			for( var i = 0; i < this.items.length; i++ )
			{
				if ( this.items[i] instanceof Array )
				{
					row = this.items[i];
				    for( var j = 0; j < row.length; j++ )
				    {
				    	row[j].addToView( this.view );
				    }
				} 
				else
				{	
					this.items[i].addToView(this.view);
				}
			};
		
			this.view.addEventListener('click',this.onClick);
		}	
		
		return( this.view );
	};
	
	
	this.validate = function()
	{
		var allOK = true;
		for( var id in this.fields )
		{	
			var field = this.fields[id];
			var err = field.validate();

			if( err )
			{
				allOK = false;
				field.showError();
				this.errors[id] = err;
			}	
			else
			{
				// clear previous errors
				if( id in this.errors )
				{
					field.clearError();
					delete this.errors[id];
				}
			}
		}		
		return allOK;
	};
	
	this.getValues = function()
	{
		var values = {};
		for( var id in this.fields )
		{
			values[ id ] = this.fields[id].get();
		};
		return values;		
	};
	
	this.clear = function()
	{
		for( var id in this.fields )
		{
			this.fields[id].clear();
		}
		this.errors = {};
	}
		
	var that = this;
	this.onClick = function(e)
	{
		Titanium.API.info("form: onClick");
		for( var id in that.fields )
		{
			Titanium.API.info("form: looking at field " + id);
			if( that.fields[id].item)
			{
				Titanium.API.info("form: blurring field " + id);			
				that.fields[id].blur();					
			}
		}
	}
	return( that );
};
