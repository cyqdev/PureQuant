from purequant.exchange.bitmex.bitmex_websocket import BitMEXWebsocket
from purequant.exchange.bitmex.bitmex import Bitmex
from purequant.exceptions import *
import uuid


class BITMEXWS:

    def __init__(self, access_key, secret_key, instrument_id, leverage=None, testing=False):
        """
        api_key: api key
        api_secret: api secret
        symbol: symbol  例如："XBTUSD"
        leverage: 杠杆倍数，不填则设置为20倍
        testing: 默认为真实账户，如果是模拟交易请设置为True
        """
        endpoint = "https://testnet.bitmex.com/api/v1" if testing else "https://www.bitmex.com/api/v1"
        self.__ws = BitMEXWebsocket(endpoint=endpoint, symbol=instrument_id, api_key=access_key, api_secret=secret_key)
        self.__bitmex = Bitmex(api_key=access_key, api_secret=secret_key, testing=testing)
        self.__bitmex.set_leverage(instrument_id, leverage=leverage or 20)
        self.__instrument_id = instrument_id

    def generate_uuid(self):
        """生成client order id"""
        return str(uuid.uuid4())

    def revoke_order(self, clOrdID):
        """撤单"""
        receipt = self.__bitmex.cancel_order(clOrdID=clOrdID)
        return receipt

    def buy(self, price, size, order_type=None, timeInForce=None, clOrdID=None):
        """
        买入开多
        :param price: 价格
        :param size: 数量
        :param order_type: Market, Limit, Stop, StopLimit, MarketIfTouched, LimitIfTouched, Pegged，默认是"Limit"
        :param timeInForce:Day, GoodTillCancel, ImmediateOrCancel, FillOrKill, 默认是"GoodTillCancel"
        :return:
        """
        order_type = order_type or "Limit"
        timeInForce = timeInForce or "GoodTillCancel"
        result = self.__bitmex.create_order(symbol=self.__instrument_id, side="Buy", price=price, orderQty=size,
                                            ordType=order_type, timeInForce=timeInForce, clOrdID=clOrdID)
        try:
            raise SendOrderError(msg=result['error']['message'])
        except:
            return result

    def sell(self, price, size, order_type=None, timeInForce=None, clOrdID=None):
        order_type = order_type or "Limit"
        timeInForce = timeInForce or "GoodTillCancel"
        result = self.__bitmex.create_order(symbol=self.__instrument_id, side="Sell", price=price, orderQty=size,
                                            ordType=order_type, timeInForce=timeInForce, clOrdID=clOrdID)
        try:
            raise SendOrderError(msg=result['error']['message'])
        except:
            return result

    def sellshort(self, price, size, order_type=None, timeInForce=None, clOrdID=None):
        order_type = order_type or "Limit"
        timeInForce = timeInForce or "GoodTillCancel"
        result = self.__bitmex.create_order(symbol=self.__instrument_id, side="Sell", price=price, orderQty=size,
                                            ordType=order_type, timeInForce=timeInForce, clOrdID=clOrdID)
        try:
            raise SendOrderError(msg=result['error']['message'])
        except:
            return result

    def buytocover(self, price, size, order_type=None, timeInForce=None, clOrdID=None):
        order_type = order_type or "Limit"
        timeInForce = timeInForce or "GoodTillCancel"
        result = self.__bitmex.create_order(symbol=self.__instrument_id, side="Buy", price=price, orderQty=size,
                                            ordType=order_type, timeInForce=timeInForce, clOrdID=clOrdID)
        try:
            raise SendOrderError(msg=result['error']['message'])
        except:
            return result

    @property
    def last(self):
        """获取ticker数据中的最新成交价"""
        if self.__ws.ws.sock.connected:
            last = self.__ws.get_ticker()['last']
            return last

    @property
    def asset(self):
        """获取账户资产"""
        if self.__ws.ws.sock.connected:
            satoshi = self.__ws.funds()['amount']
            xbt = (satoshi * 0.00000001)
            return xbt

    @property
    def __depth(self):
        if self.__ws.ws.sock.connected:
            asks = []
            bids = []
            data = self.__ws.market_depth()
            for item in data:
                if item['side'] == 'Sell':
                    asks.append(item)
                elif item['side'] == 'Buy':
                    bids.append(item)
            ask_price_list = []
            bid_price_list = []
            for j in asks:
                ask_price_list.append(j['price'])
            for x in bids:
                bid_price_list.append(x['price'])
            ask_price_list.sort(reverse=False)
            bid_price_list.sort(reverse=True)
            return {
                "ask_price_list": ask_price_list,
                "bid_price_list": bid_price_list
            }

    @property
    def asks(self):
        if self.__ws.ws.sock.connected:
            return self.__depth['ask_price_list']

    @property
    def bids(self):
        if self.__ws.ws.sock.connected:
            return self.__depth['bid_price_list']

    @property
    def hold_amount(self):
        """获取持仓数量，无论多空，返回值均为正数"""
        if self.__ws.ws.sock.connected:
            amount = abs(self.__ws.positions()[0]['currentQty'])
            return amount

    @property
    def hold_price(self):
        """获取持仓价格"""
        if self.__ws.ws.sock.connected:
            price = self.__ws.positions()[0]['avgCostPrice']
            return price

    @property
    def hold_direction(self):
        """获取当前持仓方向，bitmex只支持单向持仓模式"""
        if self.__ws.ws.sock.connected:
            if self.__ws.positions()[0]['currentQty'] > 0:
                direction = "long"
            elif self.__ws.positions()[0]['currentQty'] < 0:
                direction = "short"
            else:
                direction = "none"
            return direction

    def open_orders(self, clOrdID):
        """指定client order id 来查询订单信息，如果订单未成交，返回订单信息。如果订单已成交或已被取消，则返回空列表"""
        if self.__ws.ws.sock.connected:
            return self.__ws.open_orders(clOrdIDPrefix=clOrdID)

    @property
    def recent_trades(self):
        if self.__ws.ws.sock.connected:
            return self.__ws.recent_trades()