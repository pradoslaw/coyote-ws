import tornado.web
import tornado.template
import os
from utils.geoip import GeoIp
from tornadoes import ESConnection
from utils.cdn import cdn
import json

class JobHandler(tornado.web.RequestHandler):

    @tornado.gen.engine
    def get(self):
        geoip = GeoIp(os.environ['GEOIP_HOST'], os.environ['GEOIP_PORT'])
        loc = yield tornado.gen.Task(geoip.ip, '188.122.16.173')

        if loc:
            self.search(loc)

    @tornado.web.asynchronous
    def search(self, loc):
        es = ESConnection("localhost", 9200)
        es.search(callback=self.callback, index=os.environ['DEFAULT_INDEX'], type="jobs", source=self.get_body(loc))

    def callback(self, res):
        res = json.loads(res.body)

        if res['hits']['total'] > 0:
            self.render(os.path.dirname(__file__) + '/../templates/jobs.html', jobs=res['hits']['hits'])

    def get_body(self, loc):
        return {
            "query": {
                "filtered": {
                    "query": {
                        "match_all": {}
                    },
                    "filter": {
                        "range": {
                            "deadline_at": {
                                "gte": "now"
                            }
                        }
                    }
                }
            },
            "size": 4,
            "sort": [
                {
                    "_geo_distance": {
                        "locations.coordinates": {
                            "lat": loc['latitude'],
                            "lon": loc['longitude']
                        },
                        "order": "asc",
                        "unit": "km",
                        "distance_type": "plane"
                    }
                }
            ]
        }
