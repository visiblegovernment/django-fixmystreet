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
   var address = geodata.address;
   address = address.replace(/,.*/,'')
   var uri = "/reports/new?lat=" + geodata.Point.coordinates[1] + "&lon=" + geodata.Point.coordinates[0] + "&address=" + address
   return(  encodeURI(uri) ); 
}
    
function html_for_no_results()
{
   	var html =	"<div id='error-msg'>";
   	html += "<p>{% trans "Sorry, we couldn\'t find the address you entered. Please try again with another intersection, address or postal code, or add the name of the city to the end of the search."%}</p>";
    html += "</div>";
    jQuery("#error").html(html).fadeIn(1000);
}        
     
function handle_google_geocode_response(geodata)
{
    if ((geodata.Status.code == 200) && (geodata.Placemark.length > 0 ))
    {
		var url = url_for_geodata(geodata.Placemark[0]);
		document.location = url;
    }
    else
    {
	   	html_for_no_results();
    }
}
     
function reverse_geocode( point )
{
    var geocoder = new  GClientGeocoder();
    geocoder.getLocations(point, handle_google_geocode_response);    
    return true;
}
//]]>
</script>

