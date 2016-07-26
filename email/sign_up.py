from __future__ import print_function

import time
import random
import string
import uuid
import hashlib
import boto3
from boto3.dynamodb.conditions import Key, Attr

conf = {
    'atoken_len': 48,
    'atoken_expiry': 7 * 24 * 3600,  # 7 days
    'rtoken_len': 48,
    'rtoken_expiry': 14 * 24 * 3600,  # 14 days
    'cookie_expiry': 14 * 24 * 3600,  # 14 days
}


def sign_up_by_email(event, context):
    User = boto3.resource('dynamodb').Table('FmSsoUsers')
    Auth = boto3.resource('dynamodb').Table('FmSsoAuths')

    email = event['email']
    password = event['password']

    auth_rcds = Auth.scan(
        FilterExpression=Attr('email').eq(email)
    )

    user_rcds = User.scan(
        FilterExpression=Attr('email').eq(email)
    )

    if(auth_rcds['Count'] != 0):
        # User exists, raise error
        raise Exception('User already registered!')
    elif(user_rcds['Count'] != 0):
        raise Exception(
            'User already registered! Please login with original account and associate in it')

    user = create_auth(Auth, User, email, password)
    expires = time.time() + conf['cookie_expiry']

    return {
        'uid': user['uid'],
        'email': user['email'],
        'atoken': user['atoken'],
        'atoken_expiry': user['atoken_expiry'],
        'rtoken': user['rtoken'],
        'rtoken_expiry': user['rtoken_expiry'],
        'cookie': 'atoken={}; domain=.amazonaws.com; expires={}; path=/'.format(user['atoken'], time.strftime("%a, %d-%b-%Y %T GMT", time.gmtime(expires)))
    }


def create_auth(Auth, User, email, password):
    encrypted_password_key = 'fmsso'  # TODO: Change to conf table value
    salt = random_str(24)
    encrypted_password = hashlib.sha512('%s%s%s' % (
        encrypted_password_key, password, salt)).hexdigest()

    uid = str(uuid.uuid1())

    resp = Auth.put_item(
        Item={
            'client_id': email,
            'email': email,
            'salt': salt,
            'encrypted_password': encrypted_password,
            'created_at': int(time.time()),  # Save epoch second
            'uid': uid,
        }
    )

    auth = Auth.get_item(Key={'client_id': email})['Item']
    (atoken, atoken_expiry, rtoken, rtoken_expiry) = gen_tokens()

    User.put_item(
        Item={
            'uid': uid,
            'email': email,
            'last_sign_in': int(time.time()),
            'sign_in_count': 1,
            'atoken': atoken,
            'atoken_expiry': atoken_expiry,
            'rtoken': rtoken,
            'rtoken_expiry': rtoken_expiry,
        }
    )

    return User.get_item(Key={'uid': uid})['Item']


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
