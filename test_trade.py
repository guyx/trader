import os
import django
import asyncio
from datetime import datetime
from asgiref.sync import sync_to_async
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from trader.strategy.brother2 import TradeStrategy
from panel.models import Strategy

async def test_trade():
    print("开始测试交易系统...")
    
    # 使用sync_to_async包装同步操作
    get_strategy = sync_to_async(Strategy.objects.get)
    strategy = await get_strategy(name="Brother2")
    
    # 初始化交易策略
    trade_strategy = TradeStrategy(strategy.name)
    await trade_strategy.initialize()  # 调用异步初始化
    
    # 启动策略
    await trade_strategy.start()
    
    print("交易系统启动成功!")
    
    # 保持运行一段时间
    await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(test_trade()) 