from __future__ import print_function

import hashlib
import boto3
from boto3.dynamodb.conditions import Key, Attr


def sign_in_by_email(event, context):
    User = boto3.resource('dynamodb').Table('FmSsoUsers')
    Auth = boto3.resource('dynamodb').Table('FmSsoAuths')

    email = event['email']
    password = event['password']

    auth_query = Auth.scan(
        FilterExpression=Attr('email').eq(email)
    )

    if(auth_query['Count'] == 0):
        # Auth with given email not found
        raise Exception('Unauthorized')

    auth_rcd = auth_query['Items'][0]
    encrypted_password_key = 'fmsso'  # TODO: Change to conf table value

    if validate_password(password, auth_rcd, encrypted_password_key):
        # TODO: find user record from auth
        user = User.get_item(
            Key={'id': auth_rcd['user_id']}
        )
        # TODO: refresh token

        return {
            'access_token': user['atoken'],
            'refresh_token': user['rtoken'],
        }

    else:
        raise Exception('Unauthorized')


def validate_password(password, auth_rcd, encrypted_password_key):
    salt = auth_rcd['salt']
    encrypted_password = auth_rcd['encrypted_password']

    return hashlib.sha512('%s%s%s' % (encrypted_password_key, password, salt)).hexdigest() == encrypted_password
