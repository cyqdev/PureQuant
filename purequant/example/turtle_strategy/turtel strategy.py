"""
海龟交易策略
此示例策略适用于OKEX币本位合约，
可根据自己需求自行修改

Author: eternal ranger
Date:   2020/09/17
email: interstella.ranger2020@gmail.com
"""
from purequant.trade import OKEXFUTURES
from purequant.indicators import INDICATORS
from purequant.market import MARKET
from purequant.position import POSITION
from purequant.logger import logger
from purequant.time import *
from purequant.config import config
from purequant.push import push
from purequant.storage import storage

class Strategy:

    def __init__(self, instrument_id, time_frame, start_asset):     # 策略初始化时需传入合约id、k线周期、初始资金参数
        config.loads("config.json")     # 载入配置文件
        self.instrument_id = instrument_id  # 合约id
        self.time_frame = time_frame    # k线周期
        self.exchange = OKEXFUTURES(config.access_key, config.secret_key, config.passphrase, self.instrument_id, leverage=20)   # 初始化交易所
        self.market = MARKET(self.exchange, self.instrument_id, self.time_frame)    # 初始化market
        self.position = POSITION(self.exchange, self.instrument_id, self.time_frame)    # 初始化position
        self.indicators = INDICATORS(self.exchange, self.instrument_id, self.time_frame)    # 初始化indicators
        self.database = "回测"  # 如从purequant服务器的数据库上获取历史k线数据进行回测，必须为"回测"
        self.datasheet = self.instrument_id.split("-")[0].lower() + "_" + time_frame    # 数据表
        if config.first_run == "true":  # 程序第一次启动时保存数据，实盘时如策略中止再重启时，可以将配置文件中的first_run改成"false"，程序再次启动会直接读取数据库中保存的数据
            storage.mysql_save_strategy_run_info(self.database, self.datasheet, get_localtime(),
                                                 "none", 0, 0, 0, 0, "none", 0, 0, 0, start_asset)
        # 读取数据库中保存的总资金、总盈亏数据
        self.total_asset = storage.read_mysql_datas(0, self.database, self.datasheet, "总资金", ">")[-1][-1]
        self.total_profit = storage.read_mysql_datas(0, self.database, self.datasheet, "总资金", ">")[-1][-2]  # 策略总盈亏
        # 一些策略参数
        self.contract_value = self.market.contract_value()  # 合约面值
        self.ATRLength = 20    # 平均波动周期
        self.boLength = 20  # 短周期 BreakOut Length
        self.fsLength = 55  # 长周期 FailSafe Length
        self.teLength = 10   # 离市周期 Trailing Exit Length
        self.LastProfitableTradeFilter = 1   # 使用入市过滤条件
        self.PreBreakoutFailure = False  # 前一次是否突破失败
        self.CurrentEntries = 0  # 当前持仓的开仓次数
        self.counter = 0    # 计数器，用以控制单根bar最大交易次数
        print("{} {} 海龟交易策略已启动！".format(get_localtime(), instrument_id))  # 程序启动时打印提示信息

    def begin_trade(self, kline=None):  # 实盘时从交易所实时获取k线数据，回测时传入自定义的kline
        try:
            # 如果k线数据不够长就返回
            if self.indicators.CurrentBar(kline=kline) < self.fsLength:
                return
            # 非回测模式下时间戳就是当前本地时间
            timestamp = ts_to_datetime_str(utctime_str_to_ts(kline[-1][0])) if kline else get_localtime()
            # k线更新时计数器归零
            if self.indicators.BarUpdate(kline=kline):
                self.counter = 0
            AvgTR = self.indicators.ATR(self.ATRLength, kline=kline)     # 计算真实波幅
            N = float(AvgTR[-2])   # N值为前一根bar上的ATR值，需将numpy.float64数据类型转换为float类型，下面的转换同理
            Units = int(self.total_asset / self.contract_value / 5)    # 每一份头寸大小为总资金的20%
            """计算短周期唐奇安通道"""
            # 唐奇安通道上轨，延后1个Bar
            DonchianHi = float(self.indicators.HIGHEST(self.boLength, kline=kline)[-2])
            # 唐奇安通道下轨，延后1个Bar
            DonchianLo = float(self.indicators.LOWEST(self.boLength, kline=kline)[-2])
            """计算长周期唐奇安通道"""
            # 唐奇安通道上轨，延后1个Bar，长周期
            fsDonchianHi = float(self.indicators.HIGHEST(self.fsLength, kline=kline)[-2])
            # 唐奇安通道下轨，延后1个Bar，长周期
            fsDonchianLo = float(self.indicators.LOWEST(self.fsLength, kline=kline)[-2])
            """计算止盈唐奇安通道"""
            # 离市时判断需要的N周期最低价
            ExitLowestPrice = float(self.indicators.LOWEST(self.teLength, kline=kline)[-2])
            # 离市时判断需要的N周期最高价
            ExitHighestPrice = float(self.indicators.HIGHEST(self.teLength, kline=kline)[-2])
            # 当不使用过滤条件，或者使用过滤条件且条件PreBreakoutFailure为True时，短周期开仓
            if self.indicators.CurrentBar(kline=kline) >= self.boLength and self.position.amount() == 0 and (self.LastProfitableTradeFilter != 1 or self.PreBreakoutFailure == False) and self.counter < 1:
                if self.market.high(-1, kline=kline) >= DonchianHi:  # 突破了短周期唐奇安通道上轨
                    price = DonchianHi  # 开多价格为短周期唐奇安通道上轨
                    amount = Units  # 开多数量为Units
                    receipt = self.exchange.buy(price, amount)  # 开多
                    push(receipt)   # 推送下单结果
                    self.CurrentEntries += 1    # 记录一次开仓次数
                    self.PreBreakoutFailure = False  # 将标识重置为默认值，根据离场时的盈亏情况再修改
                    storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp, "买入开多",
                                                         price, amount, amount * self.contract_value, price,
                                                         "long", amount, 0, self.total_profit,
                                                         self.total_asset)  # 将信息保存至数据库
                    self.counter += 1   # 计数器加1
                if self.market.low(-1, kline=kline) <= DonchianLo: # 突破了短周期唐奇安通道下轨
                    price = DonchianLo  # 开空价格为DonchianLo
                    amount = Units  # 开空数量为Units
                    receipt = self.exchange.sellshort(price, amount)    # 开空
                    push(receipt)   # 推送下单结果
                    self.CurrentEntries += 1    # 记录一次开仓次数
                    self.PreBreakoutFailure = False     # 将标识重置为默认值，根据离场时的盈亏情况再修改
                    storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp, "卖出开空",
                                                         price, amount, amount * self.contract_value, price,
                                                         "short", amount, 0, self.total_profit, self.total_asset)   # 保存信息至数据库
                    self.counter += 1   # 计数器加1
            # 长周期突破开仓，其他逻辑和短周期突破开仓一样。
            if self.indicators.CurrentBar(kline=kline) >= self.fsLength and self.position.amount() == 0 and self.counter < 1:
                if self.market.high(-1, kline=kline) >= fsDonchianHi:   # 突破了长周期唐奇安通道上轨
                    price = fsDonchianHi    # 开多价格为长周期唐奇安通道上轨值
                    amount = Units  # 数量为Units
                    receipt = self.exchange.buy(price, amount)  # 下单并返回下单结果
                    push(receipt)   # 推送下单结果
                    self.CurrentEntries += 1    # 记录一次开仓次数
                    self.PreBreakoutFailure = False     # 将标识重置为默认值
                    storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp, "买入开多",
                                                         price, amount, amount * self.contract_value, price,
                                                         "long", amount, 0, self.total_profit,
                                                         self.total_asset)  # 将信息保存至数据库
                    self.counter += 1   # 计数器加1
                if self.market.low(-1, kline=kline) <= fsDonchianLo:    # 突破长周期唐奇安通道下轨
                    price = fsDonchianLo    # 开空价格为长周期唐奇安通道下轨值
                    amount = Units  # 开空数量为Units
                    receipt = self.exchange.sellshort(price, amount)    # 下单并返回下单结果
                    push(receipt)  # 推送下单结果
                    self.CurrentEntries += 1  # 记录一次开仓次数
                    self.PreBreakoutFailure = False   # 将标识重置为默认值
                    storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp, "卖出开空",
                                                         price, amount, amount * self.contract_value, price,
                                                         "short", amount, 0, self.total_profit, self.total_asset)
                    self.counter += 1   # 计数器加1
            # 止盈、加仓和止损
            if self.position.direction() == "long" and self.counter < 1:     # 持多仓的情况。回测时是一根k线上整个策略从上至下运行一次，所以在此处设置计数器过滤
                if self.market.low(-1, kline=kline) <= ExitLowestPrice:    # 跌破止盈价
                    profit = self.position.coverlong_profit(last=ExitLowestPrice, market_type="usd_contract")   # 平仓前计算利润，传入最新价以及计算盈利的合约类型
                    self.total_profit += profit  # 计算经过本次盈亏后的总利润
                    self.total_asset += profit  # 计算经过本次盈亏后的总资金
                    price = ExitLowestPrice     # 平多价格为ExitLowestPrice
                    amount = self.position.amount()     # 数量为当前持仓数量
                    receipt = self.exchange.sell(price, amount)    # 平所有多单仓位
                    push(receipt)   # 推送下单结果
                    storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp, "卖出平多",
                                                         price, amount, amount * self.contract_value,
                                                         0, "none", 0, profit, self.total_profit, self.total_asset)
                    self.counter += 1   # 计数器加1
                    self.CurrentEntries = 0   # 平仓后将开仓次数还原为0
                else:
                    # 加仓指令
                    '''以最高价为标准，判断是否能加仓，并限制最大加仓次数
                       如果价格过前次开仓价格1/2N,则直接加仓
                    '''
                    while self.market.high(-1, kline=kline) >= (self.position.price() + 0.5 * N) and (self.CurrentEntries <= 4):
                        price = self.position.price() + 0.5 * N     # 加仓的开仓价格为持仓价格+0.5 * N
                        amount = Units  # 数量为Units
                        storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp, "多头加仓",
                                                             price, amount, amount * self.contract_value,
                                                             (self.position.price() + price) / 2,
                                                             "long", self.position.amount() + amount,
                                                             0, self.total_profit, self.total_asset)
                        receipt = self.exchange.buy(price, amount)
                        push(receipt)
                        self.CurrentEntries += 1
                    # 止损指令
                    if self.market.low(-1, kline=kline) <= (self.position.price() - 2 * N):   # 如果回落大于最后下单价格-2n，就止损
                        profit = self.position.coverlong_profit(last=self.position.price() - 2 * N, market_type="usd_contract")
                        self.total_profit += profit  # 计算经过本次盈亏后的总利润
                        self.total_asset += profit  # 计算经过本次盈亏后的总资金
                        price = self.position.price() - 2 * N
                        amount = self.position.amount()
                        receipt = self.exchange.sell(price, amount)  # 全部止损平仓
                        push(receipt)
                        self.PreBreakoutFailure = True  # 记录为突破失败，下次交易将使用长周期开仓
                        storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp, "卖出止损",
                                                             price, amount, amount * self.contract_value,
                                                             0, "none", 0, profit, self.total_profit, self.total_asset)
                        self.counter += 1
                        self.CurrentEntries = 0  # 平仓后将开仓次数还原为0
            elif self.position.direction() == "short" and self.counter < 1: # 持空头的情况，除方向以外，其他逻辑和上面持多仓的一致
                if self.market.high(-1, kline=kline) >= ExitHighestPrice:
                    profit = self.position.covershort_profit(last=ExitHighestPrice, market_type="usd_contract")
                    self.total_profit += profit
                    self.total_asset += profit
                    price = ExitHighestPrice
                    amount = self.position.amount()
                    receipt = self.exchange.buytocover(price, amount)
                    push(receipt)
                    storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp,
                                                         "买入平空", price, amount, amount * self.contract_value,
                                                         0, "none", 0, profit, self.total_profit, self.total_asset)
                    self.counter += 1
                    self.CurrentEntries = 0  # 平仓后将开仓次数还原为0
                else:
                    while self.market.low(-1, kline=kline) <= (self.position.price() - 0.5 * N) and (self.CurrentEntries <= 4):
                        price = self.position.price() - 0.5 * N
                        amount = Units
                        storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp, "空头加仓",
                                                             price, amount, amount * self.contract_value,
                                                             (self.position.price() + price) / 2,
                                                             "short", self.position.amount() + amount,
                                                             0, self.total_profit, self.total_asset)
                        receipt = self.exchange.sellshort(self.position.price() - 0.5 * N, Units)
                        push(receipt)
                        self.CurrentEntries += 1
                    if self.market.high(-1, kline=kline) >= (self.position.price() + 2 * N):
                        profit = self.position.covershort_profit(last=self.position.price() + 2 * N, market_type="usd_contract")
                        self.total_profit += profit
                        self.total_asset += profit
                        price = self.position.price() + 2 * N
                        amount = self.position.amount()
                        receipt = self.exchange.buytocover(price, amount)
                        push(receipt)
                        self.PreBreakoutFailure = True
                        storage.mysql_save_strategy_run_info(self.database, self.datasheet, timestamp,
                                                             "买入止损", price, amount, amount * self.contract_value,
                                                             0, "none", 0, profit, self.total_profit, self.total_asset)
                        self.counter += 1
                        self.CurrentEntries = 0  # 平仓后将开仓次数还原为0
        except:
            logger.error()

if __name__ == "__main__":

    instrument_id = "TRX-USD-201225"
    time_frame = "3m"
    strategy = Strategy(instrument_id, time_frame, start_asset=60)

    if config.backtest == "enabled":  # 回测模式
        print("正在回测，可能需要一段时间，请稍后...")
        start_time = get_cur_timestamp()
        records = []
        data = storage.read_purequant_server_datas(instrument_id.split("-")[0].lower() + "_" + time_frame)
        for k in data:
            records.append(k)
            strategy.begin_trade(kline=records)
        cost_time = get_cur_timestamp() - start_time
        print("回测用时{}秒，结果已保存至mysql数据库！".format(cost_time))
    else:  # 实盘模式
        while True:  # 循环运行begin_trade函数
            strategy.begin_trade()
            sleep(3)  # 休眠3秒，防止请求超出交易所频率限制