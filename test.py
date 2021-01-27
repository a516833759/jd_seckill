import hashlib


def register(secret):
    md5 = hashlib.md5('6a9a5ba51e2d014bd678f866ee467fd6'.encode(encoding='UTF-8'))
    md5.update(secret.encode(encoding='UTF-8'))
    local_secret = md5.hexdigest()
    print(local_secret)


if __name__ == '__main__':
    register('9f8545518fa6684ebe9060b0fc019a83')
