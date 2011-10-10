var win = Ti.UI.currentWindow;

var label1 = Titanium.UI.createLabel({
	color:'#999',
	text:'I am ABOUT window',
	font:{fontSize:20,fontFamily:'Helvetica Neue'},
	textAlign:'center',
	width:'auto'
});

win.add(label1);