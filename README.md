PureQuant

------

PureQuant是一套使用`Python`语言开发的`数字货币程序化交易开源框架`，致力于为数字货币行业的投资者提供一个快速、简便地编写自己的交易系统的工具，希望使用者能够通过使用系统，建立并优化自己的交易思想，形成自己的交易策略。PureQuant旨在化繁为简，帮助大家快速部署自己的交易系统。不用担心没有编程基础，因为PureQuant有详细的使用文档以及视频教程，在使用过程中如果遇到问题，可以随时在PureQuant交易论坛发帖。

目前支持的交易所：bitmex  okex  币安  火币 bitcoke

现货交易只要ccxt支持的交易所都可以，并且兼容指标模块。

## 框架依赖

+ **运行环境**

  python3.7或以上版本

+ **MySQL数据库(可选)**，**MongoDB数据库(可选)**

  数据存储
  

## 安装

+ 使用 `pip` 可以简单方便安装:

```python
pip install purequant
```

## 项目结构

+ 推荐创建如下结构的文件及文件夹

```
ProjectName
    |----- config.json
    |----- strategy.py
```

## 有任何问题，欢迎联系

+ 网站：http://purequant.cloud

+ 论坛：http://purequant.club

  在使用PureQuant的过程中，如有任何疑问或建议，请在论坛上发帖交流。

+ 框架使用视频教程：http://m.study.163.com/provider/400000000697049/index.htm?share=2&shareId=400000000697049


------



## 下单交易

`实盘时会真实下单，回测模式下返回模拟下单成功的提示信息`

```python
from purequant.trade import BINANCESPOT  # 从trade模块中导入币安现货
from purequant.config import config  # 导入配置模块

config.loads(config_file) 	# 载入配置文件
exchange = BINANCESPOT(config.access_key, config.secret_key, instrument_id) # 实例化交易所
```

### 买入开多

```python
exchange.buy(price, amount)  
```

### 卖出平多

```python
exchange.sell(price, amount)  
```

### 卖出开空

```python
exchange.sellshort(price, amount)  
```

### 买入平空

```python
exchange.buytocover(price, amount)  
```

### 平多开空

```python
exchange.SELL(平多价格，平多数量，开空价格，开空数量)
```

### 平空开多

```python
exchange.BUY(平空价格，平空数量，开多价格，开多数量)
```

下单后无论是否完全成交，返回下单结果。

```python
info = exchange.buy(0.01784, 1)
print(info)

>>>【交易提醒】下单结果：{'合约ID': 'TRX-USDT-SWAP', '方向': '卖出平多', '订单状态': '完全成交', '成交均价': '0.01784', '数量': '1', '成交金额': 17.84} 
```

------



## 交易助手

使用交易助手可以实现自动撤单以及撤单后重发委托直至完全成交的功能。

```json
{
"ASSISTANT": {
        "automatic_cancellation": "false",
        "reissue_order": "0.0%",
        "price_cancellation": "false",
        "amplitude": "1%",
        "time_cancellation": "false",
        "seconds": 10
    }
}
```

### 自动撤单

将配置文件中的`automatic_cancellation`设置为`true`，即可实现下单后如订单未完全成交就自动撤单。

### 价格撤单

将配置文件中的`price_cancellation`设置为 `true`,当最新价超过委托价一定百分比（`amplitude`），则自动撤单，并以最新价（可以使用超价下单，设置`reissue_order`即可）重发委托。

### 时间撤单

将配置文件中的`time_cancellation`设置为`true`,若超时未成交（`seconds`），则自动撤单，并以最新价（可以使用超价下单，设置`reissue_order`即可）重发委托直至完全成交。

### 交易助手使用说明

1.若未启用交易助手，则下单后自动查询订单状态然后返回订单结果。

2.若只启用了自动撤单功能，下单后如果订单未完全成交，则自动撤单，返回下单结果。

3.价格撤单功能只会在最新价超过委托价一定百分比时去自动撤单然后以最新价下单，不能实现达到完全成交的作用。

