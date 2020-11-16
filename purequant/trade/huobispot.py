"""
火币现货
Author: Gary-Hertel
Date:   2020/10/27
email: purequant@foxmail.com
"""

import time
from purequant.time import ts_to_utc_str
from purequant.exchange.huobi import huobi_spot as huobispot
from purequant.config import config
from purequant.exceptions import *


class HUOBISPOT:

    def __init__(self, access_key, secret_key, instrument_id):
        """

        :param access_key:
        :param secret_key:
        :param instrument_id: e.g. 'ETC-USDT'
        """
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__instrument_id = (instrument_id.split('-')[0] + instrument_id.split('-')[1]).lower()
        self.__huobi_spot = huobispot.HuobiSVC(self.__access_key, self.__secret_key)
        self.__currency = (instrument_id.split('-')[0]).lower()
        self.__account_id = self.__huobi_spot.get_accounts()['data'][0]['id']

    def get_single_equity(self, currency):
        """
        获取单个币种的权益
        :param currency: 例如 "USDT"
        :return:返回浮点数
        """
        data = self.__huobi_spot.get_balance_currency(acct_id=self.__account_id, currency=currency)
        result = float(data[currency])
        return result

    def buy(self, price, size, order_type=None):
        """
        火币现货买入开多
        :param price: 价格
        :param size: 数量
        :param order_type: 填 0或者不填都是限价单，
                            1：只做Maker（Post only）
                            2：全部成交或立即取消（FOK）
                            3：立即成交并取消剩余（IOC）
                            4.市价买入
        :return:
        """
        if config.backtest is False:
            order_type=order_type or 'buy-limit'
            if order_type == 0:
                order_type = 'buy-limit'
            elif order_type == 1:
                order_type = 'buy-limit-maker'
            elif order_type == 2:
                order_type = 'buy-limit-fok'
            elif order_type == 3:
                order_type = 'buy-ioc'
            elif order_type == 4:
                order_type = 'buy-market'
            result = self.__huobi_spot.send_order(self.__account_id, size, 'spot-api', self.__instrument_id, _type=order_type, price=price)
            if result["status"] == "error": # 如果下单失败就抛出异常
                raise SendOrderError(result["err-msg"])
            order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                return {"【交易提醒】下单结果": order_info}
            # 如果订单状态不是"完全成交"或者"失败"
            if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
                if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['data'])
                            state = self.get_order_info(order_id=result['data'])
                            if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                                return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['data'])
                            state = self.get_order_info(order_id=result['data'])
                            if state['订单状态'] == "部分成交撤销":
                                return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
            if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
                time.sleep(config.time_cancellation_seconds)
                order_info = self.get_order_info(order_id=result['data'])
                if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "部分成交撤销":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if config.automatic_cancellation:
                # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
                try:
                    self.revoke_order(order_id=result['data'])
                    state = self.get_order_info(order_id=result['data'])
                    return {"【交易提醒】下单结果": state}
                except:
                    order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
                return {"【交易提醒】下单结果": order_info}
        else:
            return "回测模拟下单成功！"

    def sell(self, price, size, order_type=None):
        """
        火币现货卖出平多
        :param price: 价格
        :param size: 数量
        :param order_type: 填 0或者不填都是限价单，
                            1：只做Maker（Post only）
                            2：全部成交或立即取消（FOK）
                            3：立即成交并取消剩余（IOC）
                            4.市价卖出
        :return:
        """
        if config.backtest is False:
            order_type=order_type or 'sell-limit'
            if order_type == 0:
                order_type = 'sell-limit'
            elif order_type == 1:
                order_type = 'sell-limit-maker'
            elif order_type == 2:
                order_type = 'sell-limit-fok'
            elif order_type == 3:
                order_type = 'sell-ioc'
            elif order_type == 4:
                order_type = 'sell-market'
            result = self.__huobi_spot.send_order(self.__account_id, size, 'spot-api', self.__instrument_id, _type=order_type, price=price)
            if result["status"] == "error":  # 如果下单失败就抛出异常
                raise SendOrderError(result["err-msg"])
            order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                return {"【交易提醒】下单结果": order_info}
            # 如果订单状态不是"完全成交"或者"失败"
            if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
                if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                    if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['data'])
                            state = self.get_order_info(order_id=result['data'])
                            if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                                return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['data'])
                            state = self.get_order_info(order_id=result['data'])
                            if state['订单状态'] == "部分成交撤销":
                                return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
            if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
                time.sleep(config.time_cancellation_seconds)
                order_info = self.get_order_info(order_id=result['data'])
                if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "部分成交撤销":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if config.automatic_cancellation:
                # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
                try:
                    self.revoke_order(order_id=result['data'])
                    state = self.get_order_info(order_id=result['data'])
                    return {"【交易提醒】下单结果": state}
                except:
                    order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
                return {"【交易提醒】下单结果": order_info}
        else:
            return "回测模拟下单成功！"

    def get_order_info(self, order_id):
        result = self.__huobi_spot.order_info(order_id)
        instrument_id = self.__instrument_id
        action = None
        try:
            if "buy" in result['data']['type']:
                action = "买入开多"
            elif  "sell" in result['data']['type']:
                action = "卖出平多"
        except Exception as e:
            raise GetOrderError(e)

        if result["data"]['state'] == 'filled':
            dict = {"交易所": "Huobi现货", "合约ID": instrument_id, "方向": action, "订单状态": "完全成交",
                    "成交均价": float(result['data']['price']),
                    "已成交数量": float(result["data"]["field-amount"]),
                    "成交金额": float(result['data']["field-cash-amount"])}
            return dict
        elif result["data"]['state'] == 'canceled':
            dict = {"交易所": "Huobi现货", "合约ID": instrument_id, "方向": action, "订单状态": "撤单成功",
                    "成交均价": float(result['data']['price']),
                    "已成交数量": float(result["data"]["field-amount"]),
                    "成交金额": float(result['data']["field-cash-amount"])}
            return dict
        elif result["data"]['state'] == 'partial-filled':
            dict = {"交易所": "Huobi现货", "合约ID": instrument_id, "方向": action, "订单状态": "部分成交",
                    "成交均价": float(result['data']['price']),
                    "已成交数量": float(result["data"]["field-amount"]),
                    "成交金额": float(result['data']["field-cash-amount"])}
            return dict
        elif result["data"]['state'] == 'partial-canceled':
            dict = {"交易所": "Huobi现货", "合约ID": instrument_id, "方向": action, "订单状态": "部分成交撤销",
                    "成交均价": float(result['data']['price']),
                    "已成交数量": float(result["data"]["field-amount"]),
                    "成交金额": float(result['data']["field-cash-amount"])}
            return dict
        elif result["data"]['state'] == 'submitted':
            dict = {"交易所": "Huobi现货", "合约ID": instrument_id, "方向": action, "订单状态": "已提交"}
            return dict

    def revoke_order(self, order_id):
        receipt = self.__huobi_spot.cancel_order(order_id)
        if receipt['status'] == "ok":
            return '【交易提醒】交易所: Huobi 撤单成功'
        else:
            return '【交易提醒】交易所: Huobi 撤单失败' + receipt['data']['errors'][0]['err_msg']

    def get_kline(self, time_frame):
        if time_frame == '1m' or time_frame == '1M':
            period = '1min'
        elif time_frame == '5m' or time_frame == '5M':
            period = '5min'
        elif time_frame == '15m' or time_frame == '15M':
            period = '15min'
        elif time_frame == '30m' or time_frame == '30M':
            period = '30min'
        elif time_frame == '1h' or time_frame == '1H':
            period = '60min'
        elif time_frame == '4h' or time_frame == '4H':
            period = '4hour'
        elif time_frame == '1d' or time_frame == '1D':
            period = '1day'
        else:
            raise KlineError("交易所: Huobi k线周期错误，k线周期只能是【1m, 5m, 15m, 30m, 1h, 4h, 1d】!")
        records = self.__huobi_spot.get_kline(self.__instrument_id, period=period)['data']
        length = len(records)
        list = []
        for item in records:
            item = [ts_to_utc_str(item['id']), item['open'], item['high'], item['low'], item['close'], item['vol'],
                    round(item['amount'], 2)]
            list.append(item)
        return list

    def get_position(self):
        """获取当前交易对的计价货币的可用余额，如当前交易对为etc-usdt, 则获取的是etc的可用余额"""
        receipt = self.__huobi_spot.get_balance_currency(self.__account_id, self.__currency)
        direction = 'long'
        amount = receipt[self.__currency]
        price = None
        result = {'direction': direction, 'amount': amount, 'price': price}
        return result

    def get_ticker(self):
        receipt = self.__huobi_spot.get_ticker(self.__instrument_id)
        last = receipt['tick']['close']
        return {"last": last}

    def get_depth(self, type=None, size=None):
        """
        火币现货获取深度数据
        :param type: 如不传参，返回asks和bids；只获取asks传入type="asks"；只获取"bids"传入type="bids"
        :param size: 返回深度档位数量，取值范围：5，10，20，默认10档
        :return:
        """
        size = size or 10
        response = self.__huobi_spot.get_depth(self.__instrument_id, depth=size, type="step0")
        asks_list = response["tick"]["asks"]
        bids_list = response["tick"]["bids"]
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