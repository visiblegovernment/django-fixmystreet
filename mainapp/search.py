'''
module containing search funcions and exceptions for fixmystreet.ca
'''

from mainapp.models import GoogleAddressLookup, Ward

class SearchException(Exception):
    pass

class SearchAddressException(SearchException):
    pass

class SearchAddressDisambiguateError(SearchAddressException):
    pass

class SearchAddressNotSupported(SearchException):
    pass

def search_address(address, match_index=-1, disambiguate=[]):
    '''
    Tries to parse `address` returning a single point, if the address is
    ambigous `match_index` will be used to pick out the correct address. if
    `match_index` is -1 or not 0 <= `match_index` < len(possible_addresses) the
    disambiguate list is populated with possible addresses and a
    `SearchAddressDisambiguateError` is raised.
    '''
    address_lookup = GoogleAddressLookup( address )

    if not address_lookup.resolve():
        raise SearchAddressException("Sorry, we couldn\'t retreive the coordinates of that location, please use the Back button on your browser and try something more specific or include the city name at the end of your search.")

    if not address_lookup.exists():
        raise SearchAddressException("Sorry, we couldn\'t find the address you entered.  Please try again with another intersection, address or postal code, or add the name of the city to the end of the search.")

    if address_lookup.matches_multiple() and match_index == -1:
        disambiguate += address_lookup.get_match_options()
        raise SearchAddressDisambiguateError('Cannot pinpoint given address')

    point_str = "POINT(" + address_lookup.lon(match_index) + " " + address_lookup.lat(match_index) + ")"
    return point_str

def search_wards(point_str):
    '''
    returns a list of wards that contain `point_str`
    '''
    wards = Ward.objects.filter(geom__contains=point_str)
    if (len(wards) == 0):
        raise SearchAddressNotSupported("Sorry, we don't yet have that area in our database.  Please have your area councillor contact fixmystreet.ca.")
    return wards