4.时间撤单功能可以一直重发委托直至完全成交。

5.建议启用交易助手的三个功能，参数可以按需自行设置。

6.订单状态为`部分成交`的情况下，只会返回最后一笔成交的订单状态。

------



## 智能渠道推送

`实盘时会实时推送信息，回测模式下不会推送信息`

```python
from purequant.push import push
from purequant.config import config 

config.loads(filename)
```

配置文件是一个名为`config.json`的文件，只需将其中参数修改为自己的即可：

```json
{
    "PUSH": {
        "sendmail": "false",
        "dingtalk": "true",
        "twilio": "false"
    },
    "DINGTALK": {
        "ding_talk_api": "https://oapi.dingtalk.com/robot/send?access_token=d3a368908a7db882cd3f6afcccca302e51a1c9"
    },
    "TWILIO": {
        "accountSID" : "AC97a11fcc5ede559cd39061ad140f",
        "authToken" : "3616b6ced8e250232ca2fa4aa559",
        "myNumber" : "+8613712345678",
        "twilio_Number" : "+12058946789"
    },
    "SENDMAIL": {
        "from_addr" : "123456789@qq.com",
        "password" : "xqkwtrsfqwcjgjjgh",
        "to_addr" : "abc@icloud.com",
        "smtp_server" : "smtp.qq.com",
        "port":587
    }
}
```

### 集成推送信息

```python
push("要推送的信息内容")
```

在配置文件中，`PUSH`中的对应参数若设置为`true`，使用`push()`时则会推送消息至相应智能渠道。

twilio所能推送的短信字节过短，因此只能用来发送简短信息，在交易时建议将此项设为"false"。

钉钉推送时会自动@群里的所有人，并且会在当前策略文件目录下自动创建一个名为'dingtalk.text'的文件，其中记录了钉钉消息的发送时间、状态以及具体的发送内容。

------



## 获取持仓信息

`实盘时会实时从交易所获取真实的账户持仓信息，回测模式下是从数据库中读取回测过程中保存的持仓信息`

```python
from purequant.position import POSITION		# 导入持仓模块

position = POSITION(exchange, instrument_id, time_frame)	# 实例化POSITION
```

### 当前持仓方向

```python
direction = position.direction()
# 若当前无持仓，返回"none"
# 若当前持多头，返回"long"
# 若当前持空头，返回"short"
```

### 当前持仓数量

```python
amount = position.amount()
```

### 当前持仓均价

```python
price = position.price()
```

注：

1. 支持双向持仓信息查询。如果是单向持仓，使用原来的position.amount()、position.price()、position.direction()查询持仓信息。

   如果是双向持仓，获取多头持仓数量与均价：

   ```python
   position.amount(mode="both", side="long")
   position.price(mode="both", side="long") 
   ```

   获取空头持仓数量与均价：

   ```python
   position.amount(mode="both", side="short")
   position.price(mode="both", side="short")
   ```

2. 币安合约支持双向持仓模式，在初始化交易所时传入参数即可：

   ```python
   exchange = BINANCEFUTURES(api_key, secret_key, instrument_id, leverage=10, position_side="both")
   
   ```

------



## 获取行情信息

`实盘时实时获取交易所的行情数据，回测时是获取PureQuant服务器上数据库中的历史数据`

```python
from purequant.market import MARKET

market = MARKET(exchange, instrument_id, time_frame)
```

### 最新成交价

```python
last = market.last()
```

### 开盘价

```python
open = market.open()

market.open(-1)  # 获取当根bar上的开盘价
market.open(-2)  # 获取上根bar上的开盘价
market.open(0)  # 获取最远一根bar上的开盘价
```

### 最高价

```python
high = market.high()

market.high(-1)  # 获取当根bar上的最高价
market.high(-2)  # 获取上根bar上的最高价
market.high(0)  # 获取最远一根bar上的最高价
```

### 最低价

