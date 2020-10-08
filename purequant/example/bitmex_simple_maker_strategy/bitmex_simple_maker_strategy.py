"""
本示例简单实现了Bitmex交易所 XBT/USD交易对买单简单maker策略:
根据当前买1(bid1)和买5(bid5)的价格，计算买1和买5的平均价格(price = (bid1+bid5)/2.0)；
判断当前策略是否已经有挂单，如果没有挂单， 那么直接使用price挂单；如果已经挂单，判断挂单价格是否超出当前bid1和bid5的价格区间，超出则撤单之后重新挂单；
同时对已下单的订单状态进行实时跟踪，当订单状态更新时您可以进行下一步策略（比如记录、通知、对冲...）
"""

import asyncio
from purequant.bitmexws import BITMEXWS
from purequant.config import config
from purequant.logger import logger
from purequant.time import sleep


class Strategy:

    def __init__(self):

        config.loads('config.json')
        self.exchange = BITMEXWS(config.access_key, config.secret_key, instrument_id="XBTUSD", leverage=10, testing=True)

        self.order_no = None  # 创建订单的id
        self.asset = None  # 账户资金

    async def on_event_orderbook_update(self):
        """订单薄更新"""
        await asyncio.sleep(0.1)

        bid1_price = self.exchange.bids[0]  # 买一价格
        bid5_price = self.exchange.bids[4]  # 买五价格

        # 如果已有挂单，且在价格区间内，就不需要执行任何操作
        if self.order_no and bid5_price < self.exchange.open_orders(clOrdID="")[0]["price"] < bid1_price:
            return

        # 如果存在挂单但不在价格区间内，就撤单；如果没有挂单也执行挂单操作
        else:
            if self.order_no:
                self.exchange.revoke_order(self.order_no)
                logger.info("撤销订单:{}".format(self.order_no))
            # 创建新订单
            new_price = (bid1_price + bid5_price) / 2
            price = round(new_price)  # bitmex的XBTUSD合约价格精度限制为下单价格必须是例如10000.0 或10000.5，此处简化处理为取整数
            quantity = 5  # 假设委托数量为5
            # 限价订单
            order_no = self.exchange.generate_uuid()  # 生成机器码作为自己维护的client order id
            self.exchange.buy(price, quantity, clOrdID=order_no)
            logger.info("创建订单:{}".format(order_no))
            sleep(0.5)  # 下单后等待一下，因为websocket获取当前挂单信息也有延迟，防止重复挂单

    async def on_event_asset_update(self):
        """资产更新"""
        await asyncio.sleep(0.1)
        if self.exchange.asset != self.asset:  # 如果资产有变化就打印变化后的资产信息
            logger.info("资产更新:{}".format(self.exchange.asset))
            self.asset = self.exchange.asset

    async def on_event_order_update(self):
        """订单状态更新"""
        await asyncio.sleep(0.1)
        if not self.exchange.open_orders(clOrdID=""):  # 如果订单失败、订单取消、订单完成交易,即当前无挂单
            self.order_no = None
        elif self.exchange.open_orders(clOrdID="") and self.exchange.open_orders(clOrdID="")[0]['clOrdID'] != self.order_no:  # 有挂单且订单有变化
            logger.info("订单更新:{}".format(self.exchange.open_orders(clOrdID="")))  # 订单变动时打印最新的订单信息
            self.order_no = self.exchange.open_orders(clOrdID="")[0]['clOrdID']

    def main(self):  # 入口函数
        tasks = [self.on_event_orderbook_update(), self.on_event_asset_update(), self.on_event_order_update()]
        asyncio.run(asyncio.wait(tasks))


if __name__ == "__main__":
    strategy = Strategy()
    while True:
        strategy.main()