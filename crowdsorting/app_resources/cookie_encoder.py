import objcrypt

class CookieCrypter:
    def __init__(self):
        from crowdsorting.settings.configurables import COOKIE_KEY
        self.crypter = objcrypt.Crypter(COOKIE_KEY, 'cbc')

    def encrypt(self, d):
        return d
        # d is a dictionary
        d = {k: v.encode('utf-8') for k, v in d.items()}
        return self.crypter.encrypt_object(d)

    def decrypt(self, e):
        return e
        # e is an encrypted dictionary
        return self.crypter.decrypt_object(e)
