import os

def cdn(self, path):
    return '//' + os.environ['CDN'] + '/' + path