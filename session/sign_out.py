from __future__ import print_function

import hashlib
import Cookie
import time
import datetime
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr


def sign_out(event, context):
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

    if atoken is not None and atoken is not '':
        found, user = find_user_by_atoken(User, atoken)

    if (not found) or (atoken is None):
        raise Exception('Unauthorized')

    User.update_item(
        Key={'uid': user['uid']},
        UpdateExpression='SET atoken_expiry = :atoken_expiry, rtoken_expiry = :rtoken_expiry',
        ExpressionAttributeValues={
            ':atoken_expiry': 0,
            ':rtoken_expiry': 0,
        }
    )

    user = User.get_item(
        Key={'uid': user['uid']}
    )['Item']

    return {
        'uid': user['uid'],
        'email': user['email'],
        'cookie': 'atoken=""; domain=.execute-api.us-east-1.amazonaws.com; expires={}; path=/'.format(time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime(time.time())))
    }


def find_user_by_atoken(User, atoken):
    user = User.scan(
        FilterExpression=Attr('atoken').eq(atoken)
    )
    found = (user['Count'] != 0)
    return found, user['Items'][0]
