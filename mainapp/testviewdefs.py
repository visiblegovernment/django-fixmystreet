# urls used by testview app

TEST_URLS = [   
    ('/'         , 'home'), 
    ('/cities/'  , 'city list'),
    ('/cities/1' , 'ward list'),
    ('/wards/3'  , 'show ward'),
    ('/search?q=slater street', 'ambigous search'),
    ('/search?q=somerset and empress,ottawa canada', 'search'),
    ('/reports/new?&lat=45.41958499972712&lon=-75.7028603553772','file new report'),
    ('/reports/114', 'unconfirmed report'),
    ('/reports/331', 'report with no updates'),
    ('/reports/491', 'updated report'),
    ('/reports/479', 'fixed report'),
    ('/reports/updates/confirm/c0c3698d06f3485b7cb69addd21b2b6f', 'confirm report'),
    ('/reports/updates/create/', 'confirm update'),
    ('/reports/331/flags', 'flag report'),
    ('/reports/331/flags/thanks', 'after flagging a report'),
    ('/contact/', 'contact form'),
    ('/contact/thanks', 'after submitting contact form'),
    ('/about', 'about') 
    ]

FIXTURES = [ 'testview_report_fixtures.json' ]