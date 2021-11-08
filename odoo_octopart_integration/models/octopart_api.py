from six.moves import urllib
import json
from odoo.exceptions import UserError


class GraphQLClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.token = None
        self.headername = None

    def execute(self, query, variables=None):
        return self._send(query, variables)

    def inject_token(self, token, headername='token'):
        self.token = token
        self.headername = headername

    def _send(self, query, variables):
        data = {'query': query,
                'variables': variables}
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}

        if self.token is not None:
            headers[self.headername] = '{}'.format(self.token)

        req = urllib.request.Request(self.endpoint, json.dumps(data).encode(
            'utf-8'), headers)

        try:
            response = urllib.request.urlopen(req)
            return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print((e.read()))
            print('')
            raise e


def get_parts(client, ids):
    query = '''
    query get_parts($ids: [String!]!) {
        parts(ids: $ids) {
            id
            manufacturer {
                name
            }
            mpn
            category {
                name
            }
        }
    }
    '''

    ids = [str(id) for id in ids]
    resp = client.execute(query, {'ids': ids})

    if "errors" not in resp:
        return json.loads(resp)['data']['parts']
    else:
        raise UserError('\n'.join([error['message'] for error in json.loads(resp)["errors"]]))


def match_mpns(client, mpns, seller=False):
    dsl = '''
    query match_mpns($queries: [PartMatchQuery!]!) {
        multi_match(queries: $queries) {
            hits
            reference
            parts {
                manufacturer {
                    id
                    name
                }
                sellers{
                    company{
                        id
                        name
                    }
                    offers {
                        moq
                        sku
                        inventory_level
                        packaging
                        updated
                        prices{
                            _cache_id
                            currency
                            quantity
                            price
                        }
                    }
                }
                mpn
                descriptions{
                    text
                    credit_string
                    credit_url
                }
            }
        }
    }
    '''

    queries = []
    for mpn in mpns:
        mpn_query = {
            'mpn': mpn,
            'start': 0,
            'limit': 100000,
            'reference': mpn,
        }
        if seller:
            mpn_query['seller'] = seller
        queries.append(mpn_query)
    resp = client.execute(dsl, {'queries': queries})
    if "errors" not in resp:
        return json.loads(resp)['data']['multi_match']
    else:
        raise UserError('\n'.join([error['message'] for error in json.loads(resp)["errors"]]))


def demo_get_sellers(client):
    dsl = '''
        query demo_get_sellers() {
            sellers {
                id
                name
          }
        }
        '''
    resp = client.execute(dsl)
    return json.loads(resp)['data']['sellers']


def demo_part_get(client):
    ids = ["1", "2", "asdf", "4"]
    parts = get_parts(client, ids)
    return parts


def demo_match_mpns(client):
    mpns = [
        'CC4V-T1A 32.768KHZ +-20PPM 9PF',
        'LMC6482IMX/NOPB',
        'PCF8583T/F5,112',
        'FH12-5S-1SH(55)',
    ]
    matches = match_mpns(client, mpns)
    return matches
