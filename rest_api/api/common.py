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

from Crypto.Cipher import AES

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from sawtooth_signing import CryptoFactory
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from api.errors import ApiBadRequest

from db import auth_query

from marketplace_transaction.protobuf import rule_pb2


def validate_fields(required_fields, request_json):
    try:
        for field in required_fields:
            if request_json.get(field) is None:
                raise ApiBadRequest("{} is required".format(field))
    except (ValueError, AttributeError):
        raise ApiBadRequest("Improper JSON format")


def encrypt_private_key(aes_key, public_key, private_key):
    init_vector = bytes.fromhex(public_key[:32])
    cipher = AES.new(bytes.fromhex(aes_key), AES.MODE_CBC, init_vector)
    return cipher.encrypt(private_key)


def decrypt_private_key(aes_key, public_key, encrypted_private_key):
    init_vector = bytes.fromhex(public_key[:32])
    cipher = AES.new(bytes.fromhex(aes_key), AES.MODE_CBC, init_vector)
    return cipher.decrypt(encrypted_private_key)


async def get_signer(request):
    email = deserialize_auth_token(
        request.app.config.SECRET_KEY, request.token).get('email')
    auth_info = await auth_query.fetch_info_by_email(
        request.app.config.DB_CONN, email)
    private_key_hex = decrypt_private_key(
        request.app.config.AES_KEY,
        auth_info.get('public_key'),
        auth_info.get('encrypted_private_key'))
    private_key = Secp256k1PrivateKey.from_hex(private_key_hex)
    return CryptoFactory(request.app.config.CONTEXT).new_signer(private_key)


def generate_auth_token(secret_key, email, public_key):
    serializer = Serializer(secret_key)
    token = serializer.dumps({'email': email, 'public_key': public_key})
    return token.decode('ascii')


def deserialize_auth_token(secret_key, token):
    serializer = Serializer(secret_key)
    return serializer.loads(token)


def proto_wrap_rules(rules):
    rule_protos = []
    if rules is not None:
        for rule in rules:
            try:
                rule_proto = rule_pb2.Rule(type=rule['type'])
            except IndexError:
                raise ApiBadRequest("Improper rule format")
            except ValueError:
                raise ApiBadRequest("Invalid rule type")
            except KeyError:
                raise ApiBadRequest("Rule type is required")
            if rule.get('value') is not None:
                rule_proto.value = value_to_csv(rule['value'])
            rule_protos.append(rule_proto)
    return rule_protos


def value_to_csv(value):
    if isinstance(value, (list, tuple)):
        csv = ",".join(map(str, value))
        return bytes(csv, 'utf-8')
    else:
        raise ApiBadRequest("Rule value must be a JSON array")
