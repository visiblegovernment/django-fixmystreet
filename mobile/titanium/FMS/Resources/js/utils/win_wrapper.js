
function WinWrapper( win )
{
	this.win = win;
	
	this.open = function( params )
	{
		this.win.open(params);
	}
	
	this.close = function()
	{
		this.win.close();
	}
	
	this.show = function()
	{
		this.win.show();
	}
	
	this.hide = function()
	{
		this.win.hide();
	}
	
	this.addEventListener = function( name, func )
	{
		this.win.addEventListener(name,func);
	}
};