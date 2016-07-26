from __future__ import print_function

import json
import time
import random
import string
import uuid
import requests
from conf import google_conf
import boto3
from boto3.dynamodb.conditions import Key, Attr

print('Loading function')

conf = {
    'atoken_len': 48,
    'atoken_expiry': 7 * 24 * 3600,  # 7 days
    'rtoken_len': 48,
    'rtoken_expiry': 14 * 24 * 3600,  # 14 days
    'cookie_expiry': 14 * 24 * 3600,  # 14 days
}


def google_callback(event, context):
    User = boto3.resource('dynamodb').Table('FmSsoUsers')
    Auth = boto3.resource('dynamodb').Table('FmSsoAuths')

    print('-' * 20)
    print(event)
    print('-' * 20)

    code = event['code']  # Param passed from URL

    # Exchange access_token with code
    g_token = requests.post(google_conf['token_api'], data={
        'code': code,
        'client_id': google_conf['client_id'],
        'client_secret': google_conf['client_secret'],
        'redirect_uri': google_conf['redirect_uri'],
        'grant_type': 'authorization_code',
    }).json()

    auth_data = Auth.get_item(
        Key={'client_id': g_token['id_token']}
    )

    # Get user profile info
    user_profile_req = requests.get(google_conf['me_api'], params={
        'access_token': g_token['access_token']
    })

    user_profile = user_profile_req.json()

    try:
        auth_data['displayName'] = user_profile.get('displayName', '')
        auth_data['email'] = user_profile['emails'][0]['value']
    except KeyError:
        print('KeyError')

    # Upsert Auth record
    Auth.update_item(
        Key={'client_id': g_token['id_token']},
        UpdateExpression='SET displayName = :displayName, access_token = :atoken, email = :email',
        ExpressionAttributeValues={
            ':displayName': auth_data['displayName'],
            ':atoken': g_token['access_token'],
            ':email': auth_data['email'],
        }
    )

    auth_rcd = Auth.get_item(
        Key={'client_id': g_token['id_token']},
    )

    # Find User record
    user_query = User.scan(
        FilterExpression=Attr('email').eq(auth_data['email'])
    )

    if(user_query['Count'] == 0):
        uid = str(uuid.uuid1())
        (atoken, atoken_expiry, rtoken, rtoken_expiry) = gen_tokens()
        User.put_item(
            Item={
                'uid': uid,
                'email': auth_data['email'],
                'last_sign_in': int(time.time()),
                'sign_in_count': 1,
                'atoken': atoken,
                'atoken_expiry': atoken_expiry,
                'rtoken': rtoken,
                'rtoken_expiry': rtoken_expiry,
            }
        )
        user_query = User.get_item(Key={'uid': uid})

    print('-' * 20)
    print(user_query)
    print('-' * 20)

    user = user_query['Items'][0]
    expires = time.time() + conf['cookie_expiry']

    if user['atoken_expiry'] < int(time.time()) or user['rtoken_expiry'] < int(time.time()):
        (atoken, atoken_expiry, rtoken, rtoken_expiry) = gen_tokens()
        User.update_item(
            Key={'uid': user['uid']},
            UpdateExpression='SET atoken = :atoken, atoken_expiry = :atoken_expiry, rtoken = :rtoken, rtoken_expiry = :rtoken_expiry',
            ExpressionAttributeValues={
                ':atoken': atoken,
                ':atoken_expiry': atoken_expiry,
                ':rtoken': rtoken,
                ':rtoken_expiry': rtoken_expiry,
            }
        )

    return {
        'uid': user['uid'],
        'email': user['email'],
        'atoken': user['atoken'],
        'atoken_expiry': user['atoken_expiry'],
        'rtoken': user['rtoken'],
        'rtoken_expiry': user['rtoken_expiry'],
        'cookie': 'atoken={}; domain=.execute-api.us-east-1.amazonaws.com; expires={}; path=/'.format(user['atoken'], time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime(expires)))
    }


def random_str(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))


def gen_tokens():
    # atoken, rtoken, atoken_expiry, rtoken_expiry
    return (
        random_str(conf['atoken_len']),
        int(time.time() + conf['atoken_expiry']),
        random_str(conf['rtoken_len']),
        int(time.time() + conf['rtoken_expiry']),
    )
