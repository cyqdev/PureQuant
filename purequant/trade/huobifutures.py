"""
火币交割合约
https://huobiapi.github.io/docs/dm/v1/cn/#5ea2e0cde2
Author: Gary-Hertel
Date:   2020/10/27
email: purequant@foxmail.com
"""

import time
from purequant.exchange.huobi import huobi_futures as huobifutures
from purequant.time import ts_to_utc_str
from purequant.config import config
from purequant.exceptions import *


class HUOBIFUTURES:

    def __init__(self, access_key, secret_key, instrument_id, contract_type=None, leverage=None):
        """
        :param access_key:
        :param secret_key:
        :param instrument_id: 'BTC-USD-201225'
        :param contract_type:如不传入此参数，则默认只能交易季度或次季合约
        :param leverage:杠杆倍速，如不填则默认设置为20倍杠杆
        """
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__instrument_id = instrument_id
        self.__huobi_futures = huobifutures.HuobiFutures(self.__access_key, self.__secret_key)
        self.__symbol = self.__instrument_id.split("-")[0]
        self.__contract_code = self.__instrument_id.split("-")[0] + self.__instrument_id.split("-")[2]
        self.__leverage = leverage or 20

        if contract_type is not None:
            self.__contract_type = contract_type
        else:
            if self.__instrument_id.split("-")[2][2:4] == '03' or self.__instrument_id.split("-")[2][2:4] == '09':
                self.__contract_type = "quarter"
            elif self.__instrument_id.split("-")[2][2:4] == '06' or self.__instrument_id.split("-")[2][2:4] == '12':
                self.__contract_type = "next_quarter"
            else:
                self.__contract_type = None
                raise SymbolError("交易所: Huobi 交割合约ID错误，只支持当季与次季合约！")

    def get_single_equity(self, currency):
        """
        获取单个合约账户的权益
        :param currency: 例如"BTC","ETH"...
        :return:返回浮点数
        """
        data = self.__huobi_futures.get_contract_account_info(symbol=currency)
        result =float(data["data"][0]["margin_balance"])
        return result

    def buy(self, price, size, order_type=None):
        """
        火币交割合约下单买入开多
        :param price:   下单价格
        :param size:    下单数量
        :param order_type:  0：限价单
                            1：只做Maker（Post only）
                            2：全部成交或立即取消（FOK）
                            3：立即成交并取消剩余（IOC）
                            4：对手价下单
        :return:
        """
        order_type = order_type or 0
        if order_type == 0:
            order_price_type = 'limit'
        elif order_type == 1:
            order_price_type = "post_only"
        elif order_type == 2:
            order_price_type = "fok"
        elif order_type == 3:
            order_price_type = "ioc"
        elif order_type == 4:
            order_price_type = "opponent"
        else:
            return "【交易提醒】交易所：Huobi 交割合约订单报价类型错误！"
        result = self.__huobi_futures.send_contract_order(symbol=self.__symbol, contract_type=self.__contract_type, contract_code=self.__contract_code,
                        client_order_id='', price=price, volume=size, direction='buy',
                        offset='open', lever_rate=self.__leverage, order_price_type=order_price_type)
        try:
            order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
        except Exception as e:
            raise SendOrderError(result['err_msg'])
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return {"【交易提醒】下单结果": order_info}
        # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id = result['data']['order_id_str'])
                        state = self.get_order_info(order_id = result['data']['order_id_str'])
                        if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id = result['data']['order_id_str'])
                        state = self.get_order_info(order_id = result['data']['order_id_str'])
                        if state['订单状态'] == "部分成交撤销":
                            return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id = result['data']['order_id_str'])
            if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                try:
                    self.revoke_order(order_id = result['data']['order_id_str'])
                    state = self.get_order_info(order_id = result['data']['order_id_str'])
                    if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id = result['data']['order_id_str'])
                    state = self.get_order_info(order_id = result['data']['order_id_str'])
                    if state['订单状态'] == "部分成交撤销":
                        return self.buy(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id = result['data']['order_id_str'])
                state = self.get_order_info(order_id = result['data']['order_id_str'])
                return {"【交易提醒】下单结果": state}
            except:
                order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                    return {"【交易提醒】下单结果": order_info}
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return {"【交易提醒】下单结果": order_info}


    def sell(self, price, size, order_type=None):
        """
        火币交割合约下单卖出平多
        :param price:   下单价格
        :param size:    下单数量
        :param order_type:  0：限价单
                            1：只做Maker（Post only）
                            2：全部成交或立即取消（FOK）
                            3：立即成交并取消剩余（IOC）
                            4：对手价下单
        :return:
        """
        order_type = order_type or 0
        if order_type == 0:
            order_price_type = 'limit'
        elif order_type == 1:
            order_price_type = "post_only"
        elif order_type == 2:
            order_price_type = "fok"
        elif order_type == 3:
            order_price_type = "ioc"
        elif order_type == 4:
            order_price_type = "opponent"
        else:
            return "【交易提醒】交易所: Huobi 交割合约订单报价类型错误！"
        result = self.__huobi_futures.send_contract_order(symbol=self.__symbol, contract_type=self.__contract_type, contract_code=self.__contract_code,
                        client_order_id='', price=price, volume=size, direction='sell',
                        offset='close', lever_rate=self.__leverage, order_price_type=order_price_type)
        try:
            order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
        except Exception as e:
            raise SendOrderError(result['err_msg'])
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return {"【交易提醒】下单结果": order_info}
        # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data']['order_id_str'])
                        state = self.get_order_info(order_id=result['data']['order_id_str'])
                        if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data']['order_id_str'])
                        state = self.get_order_info(order_id=result['data']['order_id_str'])
                        if state['订单状态'] == "部分成交撤销":
                            return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['data']['order_id_str'])
            if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                try:
                    self.revoke_order(order_id=result['data']['order_id_str'])
                    state = self.get_order_info(order_id=result['data']['order_id_str'])
                    if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                        return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id=result['data']['order_id_str'])
                    state = self.get_order_info(order_id=result['data']['order_id_str'])
                    if state['订单状态'] == "部分成交撤销":
                        return self.sell(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['data']['order_id_str'])
                state = self.get_order_info(order_id=result['data']['order_id_str'])
                return {"【交易提醒】下单结果": state}
            except:
                order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                    return {"【交易提醒】下单结果": order_info}
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return {"【交易提醒】下单结果": order_info}

    def buytocover(self, price, size, order_type=None):
        """
        火币交割合约下单买入平空
        :param price:   下单价格
        :param size:    下单数量
        :param order_type:  0：限价单
                            1：只做Maker（Post only）
                            2：全部成交或立即取消（FOK）
                            3：立即成交并取消剩余（IOC）
                            4：对手价下单
        :return:
        """
        order_type = order_type or 0
        if order_type == 0:
            order_price_type = 'limit'
        elif order_type == 1:
            order_price_type = "post_only"
        elif order_type == 2:
            order_price_type = "fok"
        elif order_type == 3:
            order_price_type = "ioc"
        elif order_type == 4:
            order_price_type = "opponent"
        else:
            return "【交易提醒】交易所: Huobi交割合约订单报价类型错误！"
        result = self.__huobi_futures.send_contract_order(symbol=self.__symbol, contract_type=self.__contract_type, contract_code=self.__contract_code,
                        client_order_id='', price=price, volume=size, direction='buy',
                        offset='close', lever_rate=self.__leverage, order_price_type=order_price_type)
        try:
            order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
        except Exception as e:
            raise SendOrderError(result['err_msg'])
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return {"【交易提醒】下单结果": order_info}
        # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data']['order_id_str'])
                        state = self.get_order_info(order_id=result['data']['order_id_str'])
                        if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                            return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) >= price * (1 + config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data']['order_id_str'])
                        state = self.get_order_info(order_id=result['data']['order_id_str'])
                        if state['订单状态'] == "部分成交撤销":
                            return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['data']['order_id_str'])
            if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                try:
                    self.revoke_order(order_id=result['data']['order_id_str'])
                    state = self.get_order_info(order_id=result['data']['order_id_str'])
                    if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                        return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state['已成交数量'])
                except:
                    order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id=result['data']['order_id_str'])
                    state = self.get_order_info(order_id=result['data']['order_id_str'])
                    if state['订单状态'] == "部分成交撤销":
                        return self.buytocover(float(self.get_ticker()['last']) * (1 + config.reissue_order), size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['data']['order_id_str'])
                state = self.get_order_info(order_id=result['data']['order_id_str'])
                return {"【交易提醒】下单结果": state}
            except:
                order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                    return {"【交易提醒】下单结果": order_info}
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return {"【交易提醒】下单结果": order_info}

    def sellshort(self, price, size, order_type=None):
        """
        火币交割合约下单卖出开空
        :param price:   下单价格
        :param size:    下单数量
        :param order_type:  0：限价单
                            1：只做Maker（Post only）
                            2：全部成交或立即取消（FOK）
                            3：立即成交并取消剩余（IOC）
                            4：对手价下单
        :return:
        """
        order_type = order_type or 0
        if order_type == 0:
            order_price_type = 'limit'
        elif order_type == 1:
            order_price_type = "post_only"
        elif order_type == 2:
            order_price_type = "fok"
        elif order_type == 3:
            order_price_type = "ioc"
        elif order_type == 4:
            order_price_type = "opponent"
        else:
            return "【交易提醒】交易所: Huobi 订单报价类型错误！"
        result = self.__huobi_futures.send_contract_order(symbol=self.__symbol, contract_type=self.__contract_type, contract_code=self.__contract_code,
                        client_order_id='', price=price, volume=size, direction='sell',
                        offset='open', lever_rate=self.__leverage, order_price_type=order_price_type)
        try:
            order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
        except Exception as e:
            raise SendOrderError(result['err_msg'])
        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
            return {"【交易提醒】下单结果": order_info}
        # 如果订单状态不是"完全成交"或者"失败"
        if config.price_cancellation:  # 选择了价格撤单时，如果最新价超过委托价一定幅度，撤单重发，返回下单结果
            if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data']['order_id_str'])
                        state = self.get_order_info(order_id=result['data']['order_id_str'])
                        if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                            return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state['已成交数量'])
                    except:
                        order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                if float(self.get_ticker()['last']) <= price * (1 - config.price_cancellation_amplitude):
                    try:
                        self.revoke_order(order_id=result['data']['order_id_str'])
                        state = self.get_order_info(order_id=result['data']['order_id_str'])
                        if state['订单状态'] == "部分成交撤销":
                            return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                    except:
                        order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                        if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                            return {"【交易提醒】下单结果": order_info}
        if config.time_cancellation:  # 选择了时间撤单时，如果委托单发出多少秒后不成交，撤单重发，直至完全成交，返回成交结果
            time.sleep(config.time_cancellation_seconds)
            order_info = self.get_order_info(order_id=result['data']['order_id_str'])
            if order_info["订单状态"] == "准备提交" or order_info["订单状态"] == "已提交":
                try:
                    self.revoke_order(order_id=result['data']['order_id_str'])
                    state = self.get_order_info(order_id=result['data']['order_id_str'])
                    if state['订单状态'] == "撤单成功" or state['订单状态'] == "部分成交撤销":
                        return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
            if order_info["订单状态"] == "部分成交":
                try:
                    self.revoke_order(order_id=result['data']['order_id_str'])
                    state = self.get_order_info(order_id=result['data']['order_id_str'])
                    if state['订单状态'] == "部分成交撤销":
                        return self.sellshort(float(self.get_ticker()['last']) * (1 - config.reissue_order), size - state["已成交数量"])
                except:
                    order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                    if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                        return {"【交易提醒】下单结果": order_info}
        if config.automatic_cancellation:
            # 如果订单未完全成交，且未设置价格撤单和时间撤单，且设置了自动撤单，就自动撤单并返回下单结果与撤单结果
            try:
                self.revoke_order(order_id=result['data']['order_id_str'])
                state = self.get_order_info(order_id=result['data']['order_id_str'])
                return {"【交易提醒】下单结果": state}
            except:
                order_info = self.get_order_info(order_id=result['data']['order_id_str'])  # 下单后查询一次订单状态
                if order_info["订单状态"] == "完全成交" or order_info["订单状态"] == "失败 ":  # 如果订单状态为"完全成交"或者"失败"，返回结果
                    return {"【交易提醒】下单结果": order_info}
        else:  # 未启用交易助手时，下单并查询订单状态后直接返回下单结果
            return {"【交易提醒】下单结果": order_info}

    def BUY(self, cover_short_price, cover_short_size, open_long_price, open_long_size, order_type=None):
        """火币交割合约平空开多"""
        receipt1 = self.buytocover(cover_short_price, cover_short_size, order_type)
        if "完全成交" in str(receipt1):
            receipt2 = self.buy(open_long_price, open_long_size, order_type)
            return {"平仓结果": receipt1, "开仓结果": receipt2}
        else:
            return receipt1

    def SELL(self, cover_long_price, cover_long_size, open_short_price, open_short_size, order_type=None):
        """火币交割合约平多开空"""
        receipt1 = self.sell(cover_long_price, cover_long_size, order_type)
        if "完全成交" in str(receipt1):
            receipt2 = self.sellshort(open_short_price, open_short_size, order_type)
            return {"平仓结果": receipt1, "开仓结果": receipt2}
        else:
            return receipt1

    def revoke_order(self, order_id):
        receipt = self.__huobi_futures.cancel_contract_order(self.__symbol, order_id)
        if receipt['status'] == "ok":
            return '【交易提醒】交易所: Huobi 撤单成功'
        else:
            return '【交易提醒】交易所: Huobi 撤单失败' + receipt['data']['errors'][0]['err_msg']

    def get_order_info(self, order_id):
        result = self.__huobi_futures.get_contract_order_info(self.__symbol, order_id)
        instrument_id = result['data'][0]['contract_code']
        state = int(result['data'][0]['status'])
        avg_price = result['data'][0]['trade_avg_price']
        amount = result['data'][0]['trade_volume']
        turnover = result['data'][0]['trade_turnover']
        if result['data'][0]['direction'] == "buy" and result['data'][0]['offset'] == "open":
            action = "买入开多"
        elif result['data'][0]['direction'] == "buy" and result['data'][0]['offset'] == "close":
            action = "买入平空"
        elif result['data'][0]['direction'] == "sell" and result['data'][0]['offset'] == "open":
            action = "卖出开空"
        elif result['data'][0]['direction'] == "sell" and result['data'][0]['offset'] == "close":
            action = "卖出平多"
        else:
            action = "交易方向错误！"
        if state == 6:
            dict = {"交易所": "Huobi交割合约", "合约ID": instrument_id, "方向": action, "订单状态": "完全成交",
                    "成交均价": avg_price, "已成交数量": amount, "成交金额": turnover}
            return dict
        elif state == 1:
            dict = {"交易所": "Huobi交割合约", "合约ID": instrument_id, "方向": action, "订单状态": "准备提交"}
            return dict
        elif state == 7:
            dict = {"交易所": "Huobi交割合约", "合约ID": instrument_id, "方向": action, "订单状态": "撤单成功",
                    "成交均价": avg_price, "已成交数量": amount, "成交金额": turnover}
            return dict
        elif state == 2:
            dict = {"交易所": "Huobi交割合约", "合约ID": instrument_id, "方向": action, "订单状态": "准备提交"}
            return dict
        elif state == 4:
            dict = {"交易所": "Huobi交割合约", "合约ID": instrument_id, "方向": action, "订单状态": "部分成交",
                    "成交均价": avg_price, "已成交数量": amount, "成交金额": turnover}
            return dict
        elif state == 3:
            dict = {"交易所": "Huobi交割合约", "合约ID": instrument_id, "方向": action, "订单状态": "已提交"}
            return dict
        elif state == 11:
            dict = {"交易所": "Huobi交割合约", "合约ID": instrument_id, "方向": action, "订单状态": "撤单中"}
            return dict
        elif state == 5:
            dict = {"交易所": "Huobi交割合约", "合约ID": instrument_id, "方向": action, "订单状态": "部分成交撤销",
                    "成交均价": avg_price, "已成交数量": amount, "成交金额": turnover}
            return dict

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
            raise KlineError("k线周期错误，k线周期只能是【1m, 5m, 15m, 30m, 1h, 4h, 1d】!")
        records = self.__huobi_futures.get_contract_kline(symbol=self.__contract_code, period=period)['data']
        list = []
        for item in records:
            item = [ts_to_utc_str(item['id']), item['open'], item['high'], item['low'], item['close'], item['vol'], round(item['amount'], 2)]
            list.append(item)
        list.reverse()
        return list

    def get_position(self, mode=None):
        receipt = self.__huobi_futures.get_contract_position_info(self.__symbol)
        if mode == "both":
            if receipt['data'] == []:
                return {"long": {"price": 0, "amount": 0}, "short": {"price": 0, "amount": 0}}
            elif len(receipt['data']) == 1:
                if receipt['data'][0]['direction'] == "buy":
                    return {"long": {"price": receipt['data'][0]['cost_hold'], "amount": receipt['data'][0]['volume']}, "short": {"price": 0, "amount": 0}}
                elif receipt['data'][0]['direction'] == "sell":
                    return {"short": {"price": receipt['data'][0]['cost_hold'], "amount": receipt['data'][0]['volume']}, "long": {"price": 0, "amount": 0}}
            elif len(receipt['data']) == 2:
                return {
                    "long": {
                        "price": receipt['data'][0]['cost_hold'], "amount": receipt['data'][0]['volume']
                    },
                        "short": {
                            "price": receipt['data'][1]['cost_hold'], "amount": receipt['data'][1]['volume']
                        }
                }
        else:
            if receipt['data'] != []:
                direction = receipt['data'][0]['direction']
                amount = receipt['data'][0]['volume']
                price = receipt['data'][0]['cost_hold']
                if amount > 0 and direction == "buy":
                    dict = {'direction': 'long', 'amount': amount, 'price': price}
                    return dict
                elif amount > 0 and direction == "sell":
                    dict = {'direction': 'short', 'amount': amount, 'price': price}
                    return dict
            else:
                dict = {'direction': 'none', 'amount': 0, 'price': 0.0}
                return dict

    def get_ticker(self):
        receipt = self.__huobi_futures.get_contract_market_merged(self.__contract_code)
        last = receipt['tick']['close']
        return {"last": last}

    def get_contract_value(self):
        receipt = self.__huobi_futures.get_contract_info()
        for item in receipt['data']:
            if item["contract_code"] == self.__contract_code:
                contract_value = item["contract_size"]
                return contract_value

    def get_depth(self, type=None):
        """
        火币交割合约获取深度数据
        :param type: 如不传参，返回asks和bids；只获取asks传入type="asks"；只获取"bids"传入type="bids"
        :return:返回20档深度数据
        """
        response = self.__huobi_futures.get_contract_depth(self.__contract_code, type="step0")
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