
Titanium.include("/js/utils/win_wrapper.js")

function MapPrompt()
{
	that = new WinWrapper( Titanium.UI.createWindow({  
		height: 150,
		width: 301,
		borderRadius: 10,
		touchEnabled: false,
		orientationModes: [
			Titanium.UI.PORTRAIT,
			Titanium.UI.UPSIDE_PORTRAIT,
			Titanium.UI.LANDSCAPE_LEFT,
			Titanium.UI.LANDSCAPE_RIGHT
		]
	}));

	that.promptView = Titanium.UI.createView({
			id:'mapclickprompt',
			height:70,
			width:300,
			borderRadius:10,
			backgroundColor:'#000',
			opacity:0.7,
			touchEnabled:false
	});

	that.promptLabel = Titanium.UI.createLabel({
		id:'mapclicklabel',
		text:'Click target to report a new problem.\nMove map to move target.',
		color:'#fff',
		width:301,
		height:'auto',
		textAlign:'center'
	});
	
	that.promptView.add(that.promptLabel);
	that.win.add(that.promptView);  

	return( that );
}