```python
low = market.low()

market.low(-1)  # 获取当根bar上的最低价
market.low(-2)  # 获取上根bar上的最低价
market.low(0)  # 获取最远一根bar上的最低价
```

### 收盘价

```python
close = market.close()

market.close(-1)  # 获取当根bar上的收盘价
market.close(-2)  # 获取上根bar上的收盘价
market.close(0)  # 获取最远一根bar上的收盘价
```

### 合约面值

```python
# 获取合约面值，返回结果为计价货币数量，数据类型为整型数字。
# 如一张币本位BTC合约面值为100美元，一张USDT本位BTC合约面值为0.01个BTC
contract_value = market.contract_value()
```

### 卖盘订单簿

```python
asks = market.asks()
```

### 买盘订单簿

```python
bids = market.bids()
```

------



## 交易指标

`实盘时实时获取交易所的行情数据，回测时是获取根据PureQuant服务器上数据库中的历史数据进行计算，具体方法可参阅示例的双均线策略`

调用时需先导入indicators模块：

```python
from purequant.indicators import INDICATORS
```

要传入的参数中都有platform、instrument_id、time_frame，所以需要声明这几个变量，并且初始化indicators

```python
from purequant.trade import OKEXFUTURES
# k线是公共数据，api传入空的字符串即可
instrument_id = "BTC-USDT-201225"
time_frame = "1d"
exchange = OKEXFUTURES("", "", "", instrument_id)


indicators = INDICATORS(exchange, instrument_id, time_frame)
```

### ATR，平均真实波幅

返回一个一维数组

```python
indicators.ATR(14)
```

```python
# 获取最新一根bar上的atr
atr = indicators.ATR(14)[-1]
```

ATR已检验，计算出的值与huobi交易所k线图上所显示的一致。

### BarUpdate，判断k线是否更新

如果更新，返回值为True，否则为False

```python
indicators.BarUpdate()
```

```python
# 调用方式
if indicators.BarUpdate():
    print("k线更新")
```

BarUpdate已检验，k线更新时，其值会变成True。

### BOLL，布林线指标

返回一个字典 {"upperband": 上轨数组， "middleband": 中轨数组， "lowerband": 下轨数组}

```python
indicators.BOLL(20)
```

```python
# 获取最新一根bar上的上、中、下轨值
upperband = indicators.BOLL(20)['upperband'][-1]
middleband = indicators.BOLL(20)['middleband'][-1]
lowerband = indicators.BOLL(20)['lowerband'][-1]
```

BOLL已检验，与okex及huobi上k线图上所显示一致。

### CurrentBar，获取bar的长度

返回一个整型数字

```python
indicators.CurrentBar()
```

```python
# 获取交易所返回k线数据的长度
kline_length = indicators.CurrentBar()
```

CurrentBar已检验，与FMZ量化所计算出的值一致。

### HIGHEST，周期最高价

返回一个一维数组

```python
indicators.HIGHEST(30)
```

```python
# 获取最新一根bar上的最高价
highest = indicators.HIGHEST(30)[-1]
```

HIGHEST已检验，与FMZ量化所计算出的值一致。

### MA，移动平均线

返回一个一维数组

```python
indicators.MA(15)
```

```python
# 获取最新一根bar上的ma
ma15 = indicators.MA(15)[-1]
```

MA已检验，与okex交易所k线图上所显示一致。

### MACD，指数平滑异同平均线

返回一个字典  {'DIF': DIF数组, 'DEA': DEA数组, 'MACD': MACD数组}

```python
indicators.MACD(12, 26, 9)
```

```python
# 获取最新一根bar上的DIF、DEA、MACD
DIF = indicators.MACD(12, 26, 9)['DIF'][-1]
DEA = indicators.MACD(12, 26, 9)['DEA'][-1]
MACD = indicators.MACD(12, 26, 9)['MACD'][-1]
```

MACD已检验，与okex交易所k线图上所显示一致。

### EMA，指数平均数

