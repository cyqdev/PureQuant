"""
bitmex
Author: Gary-Hertel
Date:   2020/10/27
email: purequant@foxmail.com
"""

import time
from purequant.exchange.bitmex.bitmex import Bitmex
from purequant.config import config
from purequant.exceptions import *

class BITMEX:

    def __init__(self, access_key, secret_key, instrument_id, leverage=None, testing=None):
        """
        BITMEX rest api
        :param access_key: api key
        :param secret_key: secret key
        :param instrument_id: 合约id，例如："XBTUSD"
        :param testing:是否是测试账户，默认为False
        :param leverage:开仓杠杆倍数，如不填则默认设置为20倍
        """
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__instrument_id = instrument_id
        self.__testing = False or testing
        self.__bitmex = Bitmex(self.__access_key, self.__secret_key, testing=self.__testing)
        self.__leverage = leverage or 20
        self.__bitmex.set_leverage(self.__instrument_id, leverage=self.__leverage)

    def get_single_equity(self, currency=None):
        """
        获取合约的权益
        :param currency: 默认为"XBt",BITMEX所有的交易是用XBT来结算的
        :return:返回浮点数
        """
        currency = "XBt"
        data = self.__bitmex.get_wallet(currency=currency)
        XBT = data["prevAmount"] * 0.00000001
        return XBT

    def get_depth(self, type=None, depth=None):
        """
        BITMEX获取深度数据
        :param type:如不传参，返回asks和bids；只获取asks传入type="asks"；只获取"bids"传入type="bids"
        :param depth:返回深度档位数量，默认10档
        :return:
        """
        depth = depth or 10
        response = self.__bitmex.get_orderbook(self.__instrument_id, depth=depth)
        asks_list = []   # 卖盘
        bids_list = []   # 买盘
        for i in response:
            if i['side'] == "Sell":
                asks_list.append(i['price'])
            elif i['side'] == "Buy":
                bids_list.append(i['price'])
        result = {"asks": asks_list, "bids": bids_list}
        if type == "asks":
            return asks_list
        elif type == "bids":
            return bids_list
        else:
            return result

    def get_ticker(self):
        """获取最新成交价"""
        receipt = self.__bitmex.get_trade(symbol=self.__instrument_id, reverse=True, count=10)[0]
        last = receipt["price"]
        return {"last": last}

    def get_position(self):
        try:
            result = self.__bitmex.get_positions(symbol=self.__instrument_id)[0]
            if result["currentQty"] > 0:
                dict = {'direction': 'long', 'amount': result["currentQty"],
                        'price': result["avgCostPrice"]}
                return dict
            elif result["currentQty"] < 0:
                dict = {'direction': 'short', 'amount': abs(result['currentQty']),
                        'price': result['avgCostPrice']}
                return dict
            else:
                dict = {'direction': 'none', 'amount': 0, 'price': 0.0}
                return dict
        except Exception as e:
            raise GetPositionError(e)

    def get_kline(self, time_frame, count=None):
        """
        获取k线数据
        :param time_frame: k线周期
        :param count: 返回的k线数量，默认为200条
        :return:
        """
        count = count or 200
        records = []
        response = self.__bitmex.get_bucket_trades(binSize=time_frame, partial=False, symbol=self.__instrument_id,
                                                   columns="timestamp, open, high, low, close, volume", count=count,
                                                   reverse=True)
        for i in response:
            records.append([i['timestamp'], i['open'], i['high'], i['low'], i['close'], i['volume']])
        return records

    def revoke_order(self, order_id):
        receipt = self.__bitmex.cancel_order(order_id)
        return receipt

    def get_order_info(self):
        result = self.__bitmex.get_orders(symbol=self.__instrument_id, count=1, reverse=True)[0]
        action = "买入" if result['side'] == "Buy" else "卖出"
        symbol = result["symbol"]
        price = result["avgPx"]
        amount = result["cumQty"]
        order_status = result['ordStatus']
        if order_status == "Filled":
            dict = {"交易所": "BITMEX", "合约ID": symbol, "方向": action,
                    "订单状态": "完全成交", "成交均价": price, "已成交数量": amount}
            return dict
        elif order_status == "Rejected":
            dict = {"交易所": "BITMEX", "合约ID": symbol, "方向": action, "订单状态": "失败"}
            return dict
        elif order_status == "Canceled":
            dict = {"交易所": "BITMEX", "合约ID": symbol, "方向": action, "订单状态": "撤单成功",
                    "成交均价": price, "已成交数量": amount}
            return dict
        elif order_status == "New":
            dict = {"交易所": "BITMEX", "合约ID": symbol, "方向": action, "订单状态": "等待成交"}
            return dict
        elif order_status == "PartiallyFilled":
            dict = {"交易所": "BITMEX", "合约ID": symbol, "方向": action, "订单状态": "部分成交",
                    "成交均价": price, "已成交数量": amount}
            return dict


    def buy(self, price, size, order_type=None, timeInForce=None):
        """
        买入开多
        :param price: 价格
        :param amount: 数量
        :param order_type: Market, Limit, Stop, StopLimit, MarketIfTouched, LimitIfTouched, Pegged，默认是"Limit"
        :param timeInForce:Day, GoodTillCancel, ImmediateOrCancel, FillOrKill, 默认是"GoodTillCancel"
        :return:
        """
        order_type = order_type or "Limit"
        timeInForce = timeInForce or "GoodTillCancel"
        result = self.__bitmex.create_order(symbol=self.__instrument_id, side="Buy", price=price, orderQty=size,
                                            ordType=order_type, timeInForce=timeInForce)
        try:
            raise SendOrderError(msg=result['error']['message'])
        except:
            order_id = result["orderID"]
            order_info = self.get_order_info()  # 下单后查询一次订单状态
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return order_info
            # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:  # 如果撤单失败，则订单可能在此期间已完全成交或部分成交
                        self.revoke_order(order_id)
                        state = self.get_order_info()
                        if state['订单状态'] == "撤单成功":  # 已完全成交时，以原下单数量重发；部分成交时，重发委托数量为原下单数量减去已成交数量
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:  # 撤单失败时，说明订单已完全成交
                        order_info = self.get_order_info()  # 再查询一次订单状态
                        if order_info["订单状态"] == "完全成交":
                            return order_info
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id)
                        state = self.get_order_info()
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:  # 撤单失败时，说明订单已完全成交，再查询一次订单状态，如果已完全成交，返回下单结果
                        order_info = self.get_order_info()  # 再查询一次订单状态
                        if order_info["订单状态"] == "完全成交":
                            return order_info
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info()
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id)
                    state = self.get_order_info()
                    if state['订单状态'] == "撤单成功":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info()  # 再查询一次订单状态
                    if order_info["订单状态"] == "完全成交":
                        return order_info
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id)
                    state = self.get_order_info()
                    if state['订单状态'] == "撤单成功":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info()  # 再查询一次订单状态
                    if order_info["订单状态"] == "完全成交":
                        return order_info
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id)
                state = self.get_order_info()
                return state
            except:
                order_info = self.get_order_info()  # 再查询一次订单状态
                if order_info["订单状态"] == "完全成交":
                    return order_info
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return order_info

    def sell(self, price, size, order_type=None, timeInForce=None):
        order_type = order_type or "Limit"
        timeInForce = timeInForce or "GoodTillCancel"
        result = self.__bitmex.create_order(symbol=self.__instrument_id, side="Sell", price=price, orderQty=size,
                                            ordType=order_type, timeInForce=timeInForce)
        try:
            raise SendOrderError(msg=result['error']['message'])
        except:
            order_id = result["orderID"]
            order_info = self.get_order_info()  # 下单后查询一次订单状态
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return order_info
            # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:  # 如果撤单失败，则订单可能在此期间已完全成交或部分成交
                        self.revoke_order(order_id)
                        state = self.get_order_info()
                        if state['订单状态'] == "撤单成功":  # 已完全成交时，以原下单数量重发；部分成交时，重发委托数量为原下单数量减去已成交数量
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                            size + state["已成交数量"])
                    except:  # 撤单失败时，说明订单已完全成交
                        order_info = self.get_order_info()  # 再查询一次订单状态
                        if order_info["订单状态"] == "完全成交":
                            return order_info
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id)
                        state = self.get_order_info()
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                            size + state["已成交数量"])
                    except:  # 撤单失败时，说明订单已完全成交，再查询一次订单状态，如果已完全成交，返回下单结果
                        order_info = self.get_order_info()  # 再查询一次订单状态
                        if order_info["订单状态"] == "完全成交":
                            return order_info
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info()
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id)
                    state = self.get_order_info()
                    if state['订单状态'] == "撤单成功":
                        return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                        size + state["已成交数量"])
                except:
                    order_info = self.get_order_info()  # 再查询一次订单状态
                    if order_info["订单状态"] == "完全成交":
                        return order_info
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id)
                    state = self.get_order_info()
                    if state['订单状态'] == "撤单成功":
                        return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                        size + state["已成交数量"])
                except:
                    order_info = self.get_order_info()  # 再查询一次订单状态
                    if order_info["订单状态"] == "完全成交":
                        return order_info
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id)
                state = self.get_order_info()
                return state
            except:
                order_info = self.get_order_info()  # 再查询一次订单状态
                if order_info["订单状态"] == "完全成交":
                    return order_info
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return order_info

    def sellshort(self, price, size, order_type=None, timeInForce=None):
        order_type = order_type or "Limit"
        timeInForce = timeInForce or "GoodTillCancel"
        result = self.__bitmex.create_order(symbol=self.__instrument_id, side="Sell", price=price, orderQty=size,
                                            ordType=order_type, timeInForce=timeInForce)
        try:
            raise SendOrderError(msg=result['error']['message'])
        except:
            order_id = result["orderID"]
            order_info = self.get_order_info()  # 下单后查询一次订单状态
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return order_info
            # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:  # 如果撤单失败，则订单可能在此期间已完全成交或部分成交
                        self.revoke_order(order_id)
                        state = self.get_order_info()
                        if state['订单状态'] == "撤单成功":  # 已完全成交时，以原下单数量重发；部分成交时，重发委托数量为原下单数量减去已成交数量
                            return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                            size + state["已成交数量"])
                    except:  # 撤单失败时，说明订单已完全成交
                        order_info = self.get_order_info()  # 再查询一次订单状态
                        if order_info["订单状态"] == "完全成交":
                            return order_info
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id)
                        state = self.get_order_info()
                        if state['订单状态'] == "撤单成功":
                            return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                            size + state["已成交数量"])
                    except:  # 撤单失败时，说明订单已完全成交，再查询一次订单状态，如果已完全成交，返回下单结果
                        order_info = self.get_order_info()  # 再查询一次订单状态
                        if order_info["订单状态"] == "完全成交":
                            return order_info
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info()
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id)
                    state = self.get_order_info()
                    if state['订单状态'] == "撤单成功":
                        return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                        size + state["已成交数量"])
                except:
                    order_info = self.get_order_info()  # 再查询一次订单状态
                    if order_info["订单状态"] == "完全成交":
                        return order_info
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id)
                    state = self.get_order_info()
                    if state['订单状态'] == "撤单成功":
                        return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                        size + state["已成交数量"])
                except:
                    order_info = self.get_order_info()  # 再查询一次订单状态
                    if order_info["订单状态"] == "完全成交":
                        return order_info
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id)
                state = self.get_order_info()
                return state
            except:
                order_info = self.get_order_info()  # 再查询一次订单状态
                if order_info["订单状态"] == "完全成交":
                    return order_info
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return order_info

    def buytocover(self, price, size, order_type=None, timeInForce=None):
        order_type = order_type or "Limit"
        timeInForce = timeInForce or "GoodTillCancel"
        result = self.__bitmex.create_order(symbol=self.__instrument_id, side="Buy", price=price, orderQty=size,
                                            ordType=order_type, timeInForce=timeInForce)
        try:
            raise SendOrderError(msg=result['error']['message'])
        except:
            order_id = result["orderID"]
            order_info = self.get_order_info()  # 下单后查询一次订单状态
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return order_info
            # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:  # 如果撤单失败，则订单可能在此期间已完全成交或部分成交
                        self.revoke_order(order_id)
                        state = self.get_order_info()
                        if state['订单状态'] == "撤单成功":  # 已完全成交时，以原下单数量重发；部分成交时，重发委托数量为原下单数量减去已成交数量
                            return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:  # 撤单失败时，说明订单已完全成交
                        order_info = self.get_order_info()  # 再查询一次订单状态
                        if order_info["订单状态"] == "完全成交":
                            return order_info
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id)
                        state = self.get_order_info()
                        if state['订单状态'] == "撤单成功":
                            return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:  # 撤单失败时，说明订单已完全成交，再查询一次订单状态，如果已完全成交，返回下单结果
                        order_info = self.get_order_info()  # 再查询一次订单状态
                        if order_info["订单状态"] == "完全成交":
                            return order_info
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info()
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id)
                    state = self.get_order_info()
                    if state['订单状态'] == "撤单成功":
                        return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info()  # 再查询一次订单状态
                    if order_info["订单状态"] == "完全成交":
                        return order_info
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id)
                    state = self.get_order_info()
                    if state['订单状态'] == "撤单成功":
                        return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info()  # 再查询一次订单状态
                    if order_info["订单状态"] == "完全成交":
                        return order_info
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id)
                state = self.get_order_info()
                return state
            except:
                order_info = self.get_order_info()  # 再查询一次订单状态
                if order_info["订单状态"] == "完全成交":
                    return order_info
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return order_info

    def BUY(self, cover_short_price, cover_short_size, open_long_price, open_long_size, order_type=None):
        result1 = self.buytocover(cover_short_price, cover_short_size, order_type)
        if "完全成交" in str(result1):
            result2 = self.buy(open_long_price, open_long_size, order_type)
            return {"平仓结果": result1, "开仓结果": result2}
        else:
            return result1

    def SELL(self, cover_long_price, cover_long_size, open_short_price, open_short_size, order_type=None):
        result1 = self.sell(cover_long_price, cover_long_size, order_type)
        if "完全成交" in str(result1):
            result2 = self.sellshort(open_short_price, open_short_size, order_type)
            return {"平仓结果": result1, "开仓结果": result2}
        else:
            return result1