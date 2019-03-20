#   Copyright (c) 2019 Neel Network

#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:

#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.
#   ---------------------------------------------------------------------------

from functools import wraps

import bcrypt

from itsdangerous import BadSignature

from sanic import Blueprint
from sanic.response import json

from api import common
from api.errors import ApiUnauthorized
from db import auth_query


AUTH_BP = Blueprint('auth')


@AUTH_BP.post('authorization')
async def authorize(request):
    """Requests an authorization token for a registered Account"""
    required_fields = ['email', 'password']
    common.validate_fields(required_fields, request.json)
    password = bytes(request.json.get('password'), 'utf-8')
    auth_info = await auth_query.fetch_info_by_email(
        request.app.config.DB_CONN, request.json.get('email'))
    if auth_info is None:
        raise ApiUnauthorized("No user with that email exists")
    hashed_password = auth_info.get('hashed_password')
    if not bcrypt.checkpw(password, hashed_password):
        raise ApiUnauthorized("Incorrect email or password")
    token = common.generate_auth_token(
        request.app.config.SECRET_KEY,
        auth_info.get('email'),
        auth_info.get('public_key'))
    return json(
        {
            'authorization': token
        })


def authorized():
    """Verifies that the token is valid and belongs to an existing user"""
    def decorator(func):
        @wraps(func)
        async def decorated_function(request, *args, **kwargs):
            if request.token is None:
                raise ApiUnauthorized("No bearer token provided")
            try:
                email = common.deserialize_auth_token(
                    request.app.config.SECRET_KEY,
                    request.token).get('email')
                auth_info = await auth_query.fetch_info_by_email(
                    request.app.config.DB_CONN, email)
                if auth_info is None:
                    raise ApiUnauthorized(
                        "Token does not belong to an existing user")
            except BadSignature:
                raise ApiUnauthorized("Invalid bearer token")
            response = await func(request, *args, **kwargs)
            return response
        return decorated_function
    return decorator
