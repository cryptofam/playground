#!/usr/bin/env python
# coding=utf-8

from kuconfig import key, secret
import base64
import hashlib
import hmac
import time
import requests

class Client(object):

    API_URL = 'https://api.kucoin.com'
    API_VERSION = 'v1'

    _last_timestamp = None

    def __init__(self, api_key, api_secret):
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()

    def _init_session(self):
        session = requests.session()
        headers = {'Accept': 'application/json',
                   'User-Agent': 'python-kucoin',
                   'KC-API-KEY': self.API_KEY,
                   'HTTP_ACCEPT_LANGUAGE': 'en-US',
                   'Accept-Language': 'en-US'}
        session.headers.update(headers)
        return session

    def _order_params_for_sig(self, data):
        strs = []
        for key in sorted(data):
            strs.append("{}={}".format(key, data[key]))
        return '&'.join(strs)

    def _generate_signature(self, path, data, nonce):
        query_string = self._order_params_for_sig(data)
        sig_str = ("{}/{}/{}".format(path, nonce, query_string)).encode('utf-8')
        m = hmac.new(self.API_SECRET.encode('utf-8'), base64.b64encode(sig_str), hashlib.sha256)
        return m.hexdigest()

    def _create_path(self, method, path):
        return '/{}/{}'.format(self.API_VERSION, path)

    def _create_uri(self, path):
        return '{}{}'.format(self.API_URL, path)

    def _request(self, method, path, signed, **kwargs):
        kwargs['data'] = kwargs.get('data', {})
        kwargs['headers'] = kwargs.get('headers', {})

        full_path = self._create_path(method, path)
        uri = self._create_uri(full_path)

        if signed:
            # generate signature
            nonce = int(time.time() * 1000)
            kwargs['headers']['KC-API-NONCE'] = str(nonce)
            kwargs['headers']['KC-API-SIGNATURE'] = self._generate_signature(full_path, kwargs['data'], nonce)

        if kwargs['data'] and method == 'get':
            kwargs['params'] = kwargs['data']
            del(kwargs['data'])

        response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response(response)

    def _handle_response(self, response):
        if not str(response.status_code).startswith('2'):
            raise Exception(response)
        try:
            json = response.json()
            self._last_timestamp = None
            if 'timestamp' in json:
                self._last_timestamp = json['timestamp']

            # by default return full response
            res = json
            # if it's a normal response we have a data attribute, return that
            if 'data' in json:
                res = json['data']
            return res
        except ValueError:
            raise Exception('Invalid Response: %s' % response.text)

    def _get(self, path, signed=False, **kwargs):
        return self._request('get', path, signed, **kwargs)

    def _post(self, path, signed=False, **kwargs):
        return self._request('post', path, signed, **kwargs)

    def get_coin_balance(self, coin):
        return self._get('account/{}/balance'.format(coin), True)

    def get_all_balances(self, limit=None, page=None):
        data = {}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page

        return self._get('account/balance', True, data=data)

    # Trading Endpoints
    def create_order(self, symbol, order_type, price, amount):
        data = {
            'symbol': symbol,
            'type': order_type,
            'price': price,
            'amount': amount
        }

        return self._post('order', True, data=data)

    def create_buy_order(self, symbol, price, amount):
        return self.create_order(symbol, 'BUY', price, amount)

    def create_sell_order(self, symbol, price, amount):
        return self.create_order(symbol, 'SELL', price, amount)

    def get_active_orders(self, symbol, kv_format=False):
        data = {'symbol': symbol}
        return self._get('order/active', True, data=data)

    def cancel_order(self, symbol, order_id, order_type):
        data = {
            'symbol': symbol,
            'orderOid': order_id,
            'type': order_type
        }

        return self._post('cancel-order', True, data=data)

    def get_order_details(self, symbol, order_type, limit=None, page=None, order_id=None):
        data = {'type': order_type}
        if limit:
            data['limit'] = limit
        if page:
            data['page'] = page
        if order_id:
            data['orderOid'] = order_id

        return self._get('{}/order/detail'.format(symbol), True, data=data)

    # Market Endpoints
    def get_tick(self, symbol):
        data = {'symbol': symbol}
        return self._get('open/tick', False, data=data)

    def get_order_book(self, symbol, group=None, limit=None):
        data = {'symbol': symbol}
        if group:
            data['group'] = group
        if limit:
            data['limit'] = limit

        return self._get('open/orders', False, data=data)

    def get_coin_list(self):
        return self._get('market/open/coins-list')

if __name__ == '__main__':
    k = Client(api_key=key, api_secret=secret)
    print(k.get_order_book(symbol='TKY-ETH'))