返回一个一维数组

```python
indicators.EMA(9)
```

```python
# 获取最新一根bar上的ema
ema = indicators.EMA(9)[-1]
```

EMA已检验，与okex交易所k线图上所显示一致。

### KAMA ，考夫曼自适应移动平均线

返回一个一维数组

```python
indicators.EMA(30)
```

```python
# 获取最新一根bar上的kama
kama = indicators.KAMA(30)[-1]
```

KAMA已检验，与turtle quant程序化交易软件所计算出的值一致。

### KDJ，随机指标

返回一个字典，{'k': k值数组， 'd': d值数组}

```python
indicators.KDJ(9 ,3, 3)
```

```python
# 获取最新一根bar上的k和d
k = indicators.KDJ(9 ,3, 3)['k'][-1]
d = indicators.KDJ(9 ,3, 3)['d'][-1]
```

KDJ值与交易所及FMZ量化均不一致，与turtle quant软件所显示的值 略有差异，有待以后再次验证。

### LOWEST，周期最低价

返回一个一维数组

```python
indicators.LOWEST(30)
```

```python
# 获取最新一根bar上的最低价
indicators.LOWEST(30)[-1]
```

LOWEST已检验，与FMZ量化所计算出的值一致。

### OBV，能量潮

返回一个一维数组

```python
indicators.OBV()
```

```python
# 获取最新一根bar上的obv
obv = indicators.OBV()[-1]
```

计算出的obv值与交易所k线图上显示的数据不一致，但与发明者量化上计算出的obv值一致：

```python
# PureQuant计算obv：
okex = OkexFutures("", "", "", "BTC-USD-201225")
time_frame = "1d"
indicators = Indicators(okex, "BTC-USD-201225", time_frame)
print(indicators.OBV()[-2])

# 输出结果
38773276.0


# FMZ量化计算obv，标的为Okex交割合约币本位BTC:
exchange.SetContractType("next_quarter") //设置合约类型为次季合约
function main(){
    var records = exchange.GetRecords(PERIOD_D1)
    var obv = TA.OBV(records)
    Log(obv[obv.length - 2])
}
# 输出结果
信息	38773276
```

因此可以放心使用。

### RSI，强弱指标

返回一个一维数组

```python
indicators.RSI(14)
```

```python
# 获取最新一根bar上的rsi
rsi = indicators.RSI(14)[-1]
```

RSI已检验，计算出的值与okex交易所k线图上所显示的一致。

### ROC，变动率指标

返回一个一维数组

```python
indicators.ROC(12)
```

```python
# 获取最新一根bar上的roc
roc = indicators.ROC(12)[-1]
```

ROC已检验，计算出的值与okex交易所k线图上所显示的一致。

### STOCHRSI，随机相对强弱指数

返回一个字典  {'stochrsi': stochrsi数组, 'fastk': fastk数组}

```python
indicators.STOCHRSI(14, 14, 3)
```

```python
# 获取最新一根bar上的stochrsi、fastk
stochrsi = indicators.STOCHRSI(14, 14, 3)['stochrsi'][-1]
fastk = indicators.STOCHRSI(14, 14, 3)['fastk'][-1]
```

STOCHRSI已验证，与okex、huobi交易所k线图上所显示的一致。

### SAR，抛物线指标

返回一个一维数组

```python
indicators.SAR()
```

```python
# 获取最新一根bar上的sar
sar = indicators.SAR()[-1]
```

SAR与okex、huobi交易所k线图上所显示均不一致，但与turtlequant一致，应是算法略有不同的缘故。

### STDDEV， 标准方差

返回一个一维数组

```python
indicators.STDDEV()
```

```python
# 获取最新一根bar上的stddev
stddev = indicators.STDDEV(20)-1
```

STDDEV（StandardDev）已验证，与turtlequant所计算的值一致。

### TRIX，三重指数平滑平均线

返回一个一维数组

```python
indicators.TRIX(12)
```

