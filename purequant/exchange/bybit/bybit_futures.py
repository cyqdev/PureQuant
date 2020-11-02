import requests
import urllib.parse
import hmac
import urllib
import time
from purequant.time import get_cur_timestamp, get_cur_timestamp_ms

TIMEOUT = 5


class BybitFutures:

    def __init__(self, access_key, secret_key, testing=False):

        self.__url = "https://api-testnet.bybit.com" if testing else "https://api.bybit.com"
        self.__access_key = access_key
        self.__secret_key = secret_key

    def http_get_request(self, url, params):
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        postdata = urllib.parse.urlencode(params)   # 将字典里面所有的键值转化为query-string格式（key=value&key=value），并且将中文转码
        try:
            response = requests.get(url+"?"+postdata, headers=headers, timeout=TIMEOUT)
            return response.json()
        except Exception as e:
            return {"status": "fail", "error_message": "%s" % e}

    def apikey_post(self, url, params):
        timestamp = self.get_server_time() * 1000
        params.update({"timestamp": timestamp, "api_key": self.__access_key})
        val = '&'.join([str(k) + "=" + str(v) for k, v in sorted(params.items()) if (k != 'sign') and (v is not None)])
        signature = str(hmac.new(bytes(self.__secret_key, "utf-8"), bytes(val, "utf-8"), digestmod="sha256").hexdigest())
        post_data = val + "&sign=" + signature
        try:
            response = requests.post(url + "?" + post_data, timeout=TIMEOUT)
            return response.json()
        except Exception as e:
            return {"status": "fail", "error_message": "%s" % e}

    def apikey_get(self, url, params):
        timestamp = self.get_server_time() * 1000
        params.update({"timestamp": timestamp, "api_key": self.__access_key})
        val = '&'.join([str(k) + "=" + str(v) for k, v in sorted(params.items()) if (k != 'sign') and (v is not None)])
        signature = str(
            hmac.new(bytes(self.__secret_key, "utf-8"), bytes(val, "utf-8"), digestmod="sha256").hexdigest())
        post_data = val + "&sign=" + signature
        try:
            response = requests.get(url + "?" + post_data, timeout=TIMEOUT)
            return response.json()
        except Exception as e:
            return {"status": "fail", "error_message": "%s" % e}


    """行情接口"""

    def get_orderbook(self, symbol):
        """
        获取Bybit当前Orderbook信息.
        :param symbol:  e.g. "BTCUSD"
        :return:
        """
        url = self.__url + "/v2/public/orderBook/L2"
        params = {
            "symbol": symbol
        }
        data = self.http_get_request(url, params)
        bids = []
        asks = []
        for item in data['result']:
            if item['side'] == "Buy":
                bids.append(float(item['price']))
            elif item['side'] == "Sell":
                asks.append(float(item['price']))
        return {"asks": asks, "bids": bids}

    def get_kline(self, symbol, interval):
        """
        查询K线数据
        :param symbol:"BTCUSD"
        :param interval:"1m" "3m" "1h" "12" "1d"
        :return:
        """
        m, t = "", 0
        if interval == "1m":
            m = "1"
            t = 1
        elif interval == "3m":
            m = "3"
            t = 3
        elif interval == "5m":
            m = "5"
            t = 5
        elif interval == "15m":
            m = "15"
            t = 15
        elif interval == "30m":
            m = "30"
            t = 30
        elif interval == "1h":
            m = "60"
            t = 60
        elif interval == "2h":
            m = "120"
            t = 120
        elif interval == "4h":
            m = "240"
            t = 240
        elif interval == "6h":
            m = "360"
            t = 360
        elif interval == "12h":
            m = "720"
            t = 720
        elif interval == "1d":
            m = "D"
            t = 1440
        params = {
            "symbol": symbol,
            "interval": m,
            "from": get_cur_timestamp() - 60 * 200 * t
        }
        url = self.__url + "/v2/public/kline/list"
        data = self.http_get_request(url, params)
        kline = []
        for item in data['result']:
            kline.append([float(item['open_time']), float(item['open']), float(item['high']), float(item['low']), float(item['close']), float(item['volume'])])
        kline.reverse()
        return kline

    def get_ticker(self, symbol):
        """获取Bybit的最新合约ticker信息"""
        url = self.__url + "/v2/public/tickers"
        params = {
            "symbol": symbol
        }
        data = self.http_get_request(url, params)
        return data

    def get_trading_records(self, symbol):
        """平台交易历史数据"""
        params = {
            "symbol": symbol
        }
        url = self.__url + "/v2/public/trading-records"
        data = self.http_get_request(url, params)
        return data

    def get_symbols(self):
        """查询合约信息"""
        url = self.__url + "/v2/public/symbols"
        params = {}
        data = self.http_get_request(url ,params)
        return data

    def get_liq_records(self, symbol):
        """查询强平订单数据，默认: 返回最新数据"""
        url = self.__url + "/v2/public/liq-records"
        params = {"symbol": symbol}
        data = self.http_get_request(url ,params)
        return data

    def get_mark_price_kline(self, symbol, interval):
        """
        查询标记价格K线
        :param symbol:"BTCUSD"
        :param interval:"1m" "3m" "1h" "12" "1d"
        :return:
        """
        m, t = "", 0
        if interval == "1m":
            m = "1"
            t = 1
        elif interval == "3m":
            m = "3"
            t = 3
        elif interval == "5m":
            m = "5"
            t = 5
        elif interval == "15m":
            m = "15"
            t = 15
        elif interval == "30m":
            m = "30"
            t = 30
        elif interval == "1h":
            m = "60"
            t = 60
        elif interval == "2h":
            m = "120"
            t = 120
        elif interval == "4h":
            m = "240"
            t = 240
        elif interval == "6h":
            m = "360"
            t = 360
        elif interval == "12h":
            m = "720"
            t = 720
        elif interval == "1d":
            m = "D"
            t = 1440
        params = {
            "symbol": symbol,
            "interval": m,
            "from": get_cur_timestamp() - 60 * 200 * t
        }
        url = self.__url + "/v2/public/kline/list"
        data = self.http_get_request(url, params)
        kline = []
        for item in data['result']:
            kline.append([float(item['open_time']), float(item['open']), float(item['high']), float(item['low']), float(item['close']), float(item['volume'])])
        kline.reverse()
        return kline

    """平台进阶数据"""

    def get_open_interest(self, symbol, period):
        """
        获取Bybit各个合约的持仓数量
        :param symbol:
        :param period:数据记录周期. 5min 15min 30min 1h 4h 1d
        :return:
        """
        url = self.__url + "/v2/public/open-interest"
        params = {
            "symbol": symbol,
            "period": period
        }
        data = self.http_get_request(url ,params)
        return data

    def get_big_deal(self, symbol):
        """
        获取Bybit主动成交大于500000USD的订单，时间范围是最近24h内。
        :param symbol:
        :return:
        """
        url = self.__url + "/v2/public/big-deal"
        params = {
            "symbol": symbol
        }
        data = self.http_get_request(url ,params)
        return data

    def get_public_account_ratio(self, symbol, period):
        """
        获取Bybit平台用户多空持仓比率
        :param symbol:
        :param period:数据记录周期. 5min 15min 30min 1h 4h 1d
        :return:
        """
        url = self.__url + "/v2/public/account-ratio"
        params = {
            "symbol": symbol,
            "period": period
        }
        data = self.http_get_request(url ,params)
        return data

    """账户/交易接口"""

    """活动单"""

    def create_order(self, symbol, side, price, qty, order_type, time_in_force, **kwargs):
        """
        创建活动委托单
        :param symbol:合约类型,e.g. "BTCUSD"
        :param side:方向  "Buy" "Sell"
        :param price:委托价格
        :param qty:委托数量(1个委托1美元)，只能为正整数
        :param order_type:委托单价格类型 "Limit" "Market"
        :param time_in_force:执行策略, "GoodTillCancel"
        :param kwargs:如需传入其他参数，可以take_profit=100
        :return:
        """
        url = self.__url + "/v2/private/order/create"
        params = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "qty": qty,
            "order_type": order_type,
            "time_in_force": time_in_force
        }
        params.update(kwargs)
        data = self.apikey_post(url, params)
        return data

    def get_open_orders(self, symbol, order_id, **kwargs):
        """获取我的活动委托单列表"""
        url = self.__url + "/open-api/order/list"
        params = {
            "symbol": symbol,
            "order_id": order_id
        }
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data

    def cancel_order(self, symbol, order_id):
        """撤销活动委托单"""
        url = self.__url + "/v2/private/order/cancel"
        params = {
            "symbol": symbol,
            "order_id": order_id
        }
        data = self.apikey_post(url, params)
        return data

    def cancel_all_order(self, symbol):
        """撤销所有活动委托单"""
        url = self.__url + "/v2/private/order/cancelAll"
        params = {
            "symbol": symbol
        }
        data = self.apikey_post(url, params)
        return data

    def amend_order(self, symbol, order_id):
        """修改活动单信息"""
        url = self.__url + "/open-api/order/replace"
        params = {
            "symbol": symbol,
            "order_id": order_id
        }
        data = self.apikey_post(url, params)
        return data

    def get_realtime_order(self, symbol, order_id):
        """实时查询活动委托"""
        url = self.__url + "/v2/private/order"
        params = {
            "symbol": symbol,
            "order_id": order_id
        }
        data = self.apikey_get(url, params)
        return data

    """条件单"""
    def create_stop_order(self, **kwargs):
        """创建条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/open-api/stop-order/create"
        data = self.apikey_post(url, params)
        return data

    def get_stop_order(self, **kwargs):
        """查询条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/open-api/stop-order/list"
        data = self.apikey_get(url, params)
        return data

    def cancel_stop_order(self, **kwargs):
        """撤销条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/open-api/stop-order/cancel"
        data = self.apikey_post(url, params)
        return data

    def cancel_all_stop_order(self, **kwargs):
        """撤销全部条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/v2/private/stop-order/cancelAll"
        data = self.apikey_post(url, params)
        return data

    def amend_stop_order(self, **kwargs):
        """修改条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/open-api/stop-order/replace"
        data = self.apikey_post(url, params)
        return data

    def get_realtime_stop_order(self, **kwargs):
        """实时查询条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/v2/private/stop-order"
        data = self.apikey_get(url, params)
        return data

    """持仓"""

    def get_position(self, symbol):
        """获取持仓（实时）"""
        url = self.__url + "/v2/private/position/list"
        params = {
            "symbol": symbol
        }
        data = self.apikey_get(url, params)
        return data

    def change_position_margin(self, symbol, margin):
        """更新保证金"""
        url = self.__url + "/position/change-position-margin"
        params = {
            "symbol": symbol,
            "margin": margin
        }
        data = self.apikey_post(url, params)
        return data

    def set_trading_stop(self, symbol, **kwargs):
        """设置止盈止损"""
        url = self.__url + "/open-api/position/trading-stop"
        params = {
            "symbol": symbol
        }
        params.update(kwargs)
        data = self.apikey_post(url, params)
        return data

    def get_leverage(self):
        """获取用户杠杆。"""
        url = self.__url + "/user/leverage"
        params = {}
        data = self.apikey_get(url, params)
        return data

    def set_leverage(self, symbol, leverage):
        """修改杠杆"""
        url = self.__url + "/user/leverage/save"
        params = {
            "symbol": symbol,
            "leverage": leverage
        }
        data = self.apikey_post(url, params)
        return data

    def get_private_trade_history(self, symbol, **kwargs):
        """获取用户成交记录"""
        url = self.__url + "/v2/private/execution/list"
        params = {
            "symbol": symbol
        }
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data

    def get_closed_pnl(self, symbol, **kwargs):
        """获取用户平仓记录，按时间降序排列。"""
        url = self.__url + "/v2/private/trade/closed-pnl/list"
        params = {
            "symbol": symbol
        }
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data

    """风险限额"""
    def get_risk_limit(self):
        """查询风险限额表。"""
        url = self.__url + "/open-api/wallet/risk-limit/list"
        params = {}
        data = self.apikey_get(url, params)
        return data

    def set_risk_limit(self, symbol, risk_id):
        """设置风险限额  risk_id	true	integer	风险限额ID."""
        url = self.__url + "/open-api/wallet/risk-limit"
        params = {
            "symbol": symbol,
            "risk_id": risk_id
        }
        data = self.apikey_post(url, params)
        return data

    """资金费率"""
    def get_prev_funding_rate(self, symbol):
        """查询上个周期的资金费率"""
        url = self.__url + "/open-api/funding/prev-funding-rate"
        params = {
            "symbol": symbol
        }
        data = self.apikey_get(url, params)
        return data

    def get_prev_funding(self, symbol):
        """查询上个周期资金费用结算信息"""
        url = self.__url + "/open-api/funding/prev-funding"
        params = {
            "symbol": symbol
        }
        data = self.apikey_get(url, params)
        return data

    def get_predicted_funding(self, symbol):
        """查询预测资金费率和资金费用"""
        url = self.__url + "/open-api/funding/predicted-funding"
        params = {
            "symbol": symbol
        }
        data = self.apikey_get(url, params)
        return data

    def get_apikey(self):
        """获取账户API密钥信息。"""
        url = self.__url + "/open-api/api-key"
        params = {}
        data = self.apikey_get(url, params)
        return data

    def get_lcp(self, symbol):
        """查询用户流动性贡献分(当天数据每小时更新一次), 目前只支持反向合约"""
        url = self.__url + "/v2/private/account/lcp"
        params = {
            "symbol": symbol
        }
        data = self.apikey_get(url, params)
        return data

    """钱包接口"""
    def get_wallet_balance(self, coin):
        """获取钱包余额"""
        url = self.__url + "/v2/private/wallet/balance"
        params = {
            "coin": coin
        }
        data = self.apikey_get(url, params)
        return data

    def get_fund_records(self, **kwargs):
        """资金记录"""
        url = self.__url + "/open-api/wallet/fund/records"
        params = {}
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data

    def get_withdraw_list(self, **kwargs):
        """查询提币记录"""
        url = self.__url + "/open-api/wallet/withdraw/list"
        params = {}
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data

    def get_exchange_order_list(self, **kwargs):
        """资产兑换记录"""
        url = self.__url + "/v2/private/exchange-order/list"
        params = {}
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data


    """通用接口"""

    def get_server_time(self):
        """获取交易所服务器时间"""
        url = self.__url + "/v2/public/time"
        params = {}
        data = round(float(self.http_get_request(url, params)['time_now']))
        return data

    def get_announcement(self):
        """获取Bybit最近30天OpenAPI公告（时间倒叙排列）"""
        url = self.__url + "/v2/public/announcement"
        params = {}
        data = self.http_get_request(url, params)
        return data


if __name__ == '__main__':
    exchange = BybitFutures("", "", testing=True)
    # data = exchange.create_order("BTCUSD", "Buy", 13600, 1, "Limit", "GoodTillCancel")
    data = exchange.get_ticker("BTCUSD")
    # data = exchange.get_kline("BTCUSD", "1m")
    # data = exchange.get_position("BTCUSD")
    print(data)