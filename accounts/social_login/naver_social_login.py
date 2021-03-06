from datetime import datetime
from uuid import uuid4

import requests
from django.conf import settings

from accounts.models import User


class NaverSocialLogin():
    social_type = 'NAVER'
    app_key = settings.NAVER_APP_KEY
    app_secret_key = settings.NAVER_APP_SECRET_KEY
    redirect_uri = settings.NAVER_REDIRECT_URI
    code_request_url = 'https://nid.naver.com/oauth2.0/authorize'
    access_token_request_url = 'https://nid.naver.com/oauth2.0/token'
    user_data_request_url = 'https://openapi.naver.com/v1/nid/me'

    def __init__(self, state_token_code):
        self.state_token_code = state_token_code

    def login(self, user_data_per_field):
        if not User.objects.filter(email=user_data_per_field['email'], social=user_data_per_field['social']):
            raise AssertionError('해당 네이버 계정의 사용자는 존재하지 않습니다.')
        return User.objects.get(email=user_data_per_field['email'], social=user_data_per_field['social'])
    
    def sign_up(self, user_data_per_field):
        user = User.objects.filter(email=user_data_per_field['email'])
        if user:
            raise AssertionError(f'이미 {user.social}로 가입했습니다. {user.social}로 로그인 해주세요.')
        
        username = self._generate_unique_username()
        user = User.objects.create(
            email=user_data_per_field['email'],
            username=username,
            gender=user_data_per_field['gender'],
            social=user_data_per_field['social'],
            birth_year=user_data_per_field['birth_year'])
        return user

    def _generate_unique_username(self):
        username = uuid4().hex[:8]
        while User.objects.filter(username=username).exists():
            username = uuid4().hex[:8]
        return username

    def get_auth_url(self):
        body = {
            'client_id': self.app_key,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'state': self.state_token_code
        }
        query_string = '&'.join(['%s=%s' % (key, value) for (key, value) in body.items()])
        code_request_url = f'{self.code_request_url}?{query_string}'
        return code_request_url

    def get_user_data(self, request):
        code = self._get_code(request)
        access_token_by_type = self._get_access_token_by_type(code)
        user_social_data = self._get_user_social_data(access_token_by_type)
        return self._parse_user_data(user_social_data)
        
    def _get_code(self, request):
        code = request.query_params.get('code', None)
        if code is None:
            raise AssertionError('네이버 코드를 가져오는데 실패했습니다.')
        return code
    
    def _get_access_token_by_type(self, code):
        body = {
            'client_id': self.app_key,
            'client_secret': self.app_secret_key,
            'grant_type': 'authorization_code',
            'state': self.state_token_code,
            'code': code
        }
        query_string = '&'.join(['%s=%s' % (key, value) for (key, value) in body.items()])
        access_token_request_url = f'{self.access_token_request_url}?{query_string}'
        try:
            response = requests.get(access_token_request_url)
            access_token = response.json()['access_token']
            token_type = response.json()['token_type']
        except Exception as e:
            raise AssertionError('네이버 액세스 토큰을 가져오는데 실패했습니다.')
        return {
            'access_token': access_token,
            'token_type': token_type
        }

    def _get_user_social_data(self, access_token_by_type):
        headers = {'Authorization': f"{access_token_by_type['token_type']} {access_token_by_type['access_token']}"}

        response = requests.post(self.user_data_request_url, headers=headers)
        if response.status_code != 200:
            raise AssertionError('네이버 사용자 정보를 가져오는데 실패했습니다.')
        return response
        
    
    def _parse_user_data(self, user_social_data):
        user_data = user_social_data.json().get('response')
        user_data_per_field = dict()

        user_data_per_field['email'] = self._get_email(user_data)
        user_data_per_field['gender'] = self._get_gender(user_data)
        user_data_per_field['social'] = self._get_social(user_data)
        user_data_per_field['birth_year'] = self._get_brith_year(user_data)

        return user_data_per_field

    def _get_email(self, data):
        try:
            return data.get('email')
        except:
            raise ValueError('이메일 정보를 받아올 수 없습니다. 네이버 계정의 권한 설정을 확인하세요.')

    def _get_gender(self, data):
        try:
            gender = data.get('gender')
        except:
            raise ValueError('성별 정보를 받아올 수 없습니다. 네이버 계정의 권한 설정을 확인하세요.')
        return self._convert_gender(gender)
        
    def _convert_gender(self, gender):
        if gender == 'M':
            return 'MAN'
        elif gender == 'F':
            return 'WOMAN'

    def _get_social(self, data):
        return self.social_type

    def _get_brith_year(self, data):
        try:
            age_range = data.get('age')
        except:
            raise ValueError('연령대 정보를 받아올 수 없습니다. 네이버 계정의 권한 설정을 확인하세요.')
        return self._convert_age_range_to_age(age_range)
    
    def _convert_age_range_to_age(self, age_range):
        age = 0
        for boundary in age_range.split('-'):
            if boundary.isdecimal():
                age += int(boundary)
            else:
                age += age
        age //= 2
        birth_year = datetime.now().year - age
        return birth_year + 1
