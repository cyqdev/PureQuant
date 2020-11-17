import time
import hashlib
from purequant.time import get_cur_timestamp
from purequant.exchange.rq import rq, get, post

ROOT_URL = 'https://www.mxc.ceo'

headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    "Accept": "application/json",
}

class Mxc:

    def __init__(self, access_key, secret_key):
        self.__access_key = access_key
        self.__secret_key = secret_key

    """
    公共
    """

    def get_markets(self):
        """获取市场列表信息"""
        url = ROOT_URL + '/open/api/v1/data/markets'
        response = rq('GET', url, headers=headers)
        return response.json()

    def get_markets_info(self):
        """获取交易对信息"""
        url = ROOT_URL + '/open/api/v1/data/markets_info'
        response = rq('GET', url, headers=headers)
        return response.json()

    def get_depth(self, symbol, depth):
        """获取深度信息"""
        symbol = symbol
        depth = depth
        params = {'market': symbol,
                  'depth': depth}
        url = ROOT_URL + '/open/api/v1/data/depth'
        response = rq('GET', url, params=params, headers=headers)
        return response.json()

    def get_trade_history(self, symbol):
        """获取单个币种成交记录信息"""
        symbol = symbol
        params = {'market': symbol}
        url = ROOT_URL + '/open/api/v1/data/history'
        response = rq('GET', url, params=params, headers=headers)
        return response.json()

    def get_ticker(self, symbol):
        """获取市场行情信息"""
        symbol = symbol
        params = {'market': symbol}
        url = ROOT_URL + '/open/api/v1/data/ticker'
        response = rq('GET', url, params=params, headers=headers)
        return response.json()

    def get_kline(self, symbol, timeframe):
        """获取市场K线信息
        时间间隔(分钟制:1m，5m，15m，30m，60m。小时制:1h，天制:1d，月制:1M)
        """
        interval = 0
        symbol = symbol
        if "m" in timeframe:
            interval = get_cur_timestamp() - 60 * int(timeframe.split("m")[0]) * 300
        elif "h" in timeframe:
            interval = get_cur_timestamp() - 60 * int(timeframe.split("h")[0]) * 60 * 300
            print(interval)
        elif "d" in timeframe:
            interval = get_cur_timestamp() - 60 * int(timeframe.split("d")[0]) * 24 * 60 * 300
        params = {'market': symbol,
                  'interval': timeframe,
                  'startTime': interval,
                  'limit': 1000}
        url = ROOT_URL + '/open/api/v1/data/kline'
        response = rq('GET', url, params=params, headers=headers)
        return response.json()


    """
    私有
    """

    def sign(self, params):
        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) + '&'
        response_data = sign + 'api_secret=' + self.__secret_key
        return hashlib.md5(response_data.encode("utf8")).hexdigest()

    def get_account_info(self):
        """获取账户资产信息"""
        url = ROOT_URL + '/open/api/v1/private/account/info'
        params = {'api_key': self.__access_key,
                  'req_time': time.time()}
        params.update({'sign': self.sign(params)})
        response = rq('GET', url, params=params, headers=headers)
        return response.json()

    def get_current_orders(self, symbol):
        """获取当前委托信息"""
        symbol = symbol
        trade_type = 0
        params = {'api_key': self.__access_key,
                  'req_time': time.time(),
                  'market': symbol,
                  'trade_type': trade_type,  # 交易类型，0/1/2 (所有/买/卖)
                  'page_num': 1,
                  'page_size': 50}
        params.update({'sign': self.sign(params)})
        url = ROOT_URL + '/open/api/v1/private/current/orders'
        response = rq('GET', url, params=params, headers=headers)
        return response.json()

    def create_order(self, symbol, price, quantity, trade_type):
        """下单
        trade_type: 1是买   2是卖
        """
        symbol = symbol
        price = price
        quantity = quantity
        trade_type = trade_type  # 1/2 (买/卖)
        params = {'api_key': self.__access_key,
                  'req_time': time.time(),
                  'market': symbol,
                  'price': price,
                  'quantity': quantity,
                  'trade_type': trade_type}
        params.update({'sign': self.sign(params)})
        url = ROOT_URL + '/open/api/v1/private/order'
        response = rq('POST', url, params=params, headers=headers)
        return response.json()

    def create_multi_orders(self):
        """批量下单"""
        symbol = 'BTC_USDT'
        trade_type = 1  # 1/2 (买/卖)
        params = {'api_key': self.__access_key,
                  'req_time': time.time()}
        params.update({'sign': self.sign(params)})
        data = [
            {
                'market': symbol,
                'price': 10000,
                'quantity': 1,
                'type': trade_type,
            },
            {
                'market': symbol,
                'price': 9999,
                'quantity': 1,
                'type': trade_type,
            },
        ]
        url = ROOT_URL + '/open/api/v1/private/order_batch'
        response = rq('POST', url, params=params, json=data, headers=headers)
        return response.json()

    def cancel_order(self, symbol, order_id):
        """取消订单"""
        symbol = symbol
        order_id = order_id
        params = {'api_key': self.__access_key,
                  'req_time': time.time(),
                  'market': symbol,
                  'trade_no': order_id}
        params.update({'sign': self.sign(params)})
        url = ROOT_URL + '/open/api/v1/private/order'
        response = rq('DELETE', url, params=params, headers=headers)
        return response.json()

    def cancel_multi_orders(self):
        """批量取消订单"""
        symbol = 'BTC_USDT'
        order_id = ['3cd4bd41-****-****-****-d593f8eea202', '123ce00a-****-****-****-ed91337febb7']
        params = {'api_key': self.__access_key,
                  'req_time': time.time(),
                  'market': symbol,
                  'trade_no': ','.join(order_id)}
        params.update({'sign': self.sign(params)})
        url = ROOT_URL + '/open/api/v1/private/order_cancel'
        response = rq('POST', url, params=params, headers=headers)
        return response.json()

    def get_private_order_history(self, symbol, deal_type):
        """查询账号历史委托记录
        deal_type: 1买  2卖
        """
        symbol = symbol
        deal_type = deal_type
        params = {'api_key': self.__access_key,
                  'req_time': time.time(),
                  'market': symbol,
                  'trade_type': deal_type,
                  'page_num': 1,
                  'page_size': 70}
        params.update({'sign': self.sign(params)})
        url = ROOT_URL + '/open/api/v1/private/orders'
        response = rq('GET', url, params=params)
        return response.json()

    def get_order_info(self, symbol, order_id):
        """查询订单状态"""
        symbol = symbol
        trade_no = order_id
        params = {'api_key': self.__access_key,
                  'req_time': time.time(),
                  'market': symbol,
                  'trade_no': trade_no}
        params.update({'sign': self.sign(params)})
        url = ROOT_URL + '/open/api/v1/private/order'
        response = rq('GET', url, params=params)
        return response.json()


if __name__ == '__main__':
    exchange = Mxc("", "")
    info = (exchange.get_current_orders('BTC_USDT'))
    print(info)