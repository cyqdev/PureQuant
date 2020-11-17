"""
混合合约：

BTCUSD、ETHUSD、EOSUSD、LTCUSD、BCHUSD、TRXUSD、LINKUSD、DOTUSD、XTZUSD、COMPUSD、BANDUSD、YFIUSD、CRVUSD、UNIUSD：Maker(挂单)：0.02% Taker(吃单)：0.04%

目前暂不收取对于混合合约的换币手续。

例如：您使用BTC交易EOSUSD合约，在盈亏结算时，对于我们的系统，需要做相关换币工作，不同资产间的兑换都是需要支付兑换费用，但是我们目前不收取费用。如有收费变动，我们会提前通过交易所各个官方渠道通知。
"""
import requests
import urllib.parse
import hashlib
import urllib
from purequant.time import get_cur_timestamp

TIMEOUT = 5


class BitCoke:

    def __init__(self, access_key, secret_key):
        self.__url = "https://api.bitcoke.com"
        self.__trade_url = "https://api.bitcoke.com/trade"
        self.__access_key = access_key
        self.__secret_key = secret_key

    def http_get_request(self, url, params, add_to_headers=None):
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = urllib.parse.urlencode(params)   # 将字典里面所有的键值转化为query-string格式（key=value&key=value），并且将中文转码
        try:
            response = requests.get(url+"?"+postdata, headers=headers, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "fail"}
        except Exception as e:
            return {"status": "fail", "error_message": "%s" % e}

    def http_post_request(self, url, params, add_to_headers=None):
        headers = {
            "Accept": "application/json",
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        if add_to_headers:
            headers.update(add_to_headers)
        postdata = urllib.parse.urlencode(params)
        try:
            response = requests.post(url+"?"+postdata, headers=headers, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()
            else:
                return response.json()
        except Exception as e:
            return {"status": "fail", "msg": "%s" % e}

    def api_key_get(self, request_path, params):
        timestamp = str(get_cur_timestamp() + 1000)
        data = "{}{}{}{}".format(self.__secret_key, "GET", request_path, timestamp)
        add_to_headers = {
            "apiKey": self.__access_key,
            "expires": timestamp,
            "signature": hashlib.sha256(data.encode('utf-8')).hexdigest()
        }
        return self.http_get_request(self.__trade_url + request_path, params, add_to_headers)


    def api_key_post(self, request_path, params):
        timestamp = str(get_cur_timestamp() + 1000)
        data = "{}{}{}{}".format(self.__secret_key, "POST", request_path, timestamp)
        add_to_headers = {
            "apiKey": self.__access_key,
            "expires": timestamp,
            "signature": hashlib.sha256(data.encode('utf-8')).hexdigest()
        }
        return self.http_post_request(self.__trade_url + request_path, params, add_to_headers)


    '''
    ======================
    Market data API
    ======================
    '''

    def get_contract_info(self):
        """
        获取合约信息
        请求频率限定：1次/秒/IP。
        响应结果如下，symbol 为合约名；tick 为价格最小变动单位；lotSize 为合约面值，单位 USD；type 为合约类型，PERP为永续合约。
        """
        url = self.__url + "/api/basic/refData"
        params = {}
        return self.http_get_request(url, params)

    def get_last_price(self, symbol):
        """
        获取合约最新成交价
        请求频率限定：1次/秒/IP。
        :param symbol:合约名称，eg: "XBTCUSD"
        :return:
        """
        url = self.__url + "/api/basic/lastPrice"
        params = {"symbols": symbol}
        return self.http_get_request(url, params)

    def get_index_price(self, symbol):
        """
        获取标记价
        :param symbol:合约名称,eg: "XBTCUSD"
        :return:
        """
        url = self.__url + "/api/index/price"
        params = {"symbols": symbol.replace("X", "")}
        return self.http_get_request(url, params)

    def get_market_depth(self, symbol):
        """
        获取市场深度
        请求频次限定：5次/秒/IP。
        :param symbol:合约名称,eg: "XBTCUSD"
        :return:响应结果：20档深度
        """
        url = self.__url + "/api/depth/depth"
        params = {"symbol": symbol}
        return self.http_get_request(url, params)

    def get_trade_records(self, symbol):
        """
        获取最新成交记录
        请求频次限定：5次/秒/IP。
        :param symbol:合约名称,eg: "XBTCUSD"
        :return:响应结果：返回最近50笔成交
        """
        url = self.__url + "/api/depth/trades"
        params = {"symbol": symbol}
        return self.http_get_request(url, params)

    def get_kline(self, symbol, timeframe):
        """
        获取k线
        请求频次限定：15次/分/IP
        :param symbol: eg: XBTCUSD
        :param timeframe:大小写均可，1M, 3M, 5M, 10M, 15M, 30M, 1H, 2H, 4H, 6H, 8H, 12H, D, W, MTH
        :return:
        """
        url = self.__url + "/api/kLine/byTime"
        if timeframe == "1d" or timeframe == "1D":
            timeframe = "D"
        params = {"symbol": symbol, "step": 500, "type": timeframe.upper()}
        return self.http_get_request(url, params)

    def get_latest_kline(self, symbol, timeframe):
        """
        获取最新一根k线数据
        请求频次限定：75次/分/IP
        :param symbol: eg: XBTCUSD
        :param timeframe:大小写均可，1M, 3M, 5M, 10M, 15M, 30M, 1H, 2H, 4H, 6H, 8H, 12H, D, W, MTH
        :return:
        """
        url = self.__url + "/api/kLine/latest"
        params = {"symbol": symbol, "type": timeframe.upper()}
        return self.http_get_request(url, params)

    def get_latest_period(self, symbol, timeframe):
        """
        获取上次拉取 K 线后的更新数据
        请求频次限定：75次/分/IP
        :param symbol: eg: XBTCUSD
        :param timeframe:大小写均可，1M, 3M, 5M, 10M, 15M, 30M, 1H, 2H, 4H, 6H, 8H, 12H, D, W, MTH
        :return:
        """
        url = self.__url + "/api/kLine/latest"
        params = {"symbol": symbol, "type": timeframe.upper()}
        return self.http_get_request(url, params)

    def get_funding_rate(self, symbol):
        """
        获取资金费率。
        请求频次限定：5次/秒/IP。
        :param symbol:eg: XBTCUSD
        :return:
        """
        url = self.__url + "/api/kLine/fundingRate"
        params = {"symbols": symbol}
        return self.http_get_request(url, params)

    def get_trade_statistics(self, symbol):
        """
        获取最近24小时的成交统计数据
        请求频次限定：5次/秒/IP。
        :param symbol:eg: XBTCUSD
        :return:
        """
        url = self.__url + "/api/kLine/tradeStatistics"
        params = {"symbols": symbol}
        return self.http_get_request(url, params)

    def get_open_interest(self, symbol):
        """
        获取系统合约持仓量
        请求频次限定：5次/秒/IP。
        :param symbol:eg: "XBTCUSD"
        :return:
        """
        url = self.__url + "/api/kLine/openInterest"
        params = {"symbol": symbol.replace("X", "")}
        return self.http_get_request(url, params)

    '''
    ======================
    Account API
    ======================
    '''

    def get_account_info(self):
        """
        查询用户的交易账号信息
        请求频率限制：60次/分/Key
        :return:
        """
        params = {}
        request_path = "/api/trade/queryAccounts"
        return self.api_key_get(request_path, params)

    def get_open_orders(self, symbol):
        """
        查询用户尚未完成的订单列表（包括委托单和条件单）
        请求频率限制：60次/分/Key
        :param symbol: 例如："XBTCUSD"
        :return:
        """
        params = {"symbol": symbol}
        request_path = "/api/trade/queryActiveOrders"
        return self.api_key_get(request_path, params)

    def get_history_orders(self):
        """
        查询用户订单历史，订单按时间倒叙排列。
        请求频率限制：30次/分/Key
        :return:
        """
        params = {}
        request_path = "/api/trade/queryOrders"
        return self.api_key_get(request_path, params)

    def get_order_info(self, order_id):
        """
        根据订单 Id 查询订单。 请求频率限制：5次/秒/Key。
        :param order_id:
        :return:
        """
        params = {"orderId": order_id}
        request_path = "/api/trade/queryOrderById"
        return self.api_key_get(request_path, params)

    def get_position(self):
        """
        查询用户的当前持仓。请求频率限制：60次/分/Key。
        :return:
        """
        params = {}
        request_path = "/api/trade/queryPosition"
        return self.api_key_get(request_path, params)

    def get_ledger(self, currency):
        """
        按币种分页查询用户交易账号的账本记录，首次通过分页获取所有记录，后续则通过传入最新记录ID获取增量记录。 GET请求。 请求频率限制：10次/分/Key。
        :param currency: 币种；eg: BTC、EOS等,大小写均可
        :return:
        """
        params = {"currency": currency.upper()}
        request_path = "/api/trade/ledger"
        return self.api_key_get(request_path, params)

    def get_wallet_list(self):
        """
        获取用户的钱包账号列表。 GET请求。 请求频率限制：10次/分/Key。
        :return:
        """
        params = {}
        request_path = "/api/wallet/list"
        return self.api_key_get(request_path, params)

    def get_deposit_address(self):
        """
        获取用户的钱包地址列表。 GET请求。 请求频率限制：10次/分/Key。
        :return:
        """
        params = {}
        request_path = "/api/wallet/depositAddress"
        return self.api_key_get(request_path, params)

    def get_wallet_ledger(self, currency):
        """
        按币种分页查询用户钱包账号的账本记录，首次通过分页获取所有记录，后续则通过传入最新记录ID获取增量记录。GET请求。 请求频率限制：10次/分/Key。
        :param currency:币种，eg: BTC、EOS等；大小写均可
        :return:
        """
        params = {"currency": currency.upper()}
        request_path = "/api/trade/ledger"
        return self.api_key_get(request_path, params)

    '''
    ======================
    Trade API
    ======================
    '''

    def create_order(self, currency, open_position, order_type, qty, side, symbol, price=None,
                     stopLossPrice=None, trailingStop=None, stopWinPrice=None, stopWinType=None,
                     triggerPrice=None, triggerType=None, tif=None):
        """
        下单接口，通过不同参数的组合，支持下普通单、条件单、高级单以及平仓单。POST请求。接口请求频率设在10次/秒/Key。
        :param currency:账号币种
        :param open_position:开、平仓单	true 为开仓，false 为平仓
        :param order_type:订单类型	Limit 为限价单；Market 为市价单
        :param price:订单价格	市价单价格可以为 null
        :param qty:订单数量	正整数
        :param side:订单方向	Buy 买入，Sell 卖出
        :param symbol:合约名称	XBTCUSD，XEOSUSD，XBCHUSD 等
        :param stopLossPrice:止损价格	不能和追踪止损（trailingStop）同时设置
        :param trailingStop:追踪止损	不能和止损价格（stopLossPrice）同时设置
        :param stopWinPrice:止盈价格
        :param stopWinType:止盈类型	Limit为限价止盈，Market为市价止盈
        :param triggerPrice:条件单触发价
        :param triggerType:条件单触发价类型	LAST 为最后成交价触发，INDEX 为标记价触发
        :param tif:订单生效设定	GOOD_TILL_CANCEL: 一直有效至消失；IMMEDIATE_OR_CANCEL: 立即成交或取消；FILL_OR_KILL:完全成交或取消；QUEUE_OR_CANCEL: 被动委托
        :return:
        """
        params = {
            "currency": currency.upper(),
            "openPosition": open_position,
            "orderType": order_type,
            "qty": qty,
            "side": side,
            "symbol": symbol
        }
        if price:
            params.update({"price": price})
        if stopLossPrice:
            params.update({"stopLossPrice": stopLossPrice})
        if trailingStop:
            params.update({"trailingStop": trailingStop})
        if stopWinPrice:
            params.update({"stopWinPrice": stopWinPrice})
        if stopWinType:
            params.update({"stopWinType": stopWinType})
        if triggerPrice:
            params.update({"triggerPrice": triggerPrice})
        if triggerType:
            params.update({"triggerType": triggerType})
        if tif:
            params.update({"tif": tif})
        request_path = "/api/trade/enterOrder"
        return self.api_key_post(request_path, params)

    def cancel_order(self, order_id):
        """
        根据订单Id进行撤单。POST请求。接口请求频率设在20次/秒/Key。
        :param order_id:订单 Id
        :return:
        """
        params = {"orderId": order_id}
        request_path = '/api/trade/cancelOrder'
        return self.api_key_post(request_path, params)

    def amend_order(self, orderId, price, qty, stopLossPrice=None, trailingStop=None, stopWinPrice=None, stopWinType=None, triggerPrice=None):
        """
        修改订单信息。POST请求。接口请求频率设在5次/秒/Key
        :param orderId:订单 Id
        :param price:订单价格,订单价格修改成功后，系统可能会生产一条新的订单
        :param qty:订单数量,订单数量增加修改成功后，系统可能会生产一条新的订单
        :param stopLossPrice:止损价格,不能和追踪止损（trailingStop）同时设置
        :param trailingStop:追踪止损，不能和止损价格（stopLossPrice）同时设置
        :param stopWinPrice:止盈价格
        :param stopWinType:止盈类型	Limit为限价止盈，Market为市价止盈
        :param triggerPrice:条件单触发价
        :return:
        """
        params = {
            "orderId": orderId,
            "price": price,
            "qty": qty
        }
        if stopLossPrice:
            params.update({"stopLossPrice": stopLossPrice})
        if trailingStop:
            params.update({"trailingStop": trailingStop})
        if stopWinPrice:
            params.update({"stopWinPrice": stopWinPrice})
        if stopWinType:
            params.update({"stopWinType": stopWinType})
        if triggerPrice:
            params.update({"triggerPrice": triggerPrice})
        request_path = '/api/trade/amendOrder'
        return self.api_key_post(request_path, params)

    def market_close_position(self, currency, side, symbol):
        """
        市价全部平仓。POST请求。接口请求频率设在4次/秒/Key。
        :param currency:账号币种
        :param side:合约名称	XBTCUSD，XEOSUSD，XBCHUSD 等
        :param symbol:所平仓位的方向	Long 为多仓，Short 为空仓
        :return:
        """
        params = {
            "currency": currency,
            "side": side,
            "symbol": symbol
        }
        request_path = '/api/trade/closePosition'
        return self.api_key_post(request_path, params)

    def change_pos_leverage(self, currency, symbol, leverage):
        """
        修改仓位杠杆设定。POST请求。接口请求频率设在4次/秒/Key。
        :param currency:账号币种
        :param symbol:合约名称	XBTCUSD，XEOSUSD，XBCHUSD 等
        :param leverage:仓位杠杆
        :return:
        """
        params = {
            "currency": currency,
            "symbol": symbol,
            "leverage": leverage
        }
        request_path = '/api/trade/changePosLeverage'
        return self.api_key_post(request_path, params)

    def risk_setting(self, currency, side, symbol, stopLossPrice=None, trailingStop=None, stopWinPrice=None, stopWinType=None):
        """
        修改仓位风控设定。POST请求。接口请求频率设在5次/秒/Key。
        :param currency:账号币种
        :param side:仓位方向	Long为多仓，Short为空仓
        :param symbol:合约名称	XBTCUSD，XEOSUSD，XBCHUSD 等
        :param stopLossPrice:止损价格	不能和追踪止损（trailingStop）同时设置
        :param trailingStop:追踪止损	不能和止损价格（stopLossPrice）同时设置
        :param stopWinPrice:止盈价格
        :param stopWinType:止盈类型	Limit为限价止盈，Market为市价止盈
        :return:
        """
        params = {
            "currency": currency,
            "side": side,
            "symbol": symbol
        }
        if stopLossPrice:
            params.update({"stopLossPrice": stopLossPrice})
        if trailingStop:
            params.update({"trailingStop": trailingStop})
        if stopWinPrice:
            params.update({"stopWinPrice": stopWinPrice})
        if stopWinType:
            params.update({"stopWinType": stopWinType})
        request_path = '/api/trade/riskSetting'
        return self.api_key_post(request_path, params)

    def switch_pos_side(self, currency, twoSidePosition):
        """
        切换账号单双向持仓模式。POST请求。接口请求频率设在4次/秒/Key。
        :param currency:账号币种
        :param twoSidePosition:切换为双向持仓	true 为双向持仓；false 为单向持仓
        :return:
        """
        params = {
            "currency": currency,
            "twoSidePosition": twoSidePosition
        }
        request_path = '/api/trade/switchPosSide'
        return self.api_key_post(request_path, params)

    def switch_to_cross(self, currency):
        """
        将账号从逐仓模式切换为全仓模式。POST请求。接口请求频率设在4次/秒/Key。
        :param currency:账号币种
        :return:
        """
        params = {
            "currency": currency
        }
        request_path = '/api/trade/switchToCross'
        return self.api_key_post(request_path, params)


if __name__ == '__main__':

    exchange = BitCoke("", "")
    info = exchange.create_order("eos", False, "Market", 20, "Buy", "XEOSUSD")
    res = exchange.cancel_order("O101-20201026-234257-642-1839")
    print(res)
    print(info)