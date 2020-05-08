class DocNotInDatabase(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        print('calling str')
        if self.message:
            return f'DocNotInDatabase: {self.message}'
        else:
            return 'DocNotInDatabase has been raised'
