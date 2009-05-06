{% autoescape off %}{% block vars %}var map;{% endblock %}
{% block functions %}{% endblock %}
{% block load %}function {{ load_func }}(){
  if (GBrowserIsCompatible()) {
  
    // Create a base icon for all of our markers that specifies the
    // shadow, icon dimensions, etc.
    var baseIcon = new GIcon();
    baseIcon.shadow = "http://www.google.com/mapfiles/shadow50.png";
    baseIcon.iconSize = new GSize(20, 34);
    baseIcon.shadowSize = new GSize(37, 34);
    baseIcon.iconAnchor = new GPoint(9, 34);
    baseIcon.infoWindowAnchor = new GPoint(9, 2);
    baseIcon.infoShadowAnchor = new GPoint(18, 25);
  
    map = new GMap2(document.getElementById("{{ dom_id }}"));
    map.setCenter(new GLatLng({{ center.1 }}, {{ center.0 }}), {{ zoom }});
    {% block controls %}map.addControl(new GSmallMapControl());
    map.addControl(new GMapTypeControl());{% endblock %}
    {% if calc_zoom %}var bounds = new GLatLngBounds(); var tmp_bounds = new GLatLngBounds();{% endif %}
    {% for kml_url in kml_urls %}var kml{{ forloop.counter }} = new GGeoXml("{{ kml_url }}");
    map.addOverlay(kml{{ forloop.counter }});{% endfor %}

    {% for polygon in polygons %}var poly{{ forloop.counter }} = new {{ polygon }};
    map.addOverlay(poly{{ forloop.counter }});
    {% for event in polygon.events %}GEvent.addListener(poly{{ forloop.parentloop.counter }}, {{ event }});{% endfor %}
    {% if calc_zoom %}tmp_bounds = poly{{ forloop.counter }}.getBounds(); bounds.extend(tmp_bounds.getSouthWest()); bounds.extend(tmp_bounds.getNorthEast());{% endif %}{% endfor %}

    {% for polyline in polylines %}var polyline{{ forloop.counter }} = new {{ polyline }};
    map.addOverlay(polyline{{ forloop.counter }});
    {% for event in polyline.events %}GEvent.addListener(polyline{{ forloop.parentloop.counter }}, {{ event }}); {% endfor %}
    {% if calc_zoom %}tmp_bounds = polyline{{ forloop.counter }}.getBounds(); bounds.extend(tmp_bounds.getSouthWest()); bounds.extend(tmp_bounds.getNorthEast());{% endif %}{% endfor %}
    
    {% for marker in markers %} {{marker.icon}}
    var marker{{ forloop.counter }} = new {{ marker }};
    map.addOverlay(marker{{ forloop.counter }});
    {% for event in marker.events %}GEvent.addListener(marker{{ forloop.parentloop.counter }}, {{ event }}); {% endfor %}
    {% endfor %}

    {% if calc_zoom %}map.setCenter(bounds.getCenter(), map.getBoundsZoomLevel(bounds));{% endif %}
    {% block load_extra %}{% endblock %}
  }else {
    alert("Sorry, the Google Maps API is not compatible with this browser.");
  }
}
{% endblock %}{% endautoescape %}
