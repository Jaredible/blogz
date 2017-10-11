import hashlib
import random
import string

def make_salt():
    return ''.join([random.choice(string.ascii_letters) for x in range(5)])

def make_hash(text, salt=None):
    if not salt:
        salt = make_salt()
    hash = hashlib.sha256(str.encode(text + salt)).hexdigest()
    return '{0},{1}'.format(hash, salt)

def check_hash(text, hash):
    salt = hash.split(',')[1]
    return make_hash(text, salt) == hash