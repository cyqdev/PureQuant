from purequant.exchange.mxc.mxc import Mxc
import time
from purequant.config import config
from purequant.exceptions import *


class MXC:

    def __init__(self, access_key, secret_key, symbol):
        """
        MXC交易所
        :param access_key: api key
        :param secret_key: secret key
        :param symbol: e.g. "BTC-USDT"
        """
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__symbol = symbol.replace("-", "_")
        self.__mxc = Mxc(self.__access_key, self.__secret_key)

    def get_order_list(self, deal_type):
        """
        获取账号委托历史记录
        deal_type：  1买  2卖
        """
        receipt = self.__mxc.get_private_order_history(self.__symbol, deal_type)
        return receipt

    def revoke_order(self, order_id):
        """撤销指定订单"""
        receipt = self.__mxc.cancel_order(self.__symbol, order_id)
        if receipt['msg'] == "OK":
            return True
        else:
            return False

    def get_order_info(self, order_id):
        result = self.__mxc.get_order_info(self.__symbol, order_id)
        action = None
        if result['data']['type'] == 1:
            action = "买入"
        elif result['data']['type'] == 2:
            action = "卖出"

        if int(result['data']['status']) == 2:
            dict = {"交易所": "MXC", "交易对": result['data']['market'], "方向": action, "订单状态": "完全成交",
                    "成交均价": float(result['data']['price']),
                    "已成交数量": float(result['data']['tradedQuantity']),
                    "成交金额": float(result['data']['tradedAmount']),
                    "order_id": order_id}
            return dict
        elif int(result['data']['status']) == 4:
            dict = {"交易所": "MXC", "交易对": result['data']['market'], "方向": action, "订单状态": "撤单成功",
                    "成交均价": float(result['data']['price']),
                    "已成交数量": float(result['data']['tradedQuantity']),
                    "成交金额": float(result['data']['tradedAmount']),
                    "order_id": order_id}
            return dict
        elif int(result['data']['status']) == 1:
            dict = {"交易所": "MXC", "交易对": result['data']['market'], "方向": action, "订单状态": "等待成交", "order_id": order_id}
            return dict
        elif int(result['data']['status']) == 3:
            dict = {"交易所": "MXC", "交易对": result['data']['market'], "方向": action, "订单状态": "部分成交",
                    "成交均价": float(result['data']['price']),
                    "已成交数量": float(result['data']['tradedQuantity']),
                    "成交金额": float(result['data']['tradedAmount']),
                    "order_id": order_id}
            return dict
        elif int(result['data']['status']) == 5:
            dict = {"交易所": "MXC", "交易对": result['data']['market'], "方向": action, "订单状态": "部分撤单", "order_id": order_id}
            return dict

    def get_kline(self, time_frame):
        receipt = self.__mxc.get_kline(self.__symbol, timeframe=time_frame)['data']
        kline = []
        for item in receipt:
            kline.append([item[0], float(item[1]), float(item[3]), float(item[4]), float(item[2]), float(item[5]), float(item[6])])
        kline.reverse()
        return kline

    def get_position(self):
        receipt = self.__mxc.get_account_info()
        for item in receipt:
            available = float(item[self.__symbol]['available'])
            result = {'direction': 'long', 'amount': available, 'price': None}
            return result

    def get_ticker(self):
        response = self.__mxc.get_ticker(self.__symbol)
        receipt = {'symbol': self.__symbol, 'last': float(response['data']['last'])}
        return receipt

    def get_depth(self, type=None, size=None):
        size = size or 10
        response = self.__mxc.get_depth(symbol=self.__symbol, depth=size)
        asks_list = response['data']['asks']
        bids_list = response['data']['bids']
        bids = []
        asks = []
        for i in asks_list:
            asks.append(float(i['price']))
        for j in bids_list:
            bids.append(float(j['price']))
        bids.reverse()
        if type == "asks":
            return asks
        elif type == "bids":
            return bids
        else:
            return {"asks": asks, "bids": bids}

    def get_single_equity(self, currency):
        receipt = self.__mxc.get_account_info()
        for item in receipt:
            available = float(item[self.__symbol]['available'])
            result = available
            return result

    def buy(self, price, size):
        result = self.__mxc.create_order(symbol=self.__symbol, price=price, quantity=size, trade_type=1)
        try:
            order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
        except:
            raise SendOrderError(result['msg'])
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return order_info
            # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return order_info
            if order_info["订单状态"] == "部分成交":  # 部分成交时撤单然后重发委托，下单数量为原下单数量减去已成交数量
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return order_info
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['data'])
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id=result['data'])
                    state = self.get_order_info(order_id=result['data'])
                    if state['订单状态'] == "撤单成功":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                        size - state["已成交数量"])
                except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                    order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return order_info
            if order_info["订单状态"] == "部分成交":  # 部分成交时撤单然后重发委托，下单数量为原下单数量减去已成交数量
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return order_info
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['data'])
                state = self.get_order_info(order_id=result['data'])
                return state
            except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                    return order_info
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return order_info

    def sell(self, price, size):
        result = self.__mxc.create_order(symbol=self.__symbol, price=price, quantity=size, trade_type=2)
        try:
            order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
        except:
            raise SendOrderError(result['msg'])
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return order_info
            # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "等待成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                             size - state["已成交数量"])
                    except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return order_info
            if order_info["订单状态"] == "部分成交":  # 部分成交时撤单然后重发委托，下单数量为原下单数量减去已成交数量
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                             size - state["已成交数量"])
                    except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return order_info
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['data'])
            if order_info["订单状态"] == "等待成交":
                try:
                    self.revoke_order(order_id=result['data'])
                    state = self.get_order_info(order_id=result['data'])
                    if state['订单状态'] == "撤单成功":
                        return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                         size - state["已成交数量"])
                except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                    order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return order_info
            if order_info["订单状态"] == "部分成交":  # 部分成交时撤单然后重发委托，下单数量为原下单数量减去已成交数量
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data'])
                        state = self.get_order_info(order_id=result['data'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                             size - state["已成交数量"])
                    except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                        order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return order_info
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['data'])
                state = self.get_order_info(order_id=result['data'])
                return state
            except:  # 如撤单失败，则说明已经完全成交，此时再查询一次订单状态然后返回下单结果
                order_info = self.get_order_info(order_id=result['data'])  # 下单后查询一次订单状态
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                    return order_info
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return order_info



if __name__ == '__main__':
    exchange = MXC("", "", "BTC-USDT")
    info = exchange.get_depth()
    print(info)