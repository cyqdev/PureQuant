import requests
import urllib.parse
import hmac
import urllib
import time
from purequant.time import get_cur_timestamp, get_cur_timestamp_ms

TIMEOUT = 5

class BybitSwap:

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
        :param symbol:  e.g. "BTCUSDT"
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
        :param symbol:"BTCUSDT"
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
        url = self.__url + "/public/linear/kline"
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
        url = self.__url + "/public/linear/recent-trading-records"
        data = self.http_get_request(url, params)
        return data

    def get_symbols(self):
        """查询合约信息"""
        url = self.__url + "/v2/public/symbols"
        params = {}
        data = self.http_get_request(url, params)
        return data

    def get_liq_records(self, symbol):
        """查询强平订单数据，默认: 返回最新数据"""
        url = self.__url + "/v2/public/liq-records"
        params = {"symbol": symbol}
        data = self.http_get_request(url, params)
        return data

    def get_mark_price_kline(self, symbol, interval):
        """
        查询标记价格K线
        :param symbol:"BTCUSDT"
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
        url = self.__url + "/public/linear/mark-price-kline"
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
        data = self.http_get_request(url, params)
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
        data = self.http_get_request(url, params)
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
        data = self.http_get_request(url, params)
        return data

    """账户/交易接口"""

    """活动单"""

    def create_order(self, symbol, side, price, qty, order_type, time_in_force, reduce_only, close_on_trigger, **kwargs):
        """
        创建活动委托单
        :param symbol:合约类型, e.g. "BTCUSDT"
        :param side:方向
        :param price:委托价格。如果是下限价单，该参数为必填. 在没有仓位时，做多的委托价格需高于市价的10%、低于1百万。如有仓位时则需优于强平价。价格增减最小单位请参考交易对接口响应中的price_filter字段
        :param qty:委托数量(BTC)
        :param order_type:委托单价格类型
        :param time_in_force:执行策略
        :param reduce_only:bool 是否平仓单,true-平仓 false-开仓,ture时止盈止损设置不生效
        :param close_on_trigger:bool 平仓委托,只会减少您的仓位而不会增加您的仓位。如果当平仓委托被触发时，账户上的余额不足，那么该合约的其他委托将被取消或者降低委托数量。使用此选项可以确保您的止损单被用于减仓而非加仓。
        :param kwargs:
        :return:
        """
        url = self.__url + "/private/linear/order/create"
        params = {
            "symbol": symbol,
            "side": side,
            "price": price,
            "qty": qty,
            "order_type": order_type,
            "time_in_force": time_in_force,
            "reduce_only": reduce_only,
            "close_on_trigger": close_on_trigger
        }
        params.update(kwargs)
        data = self.apikey_post(url, params)
        return data

    def get_open_orders(self, symbol, order_id, **kwargs):
        """获取我的活动委托单列表"""
        url = self.__url + "/private/linear/order/list"
        params = {
            "symbol": symbol,
            "order_id": order_id
        }
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data

    def cancel_order(self, symbol, order_id):
        """撤销活动委托单"""
        url = self.__url + "/private/linear/order/cancel"
        params = {
            "symbol": symbol,
            "order_id": order_id
        }
        data = self.apikey_post(url, params)
        return data

    def cancel_all_order(self, symbol):
        """撤销所有活动委托单"""
        url = self.__url + "/private/linear/order/cancel-all"
        params = {
            "symbol": symbol
        }
        data = self.apikey_post(url, params)
        return data

    def amend_order(self, symbol, order_id):
        """修改活动单信息"""
        url = self.__url + "/private/linear/order/replace"
        params = {
            "symbol": symbol,
            "order_id": order_id
        }
        data = self.apikey_post(url, params)
        return data

    def get_realtime_order(self, symbol, order_id):
        """实时查询活动委托"""
        url = self.__url + "/private/linear/order/search"
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
        url = self.__url + "/private/linear/stop-order/create"
        data = self.apikey_post(url, params)
        return data

    def get_stop_order(self, **kwargs):
        """查询条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/private/linear/stop-order/list"
        data = self.apikey_get(url, params)
        return data

    def cancel_stop_order(self, **kwargs):
        """撤销条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/private/linear/stop-order/cancel"
        data = self.apikey_post(url, params)
        return data

    def cancel_all_stop_order(self, **kwargs):
        """撤销全部条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/private/linear/stop-order/cancel-all"
        data = self.apikey_post(url, params)
        return data

    def amend_stop_order(self, **kwargs):
        """修改条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/private/linear/stop-order/replace"
        data = self.apikey_post(url, params)
        return data

    def get_realtime_stop_order(self, **kwargs):
        """实时查询条件委托单"""
        params = {}
        params.update(kwargs)
        url = self.__url + "/private/linear/stop-order/search"
        data = self.apikey_get(url, params)
        return data

    """持仓"""

    def get_position(self, symbol):
        """获取持仓（实时）"""
        url = self.__url + "/private/linear/position/list"
        params = {
            "symbol": symbol
        }
        data = self.apikey_get(url, params)
        return data

    def auto_add_margin(self, symbol, margin):
        """自动追加保证金"""
        url = self.__url + "/private/linear/position/set-auto-add-margin"
        params = {
            "symbol": symbol,
            "margin": margin
        }
        data = self.apikey_post(url, params)
        return data

    def switch_isolated(self, symbol, is_isolated, buy_leverage, sell_leverage):
        """
        全仓/逐仓切换，从全仓切换至逐仓时需要传杠杆
        :param symbol:合约类型
        :param is_isolated:全仓/逐仓, true是逐仓，false是全仓
        :param buy_leverage:杠杆大于0，小于风险限额对应的杠杆
        :param sell_leverage:杠杆大于0，小于风险限额对应的杠杆
        :return:
        """
        url = self.__url + "/private/linear/position/switch-isolated"
        params = {
            "symbol": symbol,
            "is_isolated": is_isolated,
            "buy_leverage": buy_leverage,
            "sell_leverage": sell_leverage
        }
        data = self.apikey_post(url, params)
        return data

    def switch_mode(self, symbol, tp_sl_mode):
        """
        切换止盈止损模式至全仓或部分
        :param symbol:
        :param tp_sl_mode:止盈止损模式
        :return:
        """
        url = self.__url + "/private/linear/tpsl/switch-mode"
        params = {
            "symbol": symbol,
            "tp_sl_mode": tp_sl_mode
        }
        data = self.apikey_post(url, params)
        return data

    def add_or_reduce_margin(self, symbol, side, margin):
        """
        增加/减少保证金
        :param symbol:
        :param side:方向
        :param margin:增加/减少多少保证金,增加10，减少-10，支持小数后4位
        :return:
        """
        url = self.__url + "/private/linear/position/add-margin"
        params = {
            "symbol": symbol,
            "side": side,
            "margin": margin
        }
        data = self.apikey_post(url, params)
        return data

    def set_leverage(self, symbol, buy_leverage, sell_leverage):
        """修改杠杆"""
        url = self.__url + "/private/linear/position/set-leverage"
        params = {
            "symbol": symbol,
            "buy_leverage": buy_leverage,
            "sell_leverage": sell_leverage
        }
        data = self.apikey_post(url, params)
        return data

    def set_trading_stop(self, symbol, side, **kwargs):
        """
        设置止盈止损
        :param symbol:
        :param side:方向
        :param tp_trigger_by:
        :param sl_trigger_by:
        :return:
        """
        url = self.__url + "/private/linear/position/trading-stop"
        params = {
            "symbol": symbol,
            "side": side
        }
        params.update(kwargs)
        data = self.apikey_post(url, params)
        return data

    def get_private_trade_history(self, symbol, **kwargs):
        """获取用户成交记录"""
        url = self.__url + "/private/linear/trade/execution/list"
        params = {
            "symbol": symbol
        }
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data

    def get_closed_pnl(self, symbol, **kwargs):
        """获取用户平仓记录，按时间降序排列。"""
        url = self.__url + "/private/linear/trade/closed-pnl/list"
        params = {
            "symbol": symbol
        }
        params.update(kwargs)
        data = self.apikey_get(url, params)
        return data

    """风险限额"""
    def get_risk_limit(self, symbol):
        """查询风险限额表。"""
        url = self.__url + "/public/linear/risk-limit"
        params = {"symbol": symbol}
        data = self.apikey_get(url, params)
        return data


    """资金费率"""
    def get_prev_funding_rate(self, symbol):
        """查询上个周期的资金费率"""
        url = self.__url + "/public/linear/funding/prev-funding-rate"
        params = {
            "symbol": symbol
        }
        data = self.apikey_get(url, params)
        return data

    def get_prev_funding(self, symbol):
        """查询上个周期资金费用结算信息"""
        url = self.__url + "/private/linear/funding/prev-funding"
        params = {
            "symbol": symbol
        }
        data = self.apikey_get(url, params)
        return data

    def get_predicted_funding(self, symbol):
        """查询预测资金费率和资金费用"""
        url = self.__url + "/private/linear/funding/predicted-funding"
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
    exchange = BybitSwap("", "", testing=True)
    # data = exchange.get_orderbook("BTCUSDT")
    # data = exchange.create_order("BTCUSDT", "Buy", 13600, 200, "Limit", "GoodTillCancel", False, False)
    data = exchange.get_ticker("BTCUSDT")
    # data = exchange.get_position("BTCUSD")
    # data = exchange.cancel_order("BTCUSDT", order_id="1c7e1242-7cdc-40f6-835e-171c9675fb62")
    # data = exchange.get_realtime_order("BTCUSDT", order_id="1c7e1242-7cdc-40f6-835e-171c9675fb62")
    print(data)