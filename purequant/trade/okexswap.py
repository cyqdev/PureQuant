"""
okex永续合约
https://www.okex.com/docs/zh/#swap-README
Author: Gary-Hertel
Date:   2020/10/27
email: purequant@foxmail.com
"""

import time
from purequant.exchange.okex import swap_api as okexswap
from purequant.config import config
from purequant.exceptions import *


class OKEXSWAP:

    def __init__(self, access_key, secret_key, passphrase, instrument_id, leverage=None):
        """
        okex永续合约
        :param access_key:
        :param secret_key:
        :param passphrase:
        :param instrument_id: 例如："BTC-USDT-SWAP", "BTC-USD-SWAP"
        :param leverage:杠杆倍数，如不填则默认设置20倍杠杆
        """
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__passphrase = passphrase
        self.__instrument_id = instrument_id
        self.__okex_swap = okexswap.SwapAPI(self.__access_key, self.__secret_key, self.__passphrase)
        self.__leverage = leverage or 20
        try:
            self.__okex_swap.set_leverage(leverage=self.__leverage, instrument_id=self.__instrument_id, side=3)
        except Exception as e:
            print("OKEX永续合约设置杠杆倍数失败！请检查账户是否已设置成全仓模式！错误：{}".format(str(e)))

    def get_single_equity(self, instrument_id):
        """
        获取单个合约账户的权益
        :param instrument_id: 例如"TRX-USDT-SWAP"
        :return:返回浮点数
        """
        data = self.__okex_swap.get_coin_account(instrument_id=instrument_id)
        result = float(data["info"]["equity"])
        return result

    def buy(self, price, size, order_type=None):
        if config.backtest != "enabled":  # 实盘模式
            order_type = order_type or 0  # 如果不填order_type,则默认为普通委托
            try:
                result = self.__okex_swap.take_order(self.__instrument_id, 1, price, size, order_type=order_type)
            except Exception as e:
                raise SendOrderError(e)
            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                return {"【交易提醒】下单结果": order_info}
            # 如果订单状态不是"完全成交"或者"失败"
            if config.price_cancellation == "true":  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
                if order_info["订单状态"] == "等待成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['order_id'])
                            state = self.get_order_info(order_id=result['order_id'])
                            if state['订单状态'] == "撤单成功":
                                return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                                size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['order_id'])
                            state = self.get_order_info(order_id=result['order_id'])
                            if state['订单状态'] == "撤单成功":
                                return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                                size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
            if config.time_cancellation == "true":  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
                time.sleep(config.time_cancellation_seconds)
                order_info = self.get_order_info(order_id=result['order_id'])
                if order_info["订单状态"] == "等待成交":
                    try:
                        self.revoke_order(order_id=result['order_id'])
                        state = self.get_order_info(order_id=result['order_id'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    try:
                        self.revoke_order(order_id=result['order_id'])
                        state = self.get_order_info(order_id=result['order_id'])
                        if state['订单状态'] == "撤单成功":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                            size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if config.automatic_cancellation == "true":
                # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
                try:
                    self.revoke_order(order_id=result['order_id'])
                    state = self.get_order_info(order_id=result['order_id'])
                    return {"【交易提醒】下单结果": state}
                except:
                    order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
                return {"【交易提醒】下单结果": order_info}
        else:  # 回测模式
            return "回测模拟下单成功！"

    def sell(self, price, size, order_type=None):
        if config.backtest != "enabled":
            order_type = order_type or 0
            try:
                result = self.__okex_swap.take_order(self.__instrument_id, 3, price, size, order_type=order_type)
            except Exception as e:
                raise SendOrderError(e)
            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                return {"【交易提醒】下单结果": order_info}
            # 如果订单状态不是"完全成交"或者"失败"
            if config.price_cancellation == "true":  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
                if order_info["订单状态"] == "等待成交":
                    if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['order_id'])
                            state = self.get_order_info(order_id=result['order_id'])
                            if state['订单状态'] == "撤单成功":
                                return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                                 size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['order_id'])
                            state = self.get_order_info(order_id=result['order_id'])
                            if state['订单状态'] == "撤单成功":
                                return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                                 size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
            if config.time_cancellation == "true":  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
                time.sleep(config.time_cancellation_seconds)
                order_info = self.get_order_info(order_id=result['order_id'])
                if order_info["订单状态"] == "等待成交":
                    try:
                        self.revoke_order(order_id=result['order_id'])
                        state = self.get_order_info(order_id=result['order_id'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                             size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    try:
                        self.revoke_order(order_id=result['order_id'])
                        state = self.get_order_info(order_id=result['order_id'])
                        if state['订单状态'] == "撤单成功":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                             size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if config.automatic_cancellation == "true":
                # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
                try:
                    self.revoke_order(order_id=result['order_id'])
                    state = self.get_order_info(order_id=result['order_id'])
                    return {"【交易提醒】下单结果": state}
                except:
                    order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
                return {"【交易提醒】下单结果": order_info}
        else:  # 回测模式
            return "回测模拟下单成功！"

    def sellshort(self, price, size, order_type=None):
        if config.backtest != "enabled":
            order_type = order_type or 0
            try:
                result = self.__okex_swap.take_order(self.__instrument_id, 2, price, size, order_type=order_type)
            except Exception as e:
                raise SendOrderError(e)
            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                return {"【交易提醒】下单结果": order_info}
            # 如果订单状态不是"完全成交"或者"失败"
            if config.price_cancellation == "true":  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
                if order_info["订单状态"] == "等待成交":
                    if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['order_id'])
                            state = self.get_order_info(order_id=result['order_id'])
                            if state['订单状态'] == "撤单成功":
                                return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                                      size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['order_id'])
                            state = self.get_order_info(order_id=result['order_id'])
                            if state['订单状态'] == "撤单成功":
                                return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                                      size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
            if config.time_cancellation == "true":  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
                time.sleep(config.time_cancellation_seconds)
                order_info = self.get_order_info(order_id=result['order_id'])
                if order_info["订单状态"] == "等待成交":
                    try:
                        self.revoke_order(order_id=result['order_id'])
                        state = self.get_order_info(order_id=result['order_id'])
                        if state['订单状态'] == "撤单成功":
                            return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                                  size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    try:
                        self.revoke_order(order_id=result['order_id'])
                        state = self.get_order_info(order_id=result['order_id'])
                        if state['订单状态'] == "撤单成功":
                            return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order),
                                                  size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if config.automatic_cancellation == "true":
                # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
                try:
                    self.revoke_order(order_id=result['order_id'])
                    state = self.get_order_info(order_id=result['order_id'])
                    return {"【交易提醒】下单结果": state}
                except:
                    order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
                return {"【交易提醒】下单结果": order_info}
        else:  # 回测模式
            return "回测模拟下单成功！"

    def buytocover(self, price, size, order_type=None):
        if config.backtest != "enabled":
            order_type = order_type or 0
            try:
                result = self.__okex_swap.take_order(self.__instrument_id, 4, price, size, order_type=order_type)
            except Exception as e:
                raise SendOrderError(e)
            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                return {"【交易提醒】下单结果": order_info}
            # 如果订单状态不是"完全成交"或者"失败"
            if config.price_cancellation == "true":  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
                if order_info["订单状态"] == "等待成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['order_id'])
                            state = self.get_order_info(order_id=result['order_id'])
                            if state['订单状态'] == "撤单成功":
                                return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                                       size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                        try:
                            self.revoke_order(order_id=result['order_id'])
                            state = self.get_order_info(order_id=result['order_id'])
                            if state['订单状态'] == "撤单成功":
                                return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                                       size - state["已成交数量"])
                        except:
                            order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                            if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                                return {"【交易提醒】下单结果": order_info}
            if config.time_cancellation == "true":  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
                time.sleep(config.time_cancellation_seconds)
                order_info = self.get_order_info(order_id=result['order_id'])
                if order_info["订单状态"] == "等待成交":
                    try:
                        self.revoke_order(order_id=result['order_id'])
                        state = self.get_order_info(order_id=result['order_id'])
                        if state['订单状态'] == "撤单成功":
                            return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                                   size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
                if order_info["订单状态"] == "部分成交":
                    try:
                        self.revoke_order(order_id=result['order_id'])
                        state = self.get_order_info(order_id=result['order_id'])
                        if state['订单状态'] == "撤单成功":
                            return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order),
                                                   size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if config.automatic_cancellation == "true":
                # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
                try:
                    self.revoke_order(order_id=result['order_id'])
                    state = self.get_order_info(order_id=result['order_id'])
                    return {"【交易提醒】下单结果": state}
                except:
                    order_info = self.get_order_info(order_id=result['order_id'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
                return {"【交易提醒】下单结果": order_info}
        else:  # 回测模式
            return "回测模拟下单成功！"

    def BUY(self, cover_short_price, cover_short_size, open_long_price, open_long_size, order_type=None):
        if config.backtest != "enabled":
            order_type = order_type or 0
            result1 = self.buytocover(cover_short_price, cover_short_size, order_type)
            if "完全成交" in str(result1):
                result2 = self.buy(open_long_price, open_long_size, order_type)
                return {"平仓结果": result1, "开仓结果": result2}
            else:
                return result1
        else:  # 回测模式
            return "回测模拟下单成功！"

    def SELL(self, cover_long_price, cover_long_size, open_short_price, open_short_size, order_type=None):
        if config.backtest != "enabled":
            order_type = order_type or 0
            result1 = self.sell(cover_long_price, cover_long_size, order_type)
            if "完全成交" in str(result1):
                result2 = self.sellshort(open_short_price, open_short_size, order_type)
                return {"平仓结果": result1, "开仓结果": result2}
            else:
                return result1
        else:  # 回测模式
            return "回测模拟下单成功！"

    def get_order_list(self, state, limit):
        receipt = self.__okex_swap.get_order_list(self.__instrument_id, state=state, limit=limit)
        return receipt

    def revoke_order(self, order_id):
        receipt = self.__okex_swap.revoke_order(self.__instrument_id, order_id)
        if receipt['error_code'] == "0":
            return '【交易提醒】撤单成功'
        else:
            return '【交易提醒】撤单失败' + receipt['error_message']

    def get_order_info(self, order_id):
        result = self.__okex_swap.get_order_info(self.__instrument_id, order_id)
        instrument_id = result['instrument_id']
        action = None
        if result['type'] == '1':
            action = "买入开多"
        elif result['type'] == '2':
            action = "卖出开空"
        if result['type'] == '3':
            action = "卖出平多"
        if result['type'] == '4':
            action = "买入平空"

        price = float(result['price_avg'])  # 成交均价
        amount = int(result['filled_qty'])  # 已成交数量
        if instrument_id.split("-")[1] == "usd" or instrument_id.split("-")[1] == "USD":
            turnover = float(result['contract_val']) * int(result['filled_qty'])
        elif instrument_id.split("-")[1] == "usdt" or instrument_id.split("-")[1] == "USDT":
            turnover = round(float(result['contract_val']) * int(result['filled_qty']) * float(result['price_avg']), 2)

        if int(result['state']) == 2:
            dict = {"交易所": "Okex永续合约", "合约ID": instrument_id, "方向": action, "订单状态": "完全成交", "成交均价": price,
                    "已成交数量": amount, "成交金额": turnover}
            return dict
        elif int(result['state']) == -2:
            dict = {"交易所": "Okex永续合约", "合约ID": instrument_id, "方向": action, "订单状态": "失败"}
            return dict
        elif int(result['state']) == -1:
            dict = {"交易所": "Okex永续合约", "合约ID": instrument_id, "方向": action, "订单状态": "撤单成功", "成交均价": price,
                    "已成交数量": amount, "成交金额": turnover}
            return dict
        elif int(result['state']) == 0:
            dict = {"交易所": "Okex永续合约", "合约ID": instrument_id, "方向": action, "订单状态": "等待成交"}
            return dict
        elif int(result['state']) == 1:
            dict = {"交易所": "Okex永续合约", "合约ID": instrument_id, "方向": action, "订单状态": "部分成交", "成交均价": price,
                    "已成交数量": amount, "成交金额": turnover}
            return dict
        elif int(result['state']) == 3:
            dict = {"交易所": "Okex永续合约", "合约ID": instrument_id, "方向": action, "订单状态": "下单中"}
            return dict
        elif int(result['state']) == 4:
            dict = {"交易所": "Okex永续合约", "合约ID": instrument_id, "方向": action, "订单状态": "撤单中"}
            return dict

    def get_kline(self, time_frame):
        if time_frame == "1m" or time_frame == "1M":
            granularity = '60'
        elif time_frame == '3m' or time_frame == "3M":
            granularity = '180'
        elif time_frame == '5m' or time_frame == "5M":
            granularity = '300'
        elif time_frame == '15m' or time_frame == "15M":
            granularity = '900'
        elif time_frame == '30m' or time_frame == "30M":
            granularity = '1800'
        elif time_frame == '1h' or time_frame == "1H":
            granularity = '3600'
        elif time_frame == '2h' or time_frame == "2H":
            granularity = '7200'
        elif time_frame == '4h' or time_frame == "4H":
            granularity = '14400'
        elif time_frame == '6h' or time_frame == "6H":
            granularity = '21600'
        elif time_frame == '12h' or time_frame == "12H":
            granularity = '43200'
        elif time_frame == '1d' or time_frame == "1D":
            granularity = '86400'
        else:
            raise KlineError
        receipt = self.__okex_swap.get_kline(self.__instrument_id, granularity=granularity)
        return receipt

    def get_position(self, mode=None):
        receipt = self.__okex_swap.get_specific_position(self.__instrument_id)
        if mode == "both":
            result = {
                receipt['holding'][0]["side"]: {
                    "price": float(receipt['holding'][0]['avg_cost']),
                    "amount": int(receipt['holding'][0]['position'])
                },
                receipt['holding'][1]["side"]: {
                    "price": float(receipt['holding'][1]['avg_cost']),
                    "amount": int(receipt['holding'][1]['position'])
                }
            }
            return result
        else:
            direction = receipt['holding'][0]['side']
            amount = int(receipt['holding'][0]['position'])
            price = float(receipt['holding'][0]['avg_cost'])
            if amount == 0:
                direction = "none"
            result = {'direction': direction, 'amount': amount, 'price': price}
            return result

    def get_contract_value(self):
        receipt = self.__okex_swap.get_instruments()
        result = {}
        for item in receipt:
            result[item['instrument_id']] = item['contract_val']
        contract_value = float(result[self.__instrument_id])
        return contract_value

    def get_ticker(self):
        receipt = self.__okex_swap.get_specific_ticker(instrument_id=self.__instrument_id)
        return receipt

    def get_depth(self, type=None, size=None):
        """
        OKEX永续合约获取深度数据
        :param type: 如不传参，返回asks和bids；只获取asks传入type="asks"；只获取"bids"传入type="bids"
        :param size: 返回深度档位数量，最多返回200，默认10档
        :return:
        """
        size = size or 10
        response = self.__okex_swap.get_depth(self.__instrument_id, size=size)
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