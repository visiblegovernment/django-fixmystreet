
function AddPhotoForm( width )
{
	var that = new Form("Photo",width);

	that.choosePhotoSourceDialog = Ti.UI.createOptionDialog({
 	 title: 'Add a Photo'
	});


	that.view = that.getView();
	that.view.height = 70;

	that.photoLabel = Ti.UI.createLabel({
		top: 10,
		left: 70,
		width: 280,
		height: 30,
		color: '#fff',
		font: {
			fontSize: 16,
			fontWeight: 'bold'
		},
		text: 'Add a Photo'
	});
	
	 that.photoLabelDesc = Ti.UI.createLabel({
		top: 35,
		left: 70,
		width: 280,
		height: 30,
		color: '#eee',
		font: {
			fontSize: 12,
			fontWeight: 'normal'
		},
		text: 'Share a picture of the problem'
	});
	
	that.view.add(that.photoLabel);
	that.view.add(that.photoLabelDesc);

	that.photoView = Ti.UI.createView({
		top: 10,
		left: 10,
		width: 50,
		height: 50,
		backgroundColor: '#222',
		borderRadius: 6
	});
	
	that.currentPhotoView = Ti.UI.createImageView({
       top: 1,
       left: 1,
       height: 44,
       width: 44,
       borderRadius: 2
    });
	
	 that.photoButtonBg = Ti.UI.createView({
		top: 2,
		left: ((that.photoView.width - 46) / 2),
		width: 46,
		height: 46,
		backgroundColor: '#000',
		borderRadius: 5
	});
	
	that.addPhotoButton = Ti.UI.createButton({
		top: 1,
		left: 1,
		width: 44,
		height: 44,
		backgroundImage: '/images/icon_camera.png',
		backgroundSelectedImage: '/images/icon_camera.png',
		backgroundDisabledImage: '/images/icon_camera.png'
	});
	
	that.photoButtonBg.add(that.addPhotoButton);
	that.photoView.add(that.photoButtonBg);
	that.view.add(that.photoView);

	that.displayPhotoSourceChooser = function() 
	{
		if(that.currentImageAdded) 
 		{
    		that.choosePhotoSourceDialog.options = ['New Photo', 'Choose Existing', 'Remove Existing', 'Cancel'];
  		} 
  		else 
  		{
		    that.choosePhotoSourceDialog.options = ['New Photo', 'Choose Existing','Cancel'];
 		}
  		that.choosePhotoSourceDialog.show();
	}

	that.removeCurrentPhoto = function()
	{
		if(that.currentImageAdded)
 	    {
    	 	that.photoButtonBg.remove(that.currentPhotoView);
       		that.currentImageAdded = false;
   		 }
	}

	that.onPhotoSelected = function( media )
	{
		Titanium.API.info("new report: on photo selected" );
		that.removeCurrentPhoto();
    	that.currentPhotoView.image = media;
    	that.photoButtonBg.add(that.currentPhotoView);
    	that.currentImageAdded = true;
	}


	that.choosePhotoSource = function( pe ) 
	{
		switch(pe.index) {
		    case 0:
		   		Ti.Media.showCamera({
 		    		mediaTypes: [Ti.Media.MEDIA_TYPE_PHOTO],
		    		success: function(e) { that.onPhotoSelected( e.media );  },
					error:function(error) {
					Ti.UI.createAlertDialog({
			  		title:'Sorry',
			  		message:'This device either cannot take photos or there was a problem saving this photo.'
					}).show();
				},
				allowImageEditing:false,
				saveToPhotoGallery:true
 				});
 				break;
 		   case 1:
			  	Titanium.Media.openPhotoGallery({
  				  mediaTypes: [Titanium.Media.MEDIA_TYPE_PHOTO],
			 	  success: function(e)
   			  	  {
   		 				Titanium.API.info("gallery success" );
    					that.onPhotoSelected(e.media);
    			  },
    			  cancel:function(){},
				  error:function(error)
				  {
						Titanium.API.info("gallery error" +  JSON.stringify(error ) );
				  },
				  allowEditing:false
 			 	});
      			break;
    	case 2:
     		that.removeCurrentPhoto();
      		break;
  		};
	};
	
	that.choosePhotoSourceDialog.addEventListener('click', that.choosePhotoSource );
	that.addPhotoButton.addEventListener('click', that.displayPhotoSourceChooser );
	that.currentPhotoView.addEventListener('click', that.displayPhotoSourceChooser );

	return( that );
};


