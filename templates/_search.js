{% load i18n %}
<script type="text/javascript" src="http://www.google.com/jsapi?key={{GOOGLE_KEY}}"></script>
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js"></script>

<script type="text/javascript">
//<![CDATA[
google.load("maps", "2.167");
jQuery.noConflict();

function url_for_geodata(geodata)
{
   return "/search" + "?lat=" + geodata.Point.coordinates[1] + "&lon=" + geodata.Point.coordinates[0];    	
}
    
function html_for_multiple_matches(array) 
{
  	var html =	"<div id='error-msg'>";
  	html += '<p>{% trans "That address returned more than one result.  Please try again, or select an option below:"%}</p>';
   	html += '<ul>';
	for (var i=0; i<array.length; i++)
	{
		html += '<li><a href="';
		html += url_for_geodata( array[i] );
		html += '">';
		html += array[i].address;
		html += '</a></li>';
	}
	html += '</ul>';
    html += '</div>'

    jQuery("#search-error").html(html).fadeIn(1000);
}    

function html_for_no_results()
{
   	var html =	"<div id='error-msg'>";
   	html += '<p>{% trans "Sorry, we couldn\'t find the address you entered. Please try again with another intersection, address or postal code, or add the name of the city to the end of the search."%}</p>';
    html += '</div>'
    jQuery("#search-error").html(html).fadeIn(1000);
}        
    
 
function handle_google_geocode_response(geodata)
{
    if ((geodata.Status.code == 200) && (geodata.Placemark.length > 0 ))
    {
      	if ( geodata.Placemark.length  > 1)
       	{
			html_for_multiple_matches(geodata.Placemark);   		
       	}
		else
		{
			var url = url_for_geodata(geodata.Placemark[0]);
			document.location = url;
		}
    }
    else
    {
	   	html_for_no_results();
    }
}
    
    
function do_search()
{
    var search_term = jQuery('#search_box').val();
    var geocoder = new  GClientGeocoder();
    geocoder.getLocations(search_term, handle_google_geocode_response);    
    return true;
}


jQuery(document).ready(function($) 
{

	$("#search_box").keyup(function(event){
  		if(event.keyCode == 13){
    	$("#search_button").click();
  		}
	});

{% if location %}
   
    function find_nearby_reports()
    {
        var query = "{{location|escapejs}}";
        var geocoder = new GClientGeocoder();
        geocoder.getLocations(query, handle_google_geocode_response);    
    }

    find_nearby_reports();
{% endif %}

});
//]]>
</script>