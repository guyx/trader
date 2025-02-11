import os
import django
import redis
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panel.settings')
django.setup()

from panel.models import Broker, Strategy, Parameter, Instrument
from panel.const import DirectionType

def test_setup():
    # 1. 测试Redis连接
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis连接成功")
    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        return False

    # 2. 测试数据库配置
    try:
        # 创建测试账户
        broker, created = Broker.objects.get_or_create(
            name="测试账户",
            defaults={
                "broker_id": "9999",  # 模拟测试
                "investor_id": "test001",
                "password": "test123",
                "fake": Decimal("1000000"),
                "current": Decimal("1000000"),
                "pre_balance": Decimal("1000000"),
                "cash": Decimal("1000000"),
                "margin": Decimal("0")
            }
        )
        print(f"✓ 经纪商账户{'创建' if created else '已存在'}")

        # 创建测试策略
        strategy, created = Strategy.objects.get_or_create(
            name="Brother2",
            defaults={"broker": broker}
        )
        print(f"✓ 交易策略{'创建' if created else '已存在'}")

        # 创建策略参数
        params = {
            'BreakPeriod': ('突破周期', 20),
            'AtrPeriod': ('ATR周期', 20),
            'LongPeriod': ('长周期', 20),
            'ShortPeriod': ('短周期', 10),
            'StopLoss': ('止损参数', 2),
            'Risk': ('风险系数', 0.001)
        }
        
        for code, (name, value) in params.items():
            if isinstance(value, float):
                param, created = Parameter.objects.get_or_create(
                    strategy=strategy, code=code,
                    defaults={'name': name, 'float_value': value}
                )
            else:
                param, created = Parameter.objects.get_or_create(
                    strategy=strategy, code=code,
                    defaults={'name': name, 'int_value': value}
                )
            print(f"✓ 参数 {code} {'创建' if created else '已存在'}")

        # 验证数据
        broker.refresh_from_db()
        print("\n账户信息验证:")
        print(f"账户名称: {broker.name}")
        print(f"可用资金: {broker.cash:,.2f}")
        print(f"保证金: {broker.margin:,.2f}")
        print(f"虚拟资金: {broker.fake:,.2f}")

        strategy.refresh_from_db()
        print("\n策略参数验证:")
        for param in strategy.param_set.all():
            value = param.float_value if param.float_value is not None else param.int_value
            print(f"{param.name}: {value}")

        # 创建一些测试用的交易品种
        instruments = []
        test_instruments = [
            ('IF', 'CFFEX', '股指期货', 300),
            ('IC', 'CFFEX', '中证500', 200),
            ('au', 'SHFE', '黄金', 1000),
            ('cu', 'SHFE', '铜', 5),
        ]
        
        for code, exchange, name, volume in test_instruments:
            inst, created = Instrument.objects.get_or_create(
                product_code=code,
                defaults={
                    'exchange': exchange,
                    'name': name,
                    'volume_multiple': volume,
                }
            )
            instruments.append(inst)
            print(f"✓ 交易品种 {code} {'创建' if created else '已存在'}")
        
        # 为策略添加交易品种
        strategy.instruments.add(*instruments)
        print("✓ 为策略添加交易品种")

        return True

    except Exception as e:
        print(f"✗ 数据库配置测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试配置...")
    if test_setup():
        print("\n✓ 所有测试通过!")
    else:
        print("\n✗ 测试失败!") 