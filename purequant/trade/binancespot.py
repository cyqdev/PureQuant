"""
币安现货
Author: Gary-Hertel
Date:   2020/10/27
email: purequant@foxmail.com
"""


import time
from purequant.exchange.binance import binance_spot
from purequant.time import ts_to_utc_str
from purequant.config import config
from purequant.exceptions import *


class BINANCESPOT:

    def __init__(self, access_key, secret_key, symbol):
        """
        初始化
        :param access_key: api_key
        :param secret_key: secret_key
        :param symbol: 币对，例如："EOS-USDT"
        """
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__instrument_id = symbol.split("-")[0] + symbol.split("-")[1]
        self.__currency = symbol.split("-")[0]
        self.__binance_spot = binance_spot
        self.__binance_spot.set(self.__access_key, self.__secret_key)   # 设置api

    def get_single_equity(self, currency):
        """
        获取单个币种的权益
        :param currency: 例如 "USDT"
        :return:返回浮点数
        """
        data = self.__binance_spot.balances()
        for i in data:
            if i == currency:
                balance = float(data[currency]["free"])
                return balance

    def buy(self, price, size, order_type=None, timeInForce=None):
        """
        币安现货买入
        :param price: 价格
        :param size: 数量
        :param order_type:默认限价单，LIMIT 限价单
                                    MARKET 市价单
                                    STOP_LOSS 止损单
                                    STOP_LOSS_LIMIT 限价止损单
                                    TAKE_PROFIT 止盈单
                                    TAKE_PROFIT_LIMIT 限价止盈单
                                    LIMIT_MAKER 限价卖单
        :param timeInForce:有效方式，定义了订单多久能够变成失效。
                            GTC	成交为止订单会一直有效，直到被成交或者取消。
                            IOC	无法立即成交的部分就撤销，订单在失效前会尽量多的成交。
                            FOK	无法全部立即成交就撤销，如果无法全部成交，订单会失效。
        :return:
        """
        if config.backtest != "enabled":  # 实盘模式
            order_type = "LIMIT" if order_type is None else order_type  # 默认限价单
            timeInForce = "GTC" if timeInForce is None else timeInForce  # 默认成交为止，订单会一直有效，直到被成交或者取消。
            result = self.__binance_spot.order(symbol=self.__instrument_id,
                                               side="BUY",
                                               quantity=size,
                                               price=price,
                                               orderType=order_type,
                                               timeInForce=timeInForce)
            if "msg" in str(result):   # 如果下单失败就抛出异常，提示错误信息。
                raise SendOrderError(result["msg"])
            order_info = self.get_order_info(order_id=result['orderId'])   # 下单后查询一次订单状态
            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                return {"【交易提醒】下单结果": order_info}
            # 如果订单状态不是"完全成交"或者"失败"
            if config.price_cancellation == "true":  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
                if order_info["订单状态"] == "等待成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['orderId'])
                            state = self.get_order_info(order_id=result['orderId'])
                            if state['订单状态'] == "撤单成功":
                                return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['orderId'])
                            state = self.get_order_info(order_id=result['orderId'])
                            if state['订单状态'] == "撤单成功":
                                return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                                size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
            if config.time_cancellation == "true":  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
                time.sleep(config.time_cancellation_seconds)
                order_info = self.get_order_info(order_id=result['orderId'])
                if order_info["订单状态"] == "等待成交":
                    try:
                        self.revoke_order(order_id=result['orderId'])
                        state = self.get_order_info(order_id=result['orderId'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    try:
                        self.revoke_order(order_id=result['orderId'])
                        state = self.get_order_info(order_id=result['orderId'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if config.automatic_cancellation == "true":
                # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
                try:
                    self.revoke_order(order_id=result['orderId'])
                    state = self.get_order_info(order_id=result['orderId'])
                    return {"【交易提醒】下单结果": state}
                except:
                    order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
                return {"【交易提醒】下单结果": order_info}
        else:  # 回测模式
            return "回测模拟下单成功！"

    def sell(self, price, size, order_type=None, timeInForce=None):
        if config.backtest != "enabled":  # 实盘模式
            order_type = "LIMIT" if order_type is None else order_type  # 默认限价单
            timeInForce = "GTC" if timeInForce is None else timeInForce  # 默认成交为止，订单会一直有效，直到被成交或者取消。
            result = self.__binance_spot.order(symbol=self.__instrument_id,
                                               side="SELL",
                                               quantity=size,
                                               price=price,
                                               orderType=order_type,
                                               timeInForce=timeInForce)
            if "msg" in str(result):   # 如果下单失败就抛出异常，提示错误信息。
                raise SendOrderError(result["msg"])
            order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                return {"【交易提醒】下单结果": order_info}
            # 如果订单状态不是"完全成交"或者"失败"
            if config.price_cancellation == "true":  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
                if order_info["订单状态"] == "等待成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['orderId'])
                            state = self.get_order_info(order_id=result['orderId'])
                            if state['订单状态'] == "撤单成功":
                                return self.sell(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['orderId'])
                            state = self.get_order_info(order_id=result['orderId'])
                            if state['订单状态'] == "撤单成功":
                                return self.sell(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                                size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
            if config.time_cancellation == "true":  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
                time.sleep(config.time_cancellation_seconds)
                order_info = self.get_order_info(order_id=result['orderId'])
                if order_info["订单状态"] == "等待成交":
                    try:
                        self.revoke_order(order_id=result['orderId'])
                        state = self.get_order_info(order_id=result['orderId'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    try:
                        self.revoke_order(order_id=result['orderId'])
                        state = self.get_order_info(order_id=result['orderId'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if config.automatic_cancellation == "true":
                # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
                try:
                    self.revoke_order(order_id=result['orderId'])
                    state = self.get_order_info(order_id=result['orderId'])
                    return {"【交易提醒】下单结果": state}
                except:
                    order_info = self.get_order_info(order_id=result['orderId'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
                return {"【交易提醒】下单结果": order_info}
        else:  # 回测模式
            return "回测模拟下单成功！"

    def get_order_info(self, order_id):
        """币安现货查询订单信息"""
        result = self.__binance_spot.orderStatus(symbol=self.__instrument_id, orderId=order_id)
        if "msg" in str(result):
            return self.get_order_info(order_id)
        instrument_id = self.__instrument_id
        action = None
        if result['side'] == 'BUY':
            action = "买入开多"
        elif result['side'] == 'SELL':
            action = "卖出平多"

        if result['status'] == "FILLED":
            dict = {"交易所": "币安现货", "币对": instrument_id, "方向": action, "订单状态": "完全成交",
                    "成交均价": float(result['price']),
                    "已成交数量": float(result['executedQty']),
                    "成交金额": float(result["cummulativeQuoteQty"])}
            return dict
        elif result['status'] == "REJECTED":
            dict = {"交易所": "币安现货", "币对": instrument_id, "方向": action, "订单状态": "失败"}
            return dict
        elif result['status'] == "CANCELED":
            dict = {"交易所": "币安现货", "币对": instrument_id, "方向": action, "订单状态": "撤单成功",
                    "成交均价": float(result['price']),
                    "已成交数量": float(result['executedQty']),
                    "成交金额": float(result["cummulativeQuoteQty"])}
            return dict
        elif result['status'] == "NEW":
            dict = {"交易所": "币安现货", "币对": instrument_id, "方向": action, "订单状态": "等待成交"}
            return dict
        elif result['status'] == "PARTIALLY_FILLED":
            dict = {"交易所": "币安现货", "币对": instrument_id, "方向": action, "订单状态": "部分成交",
                    "成交均价": float(result['price']),
                    "已成交数量": float(result['executedQty']),
                    "成交金额": float(result["cummulativeQuoteQty"])}
            return dict
        elif result['status'] == "EXPIRED":
            dict = {"交易所": "币安现货", "币对": instrument_id, "方向": action, "订单状态": "订单被交易引擎取消",
                    "成交均价": float(result['price']),
                    "已成交数量": float(result['executedQty']),
                    "成交金额": float(result["cummulativeQuoteQty"])}
            return dict
        elif result['status'] == "PENDING_CANCEL	":
            dict = {"交易所": "币安现货", "币对": instrument_id, "方向": action, "订单状态": "撤单中"}
            return dict

    def revoke_order(self, order_id):
        """币安现货撤销订单"""
        receipt = self.__binance_spot.cancel(self.__instrument_id, orderId=order_id)
        if receipt['status'] == "CANCELED":
            return '【交易提醒】撤单成功'
        else:
            return '【交易提醒】撤单失败'

    def get_ticker(self):
        """币安现货查询最新价"""
        response = self.__binance_spot.get_ticker(self.__instrument_id)
        receipt = {'symbol': response['symbol'], 'last': response['price']}
        return receipt

    def get_kline(self, time_frame):
        """
        币安现货获取k线数据
        :param time_frame: k线周期。1m， 3m， 5m， 15m， 30m， 1h， 2h， 4h， 6h， 8h， 12h， 1d， 3d， 1w， 1M
        :return:返回一个列表，包含开盘时间戳、开盘价、最高价、最低价、收盘价、成交量。
        """
        receipt = self.__binance_spot.klines(self.__instrument_id, time_frame)  # 获取历史k线数据
        last_kine = self.__binance_spot.get_last_kline(self.__instrument_id)    # 获取24hr 价格变动情况
        for item in receipt:
            item[0] = ts_to_utc_str(int(item[0])/1000)
            item.pop(6)
            item.pop(7)
            item.pop(8)
            item.pop(6)
            item.pop(7)
            item.pop(6)
        receipt.append(last_kine)
        receipt.reverse()
        return receipt

    def get_position(self):
        """
        币安现货获取持仓信息
        :return: 返回一个字典，{'direction': direction, 'amount': amount, 'price': price}
        """
        receipt = self.__binance_spot.balances()[self.__currency]
        direction = 'long'
        amount = receipt['free']
        price = None
        result = {'direction': direction, 'amount': amount, 'price': price}
        return result

    def get_depth(self, type=None):
        """
        币安现货获取深度数据
        :param type: 如不传参，返回asks和bids；只获取asks传入type="asks"；只获取"bids"传入type="bids"
        :return:返回10档深度数据
        """
        response = self.__binance_spot.depth(self.__instrument_id)
        asks_list = response["asks"]
        bids_list = response["bids"]
        asks = []
        bids = []
        for i in asks_list:
            asks.append(float(i[0]))
        for j in bids_list:
            bids.append(float(j[0]))
        if type == "asks":
            return asks
        elif type == "bids":
            return bids
        else:
            return response