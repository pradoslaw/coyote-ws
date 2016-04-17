import urllib2
import json

class GeoIp:
    """
    geo-ip.pl service
    """

    VERSION = '1.0'

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def ip(self, ip, callback):
        """
        Geocode based on IP

        :param ip:
        :param callback
        :return:
        """
        callback(self.request('ip/' + ip))

    def request(self, path):
        """
        Make a request and return JSON object

        :param path:
        :return:
        """
        return json.loads(urllib2.urlopen(self.get_base_url() + path).read())

    def get_base_url(self):
        """
        Get base URL for the request

        :return:
        """
        return 'http://%s%s/%s/' % (self.host, ':' + self.port if self.port != '' else '', self.VERSION)