```python
# 获取最新一根bar上的trix
trix = indicators.TRIX(12)[-1]
```

TRIX已验证，与okex交易所k线图上所显示的一致。

### VOLUME，成交量

返回一个一维数组

```python
indicators.VOLUME()

# 获取最新一根bar上的volume
volume = indicators.VOLUME()[-1]
```

VOLUME已验证，与okex交易所k线图上所显示的一致。



indicators模块中的MA、EMA、KAMA函数，可以传入多个参数进行计算，求多个参数计算出的指标数值。

当传入多个参数时，返回的结果是一个列表。

用法示例：

```python
from purequant.indicators import INDICATORS
from purequant.trade import OKEXFUTURES

instrument_id = "ETC-USDT-201225"
time_frame = "1d"
exchange = OKEXFUTURES("", "", "", instrument_id)   # 实例化一个交易所对象
indicators = INDICATORS(exchange, instrument_id, time_frame)    # 实例化指标对象
ma = indicators.MA(60, 90)  # 传入两个参数
ma60 = ma[0]   # MA60, 一个一维数组
ma90 = ma[1]   # MA90, 一个一维数组
print(ma60[-1])     # 打印出当前k线上的ma60的值
print(ma90[-1])     # 打印出当前k线上的ma90的值
```



------



## 日志输出

调用时需先导入LOGGER模块，并在当前目录下创建名为`logger`的文件夹用以存放日志输出文件

默认文件路径是当前路径下的logs文件夹，如不存在则自动创建。

```python
from purequant.logger import logger
from purequant.config import config

config.loads("config.json")
```

在配置文件中，可以直接修改日志输出的等级来控制日志输出级别：

+ 将"level"设置成"critical"，则只输出"CRITICAL"级别的日志
+ "handler"中可以指明日志的输出方式
+ "file"是以文件输出的方式存储日志到当前目录下的"logger"文件夹，按照文件大小1M进行分割，保留最近10个文件
+ "time"也是文件输出，但是以按照一天的时间间隔来分割文件，保留最近10个文件
+ "stream"或者不填或者填入其他字符，都是输出到控制台，不会存储到文件
+ 输出到控制台时，不同级别的日志具有不同的颜色，建议将命令行窗口设置成黑色，以免蓝色日志看不见。

```json
{
    "LOG": {
        "level": "critical",
        "handler": "file"
    }
}
```

### debug

一般用来打印一些调试信息，级别最低

```python
logger.debug("要输出的调试信息")
```

### info

一般用来打印一些正常的操作信息

```python
logger.info("要输出的操作信息")
```

### warning

一般用来打印警告信息

```python
logger.info("要输出的警告信息")
```

### error

一般用来打印一些错误信息

```python
logger.info("要输出的错误信息")
```

### critical

一般用来打印一些致命的错误信息，等级最高

```python
logger.critical("要输出的致命的错误信息")
```



注：如果使用`logger`来记录异常信息，使用如下方法：

```python
from purequant.logger import logger
from purequant.config import config

config.loads('config.json')

try:
    print(a)
except:
    logger.error()	# 可以是任何级别，不用传入参数。
    
>>>
[2020-09-07  10:06:33] -> [ERROR] : Traceback (most recent call last):
  File "C:/Users/Administrator/PycharmProjects/pythonProject/11.py", line 7, in <module>
    print(a)
NameError: name 'a' is not defined
```

------



## 获取时间信息

调用前需先导入time_tools模块中的函数

```python
from purequant.time import *
```

### 获取本地时间

```python
localtime = get_localtime()
```

### 获取当前utc时间

```python
utc_time = get_utc_time()
```

### 获取当前时间戳（秒）

```python
cur_timestamp = get_cur_timestamp()
```

### 获取当前时间戳（毫秒）

```python
cur_timestamp_ms = get_cur_timestamp_ms()
```

------



## 示例策略

+ 双均线多空策略

+ 布林强盗突破策略

+ 更多示例策略敬请期待！