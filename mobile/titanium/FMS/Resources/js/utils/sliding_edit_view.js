
/*
 * View with a single edit field.
 */

function SlidingEditView( height, field )
{
	this.view = Titanium.UI.createView({
		height:height,
		bottom:-height,
		backgroundColor: '#333'
	});	
	
	this.done =  Titanium.UI.createButton({
		title:'Done',
		height: 35,
	});
	
	
	this.view.add(this.done);
	this.slideInAnim =  Titanium.UI.createAnimation({bottom:0});
	this.slideOutAnim =  Titanium.UI.createAnimation({bottom:-height});

	this.setField = function( field )
	{
		if( this.field )
		{
			this.view.remove(field);
		}
		this.field = field;
		
		this.view.add(field);
		this.field.top = 10;
		this.done.top = this.field.top + this.field.height + 5;
	};
	
	this.slideIn = function()
	{
		Titanium.API.info("edit window slide in... " + this );
		this.view.animate(this.slideInAnim);
	};

	this.slideOut = function()
	{
		this.view.animate(this.slideOutAnim);
	};
	
	this.addToWin = function( win )
	{
		win.add(this.view);
	}
	

	if( field )
	{
		this.setField(field);
	}
	else
	{
		this.field = null;		
	}
};
