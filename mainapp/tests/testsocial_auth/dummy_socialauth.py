"""
Dummy Auth
"""

from social_auth.backends import SocialAuthBackend,BaseAuth
from django.contrib.auth import authenticate

class DummyBackend(SocialAuthBackend):
    name = 'dummy'

    def get_user_details(self, response):
        return {'username': response['username'],
                'email': response.get('email', ''),
                'fullname': response.get('first_name',"") + " " + response.get('last_name',''),
                'first_name': response.get('first_name', ''),
                'last_name': response.get('last_name', '')}


    def get_user_id(self, details, response):
        "OAuth providers return an unique user id in response"""
        if not response.get('id',None):
            raise ValueError('Missing user id')

        return response['id']


class DummyAuth(BaseAuth):
    AUTH_BACKEND = DummyBackend

        
    def auth_complete(self, *args, **kwargs):
        """Returns user, might be logged in"""
        response = { 'email': self.data.get('email',''),
                     'username': self.data.get('username',''),
                     'first_name': self.data.get('first_name',''),
                     'last_name': self.data.get('last_name','')
                    }
        
        if self.data.get('uid',None):
            response['id'] = self.data.get('uid')
            
        kwargs.update({'response': response, DummyBackend.name: True})
        return authenticate(*args, **kwargs)




# Backend definition
BACKENDS = {
    'dummy': DummyAuth,
}
