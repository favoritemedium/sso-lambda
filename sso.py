from __future__ import print_function

import re
import time
import datetime
import json
import Cookie
import boto3
from boto3.dynamodb.conditions import Key, Attr


def sso(event, context):
    User = boto3.resource('dynamodb').Table('FmSsoUsers')

    params = event['params']
    atoken_query = params['querystring'].get('atoken', None)
    cookie_str = params['header'].get('Cookie', None)
    found = False

    atoken = None
    if atoken_query is not None:
        atoken = atoken_query
    elif cookie_str is not None:
        cookie = Cookie.SimpleCookie()
        cookie.load(cookie_str.encode('utf-8'))
        if 'atoken' in cookie:
            atoken = cookie['atoken'].value

    if atoken is not None:
        found, user = find_user_by_atoken(User, atoken)

    if (not found) or (atoken is None):
        raise Exception('Unauthorized')

    if user:
        # TODO: Refresh token
        pass

    return {
        'access_token': user['atoken'],
        'refresh_token': user['rtoken'],
    }


def find_user_by_atoken(User, atoken):
    user = User.scan(
        FilterExpression=Attr('atoken').eq(atoken)
    )
    found = (user['Count'] != 0)
    return found, user['Items'][0]
