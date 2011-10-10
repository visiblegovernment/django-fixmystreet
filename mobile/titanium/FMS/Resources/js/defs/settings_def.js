

var SETTINGS = [ { 	id: 'name',
					label:'Name', 
				   	keypad: Titanium.UI.KEYBOARD_DEFAULT  },
				 { 	id: 'phone',
				 	label:'Phone', 
				   	keypad: Titanium.UI.KEYBOARD_PHONE_PAD,
					format : function( e )
					{
						val = e.source.value;
						Titanium.API.info("format phone:" + val );
						val = val.replace(/^(\d)/,"($1");
						val = val.replace(/^(\(\d{3})([^\)]) */,"$1) $2");
						val = val.replace(/^(\(\d{3}\) \d{3})([^-])/,"$1-$2");
						val = val.replace(/^(\(\d{3}\) \d{3}-\d{4}).*/,"$1");
						e.source.value = val;
					},
					validate : function( val )
					{
						var regEx = /^\(\d{3}\) \d{3}-\d{4}$/i;
					   	var error = null;
    					if (val.search(regEx) == -1) {
          					error = "Please enter a valid 10 digit phone number.";
    					}
    					return( error );
					},
				  },				   
				  { 	
				  	id: 'email',
				 	label:'Email', 
				   	keypad: Titanium.UI.KEYBOARD_EMAIL,
					validate : function( val )
					{
						var emailRegEx = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;
					   	var error = null;
    					if (val.search(emailRegEx) == -1) {
          					error = "Please enter a valid email address.";
    					}
    					return( error );
					},

				   	} ];
