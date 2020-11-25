"""
bitcoke
Author: Gary-Hertel
Date:   2020/10/27
email: purequant@foxmail.com
"""

from purequant.exchange.bitcoke.bitcoke import BitCoke
from purequant.exceptions import *
from purequant.config import config
import time

class BITCOKE:

    def __init__(self, access_key, secret_key, currency, instrument_id, margin_mode=None, leverage=None, position_side=None):
        """
        access_key: api key
        secret_key: secret key
        currency: e.g. "EOS"
        instrument_id: e.g. "XBTCUSD"
        leverage: e.g. 10
        position_side: "both" or None
        """
        self.__symbol = instrument_id
        self.__currency = currency
        self.__bitcoke = BitCoke(access_key, secret_key)
        self.__leverage = leverage or 20
        self.__position_side = position_side  # 持仓模式
        if self.__position_side == "both":
            self.__bitcoke.switch_pos_side(currency, True)
        else:
            self.__bitcoke.switch_pos_side(currency, False)

        if margin_mode == "fixed":
            pass
        else:
            self.__bitcoke.switch_to_cross(currency)
        self.__bitcoke.change_pos_leverage(currency, symbol=self.__symbol, leverage=self.__leverage)

    def get_single_equity(self, currency):
        """获取单个币种的权益"""
        data = self.__bitcoke.get_account_info()
        for i in data['result']:
            if i['currency'] == currency:
                balance = i['cash']
                return balance

    def get_depth(self, type=None):
        response = self.__bitcoke.get_market_depth(self.__symbol)
        bids_list = response["result"]['buyDepth']
        asks_list = response["result"]['sellDepth']
        asks = []
        bids = []
        for i in bids_list:
            bids.append(i['price'])
        for j in asks_list:
            asks.append(j['price'])
        asks.reverse()
        if type == "asks":
            return asks
        elif type == "bids":
            return bids
        else:
            return {"asks": asks, "bids": bids}

    def get_position(self, mode=None):
        if mode == "both":
            long_amount = 0
            long_price = 0
            short_amount = 0
            short_price = 0
            receipt = self.__bitcoke.get_position()
            for item in receipt['result']:
                if item['currency'] == self.__currency and item['symbol'] == self.__symbol:
                    if item['side'] == "Long":
                        long_amount = item['qty']
                        long_price = item['price']
                    if item['side'] == "Short":
                        short_amount = item['qty']
                        short_price = item['price']
            return {
                "long": {
                    "price": long_price,
                    "amount": long_amount
                },
                "short": {
                    "price": short_price,
                    "amount": short_amount
                }
            }
        else:
            long_amount = 0
            long_price = 0
            short_amount = 0
            short_price = 0
            receipt = self.__bitcoke.get_position()
            for item in receipt['result']:
                if item['currency'] == self.__currency and item['symbol'] == self.__symbol:
                    if item['side'] == "Long":
                        long_amount = item['qty']
                        long_price = item['price']
                    if item['side'] == "Short":
                        short_amount = item['qty']
                        short_price = item['price']

                    if short_amount > 0:
                        return {'direction': "short", 'amount': short_amount, 'price': short_price}
                    elif long_amount > 0:
                        return {'direction': "long", 'amount': long_amount, 'price': long_price}
                    else:
                        return {'direction': "none", 'amount': 0, 'price': 0}

    def get_contract_value(self):
        receipt = self.__bitcoke.get_contract_info()
        for item in  receipt['result']:
            if item['symbol'] == self.__symbol:
                return item['lotSize']

    def get_kline(self, time_frame):
        receipt = self.__bitcoke.get_kline(self.__symbol, time_frame)
        kline = []
        for item in receipt['result']:
            kline.append([item['keyTime'].replace("+0000", "z"), item['open'], item['high'], item['low'], item['close'], item['volume']])
        return kline

    def get_ticker(self):
        response = self.__bitcoke.get_last_price(self.__symbol)
        receipt = {'symbol': self.__symbol, 'last': response['result'][self.__symbol]}
        return receipt

    def revoke_order(self, order_id):
        receipt = self.__bitcoke.cancel_order(order_id)
        if receipt['message'] == "OK":
            return '【交易提醒】撤单成功'
        else:
            return '【交易提醒】撤单失败'

    def get_order_info(self, order_id):
        result = self.__bitcoke.get_order_info(order_id)
        action = None
        if result['result']['side'] == "Buy" and result['result']['openPosition'] is True:
            action = "买入开多"
        elif result['result']['side'] == "Buy" and result['result']['openPosition'] is False:
            action = "买入平空"
        elif result['result']['side'] == "Sell" and result['result']['openPosition'] is True:
            action = "卖出开空"
        elif result['result']['side'] == "Sell" and result['result']['openPosition'] is False:
            action = "卖出平多"

        if result['result']['ordStatus'] == "FILLED":
            dict = {"交易所": "BITCOKE", "币对": self.__symbol, "方向": action, "订单状态": "完全成交",
                    "成交均价": result['result']['avgPx'],
                    "已成交数量": int(result['result']['cumQty']),
                    "成交金额": result["result"]['cumQty']}
            return dict
        elif result['result']['ordStatus'] == "REJECTED":
            dict = {"交易所": "BITCOKE", "币对": self.__symbol, "方向": action, "订单状态": "失败"}
            return dict
        elif result['result']['ordStatus'] == "CANCELED":
            dict = {"交易所": "BITCOKE", "币对": self.__symbol, "方向": action, "订单状态": "撤单成功",
                    "成交均价": result['result']['avgPx'],
                    "已成交数量": int(result['result']['cumQty']),
                    "成交金额": result["result"]['cumQty']}
            return dict
        elif result['result']['ordStatus'] == "NEW":
            dict = {"交易所": "BITCOKE", "币对": self.__symbol, "方向": action, "订单状态": "等待成交"}
            return dict
        elif result['result']['ordStatus'] == "PARTIALLY_FILLED":
            dict = {"交易所": "BITCOKE", "币对": self.__symbol, "方向": action, "订单状态": "部分成交",
                    "成交均价": result['result']['avgPx'],
                    "已成交数量": int(result['result']['cumQty']),
                    "成交金额": result["result"]['cumQty']}
            return dict
        elif result['result']['ordStatus'] == "WAITING ":
            dict = {"交易所": "BITCOKE", "币对": self.__symbol, "方向": action, "订单状态": "等待（条件单）"}
            return dict

    def buy(self, price, size, order_type=None, stopLossPrice=None, trailingStop=None, stopWinPrice=None,
            stopWinType=None, triggerPrice=None, triggerType=None, tif=None):
        order_type = order_type or "Limit"
        result = self.__bitcoke.create_order(
            currency=self.__currency,
            open_position=True,
            order_type=order_type,
            qty=size,
            side="Buy",
            symbol=self.__symbol,
            price=price,
            stopLossPrice=stopLossPrice,
            trailingStop=trailingStop,
            stopWinPrice=stopWinPrice,
            stopWinType=stopWinType,
            triggerPrice=triggerPrice,
            triggerType=triggerType,
            tif=tif
        )
        if result['message'] != "OK":  # 如果下单失败就抛出异常，提示错误信息。
            raise SendOrderError(result["message"])
        order_info = self.get_order_info(order_id=result['result'])  # 下单后查询一次订单状态
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return {"【交易提醒】下单结果": order_info}
        # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['result'])
                        state = self.get_order_info(order_id=result['result'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['result'])
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                            return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['result'])
                        state = self.get_order_info(order_id=result['result'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['result'])
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                            return {"【交易提醒】下单结果": order_info}
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['result'])
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id=result['result'])
                    state = self.get_order_info(order_id=result['result'])
                    if state['订单状态'] == "撤单成功":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['result'])
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                        return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id=result['result'])
                    state = self.get_order_info(order_id=result['result'])
                    if state['订单状态'] == "撤单成功":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['result'])
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                        return {"【交易提醒】下单结果": order_info}
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['result'])
                state = self.get_order_info(order_id=result['result'])
                return {"【交易提醒】下单结果": state}
            except:
                order_info = self.get_order_info(order_id=result['result'])
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                    return {"【交易提醒】下单结果": order_info}
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return {"【交易提醒】下单结果": order_info}

    def buytocover(self, price, size, order_type=None, stopLossPrice=None, trailingStop=None, stopWinPrice=None,
            stopWinType=None, triggerPrice=None, triggerType=None, tif=None):
        order_type = order_type or "Limit"
        result = self.__bitcoke.create_order(
            currency=self.__currency,
            open_position=False,
            order_type=order_type,
            qty=size,
            side="Buy",
            symbol=self.__symbol,
            price=price,
            stopLossPrice=stopLossPrice,
            trailingStop=trailingStop,
            stopWinPrice=stopWinPrice,
            stopWinType=stopWinType,
            triggerPrice=triggerPrice,
            triggerType=triggerType,
            tif=tif
        )
        if result['message'] != "OK":  # 如果下单失败就抛出异常，提示错误信息。
            raise SendOrderError(result["message"])
        order_info = self.get_order_info(order_id=result['result'])  # 下单后查询一次订单状态
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return {"【交易提醒】下单结果": order_info}
        # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['result'])
                        state = self.get_order_info(order_id=result['result'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['result'])
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                            return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['result'])
                        state = self.get_order_info(order_id=result['result'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['result'])
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                            return {"【交易提醒】下单结果": order_info}
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['result'])
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id=result['result'])
                    state = self.get_order_info(order_id=result['result'])
                    if state['订单状态'] == "撤单成功":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['result'])
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                        return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id=result['result'])
                    state = self.get_order_info(order_id=result['result'])
                    if state['订单状态'] == "撤单成功":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['result'])
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                        return {"【交易提醒】下单结果": order_info}
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['result'])
                state = self.get_order_info(order_id=result['result'])
                return {"【交易提醒】下单结果": state}
            except:
                order_info = self.get_order_info(order_id=result['result'])
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                    return {"【交易提醒】下单结果": order_info}
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return {"【交易提醒】下单结果": order_info}

    def sell(self, price, size, order_type=None, stopLossPrice=None, trailingStop=None, stopWinPrice=None,
            stopWinType=None, triggerPrice=None, triggerType=None, tif=None):
        order_type = order_type or "Limit"
        result = self.__bitcoke.create_order(
            currency=self.__currency,
            open_position=False,
            order_type=order_type,
            qty=size,
            side="Sell",
            symbol=self.__symbol,
            price=price,
            stopLossPrice=stopLossPrice,
            trailingStop=trailingStop,
            stopWinPrice=stopWinPrice,
            stopWinType=stopWinType,
            triggerPrice=triggerPrice,
            triggerType=triggerType,
            tif=tif
        )
        if result['message'] != "OK":  # 如果下单失败就抛出异常，提示错误信息。
            raise SendOrderError(result["message"])
        order_info = self.get_order_info(order_id=result['result'])  # 下单后查询一次订单状态
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return {"【交易提醒】下单结果": order_info}
        # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['result'])
                        state = self.get_order_info(order_id=result['result'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['result'])
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                            return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['result'])
                        state = self.get_order_info(order_id=result['result'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['result'])
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                            return {"【交易提醒】下单结果": order_info}
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['result'])
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id=result['result'])
                    state = self.get_order_info(order_id=result['result'])
                    if state['订单状态'] == "撤单成功":
                        return self.sell(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['result'])
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                        return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id=result['result'])
                    state = self.get_order_info(order_id=result['result'])
                    if state['订单状态'] == "撤单成功":
                        return self.sell(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['result'])
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                        return {"【交易提醒】下单结果": order_info}
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['result'])
                state = self.get_order_info(order_id=result['result'])
                return {"【交易提醒】下单结果": state}
            except:
                order_info = self.get_order_info(order_id=result['result'])
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                    return {"【交易提醒】下单结果": order_info}
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return {"【交易提醒】下单结果": order_info}

    def sellshort(self, price, size, order_type=None, stopLossPrice=None, trailingStop=None, stopWinPrice=None,
            stopWinType=None, triggerPrice=None, triggerType=None, tif=None):
        order_type = order_type or "Limit"
        result = self.__bitcoke.create_order(
            currency=self.__currency,
            open_position=True,
            order_type=order_type,
            qty=size,
            side="Sell",
            symbol=self.__symbol,
            price=price,
            stopLossPrice=stopLossPrice,
            trailingStop=trailingStop,
            stopWinPrice=stopWinPrice,
            stopWinType=stopWinType,
            triggerPrice=triggerPrice,
            triggerType=triggerType,
            tif=tif
        )
        if result['message'] != "OK":  # 如果下单失败就抛出异常，提示错误信息。
            raise SendOrderError(result["message"])
        order_info = self.get_order_info(order_id=result['result'])  # 下单后查询一次订单状态
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return {"【交易提醒】下单结果": order_info}
        # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['result'])
                        state = self.get_order_info(order_id=result['result'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['result'])
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                            return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['result'])
                        state = self.get_order_info(order_id=result['result'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['result'])
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                            return {"【交易提醒】下单结果": order_info}
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['result'])
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id=result['result'])
                    state = self.get_order_info(order_id=result['result'])
                    if state['订单状态'] == "撤单成功":
                        return self.sell(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['result'])
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                        return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id=result['result'])
                    state = self.get_order_info(order_id=result['result'])
                    if state['订单状态'] == "撤单成功":
                        return self.sell(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['result'])
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                        return {"【交易提醒】下单结果": order_info}
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['result'])
                state = self.get_order_info(order_id=result['result'])
                return {"【交易提醒】下单结果": state}
            except:
                order_info = self.get_order_info(order_id=result['result'])
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":
                    return {"【交易提醒】下单结果": order_info}
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return {"【交易提醒】下单结果": order_info}

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

    def get_funding_rate(self):
        """获取最新资金费率"""
        data = self.__bitcoke.get_funding_rate(self.__symbol)
        instrument_id = data['result'][0]['symbol']
        funding_time = data['result'][0]['date']
        funding_rate = data['result'][0]['rate']
        result = {
            "instrument_id": instrument_id,
            "funding_time": funding_time,
            "funding_rate": funding_rate
        }
        return result


if __name__ == '__main__':
    exchange = BITCOKE("",
                       "",
                       currency="EOS",
                       instrument_id="XEOSUSD",
                       leverage=20,
                       position_side="both")

    config.loads('config.json')
    info = exchange.sell(3, 20)
    print(info)