# coding=utf-8
#
# Copyright 2016 timercrack
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import pandas as pd
from pandas.io.sql import read_sql_query
from django.db import models
from django.db import connection
from django.core.exceptions import EmptyResultSet
from decimal import Decimal

from .const import *


def to_df(queryset, index_col=None, parse_dates=None):
    """
    :param queryset: django.db.models.query.QuerySet
    :param index_col: str or list of str, optional, default: None
    :param parse_dates: list or dict, default: None
    :return: pandas.core.frame.DataFrame
    """
    try:
        query, params = queryset.query.sql_with_params()
    except EmptyResultSet:
        # Occurs when Django tries to create an expression for a
        # query which will certainly be empty
        # e.g. Book.objects.filter(author__in=[])
        return pd.DataFrame()
    return read_sql_query(query, connection, params=params, index_col=index_col, parse_dates=parse_dates)


class Autonumber(models.Model):
    id = models.AutoField(verbose_name='自增值', primary_key=True)
    create_date = models.DateTimeField(verbose_name='生成时间', auto_now_add=True)


class Address(models.Model):
    name = models.CharField(verbose_name='名称', max_length=64)
    url = models.CharField(verbose_name='地址', max_length=128)
    type = models.CharField(verbose_name='类型', max_length=16, choices=AddressType.choices)
    operator = models.CharField(verbose_name='运营商', max_length=16, choices=OperatorType.choices)

    class Meta:
        verbose_name = '前置地址'
        verbose_name_plural = '前置地址列表'

    def __str__(self):
        return '{}{}-{}'.format(self.name, self.get_operator_display(), self.get_type_display())


class Broker(models.Model):
    name = models.CharField(max_length=50, unique=True)
    broker_id = models.CharField(max_length=20)
    investor_id = models.CharField(max_length=20)
    password = models.CharField(max_length=50)
    fake = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    current = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    pre_balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    cash = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    margin = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))

    def __str__(self):
        return self.name


class Performance(models.Model):
    broker = models.ForeignKey(Broker, verbose_name='账户', on_delete=models.CASCADE)
    day = models.DateField(verbose_name='日期')
    capital = models.DecimalField(verbose_name='资金', max_digits=12, decimal_places=2)
    unit_count = models.IntegerField(verbose_name='单位乘数', null=True)
    NAV = models.DecimalField(verbose_name='单位净值', max_digits=8, decimal_places=3, null=True)
    accumulated = models.DecimalField(verbose_name='累计净值', max_digits=8, decimal_places=3, null=True)
    dividend = models.DecimalField(verbose_name='分红', max_digits=12, decimal_places=2, null=True)
    used_margin = models.DecimalField(verbose_name='占用保证金', null=True, max_digits=12, decimal_places=2)
    fake = models.DecimalField(verbose_name='虚拟', max_digits=12, decimal_places=2, null=True)

    class Meta:
        verbose_name = '绩效'
        verbose_name_plural = '绩效列表'

    def __str__(self):
        return '{}-{}'.format(self.broker, self.NAV)


class Strategy(models.Model):
    name = models.CharField(max_length=50)
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE)
    instruments = models.ManyToManyField('Instrument', blank=True)
    force_opens = models.ManyToManyField('Instrument', blank=True, related_name='force_open_strategies')

    def __str__(self):
        return self.name


class Parameter(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='param_set')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    int_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.strategy.name}-{self.name}"


class Instrument(models.Model):
    product_code = models.CharField(max_length=20)
    exchange = models.CharField(max_length=10)
    name = models.CharField(max_length=50, blank=True)
    volume_multiple = models.IntegerField(default=1)
    price_tick = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.001'))
    margin_rate = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.1'))
    fee_money = models.DecimalField(max_digits=5, decimal_places=5, default=Decimal('0'))
    fee_volume = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    main_code = models.CharField(max_length=20, blank=True)
    all_inst = models.TextField(blank=True)
    night_trade = models.BooleanField(default=False)
    section = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.exchange}.{self.product_code}"


class Signal(models.Model):
    strategy = models.ForeignKey(Strategy, verbose_name='策略', on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, verbose_name='品种', on_delete=models.CASCADE)
    code = models.CharField('当前合约', max_length=16, null=True)
    type = models.CharField('信号类型', max_length=16, choices=SignalType.choices)
    trigger_value = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='触发值', null=True, blank=True)
    price = models.DecimalField('价格', max_digits=12, decimal_places=3, null=True, blank=True)
    volume = models.IntegerField('数量', null=True, blank=True)
    trigger_time = models.DateTimeField('发生时间')
    priority = models.IntegerField('优先级', choices=PriorityType.choices, default=PriorityType.Normal)
    processed = models.BooleanField('已处理', default=False, blank=True)

    class Meta:
        verbose_name = '信号'
        verbose_name_plural = '信号列表'

    def __str__(self):
        return f"{self.instrument}({self.code}){self.type}{self.volume}手" \
               f"{'(夜)' if self.instrument.night_trade else ''}"


class MainBar(models.Model):
    exchange = models.CharField('交易所', max_length=8, choices=ExchangeType.choices)
    product_code = models.CharField('品种代码', max_length=8, null=True, db_index=True)
    code = models.CharField('合约代码', max_length=16, null=True, blank=True)
    time = models.DateField('时间', db_index=True)
    open = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='开盘价')
    high = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='最高价')
    low = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='最低价')
    close = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='收盘价')
    settlement = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='结算价', null=True)
    volume = models.IntegerField('成交量')
    open_interest = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='持仓量')
    basis = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='基差', null=True)

    class Meta:
        verbose_name = '主力连续日K线'
        verbose_name_plural = '主力连续日K线列表'

    def __str__(self):
        return '{}.{}'.format(self.exchange, self.product_code)


class DailyBar(models.Model):
    exchange = models.CharField('交易所', max_length=8, choices=ExchangeType.choices)
    code = models.CharField('品种代码', max_length=16, null=True, db_index=True)
    expire_date = models.IntegerField('交割时间', null=True)
    time = models.DateField('时间', db_index=True)
    open = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='开盘价')
    high = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='最高价')
    low = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='最低价')
    close = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='收盘价')
    settlement = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='结算价', null=True)
    volume = models.IntegerField('成交量')
    open_interest = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='持仓量')

    class Meta:
        verbose_name = '日K线'
        verbose_name_plural = '日K线列表'

    def __str__(self):
        return '{}.{}'.format(self.exchange, self.code)


class Order(models.Model):
    broker = models.ForeignKey(Broker, verbose_name='账户', on_delete=models.CASCADE)
    strategy = models.ForeignKey(Strategy, verbose_name='策略', on_delete=models.SET_NULL, null=True, blank=True)
    order_ref = models.CharField('报单号', max_length=13)
    instrument = models.ForeignKey(Instrument, verbose_name='品种', on_delete=models.CASCADE)
    code = models.CharField('合约代码', max_length=16, null=True, blank=True)
    front = models.IntegerField('前置编号')
    session = models.IntegerField('会话编号')
    price = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='报单价格')
    volume = models.IntegerField('手数', blank=True, null=True)
    direction = models.CharField('方向', max_length=8, choices=DirectionType.choices)
    offset_flag = models.CharField('开平', max_length=8, choices=OffsetFlag.choices)
    status = models.CharField('状态', max_length=16, choices=OrderStatus.choices)
    send_time = models.DateTimeField('发送时间')
    update_time = models.DateTimeField('更新时间')
    signal = models.OneToOneField(Signal, verbose_name='信号', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = '报单'
        verbose_name_plural = '报单列表'

    def __str__(self):
        return '{}-{}'.format(self.instrument, self.get_offset_flag_display())


class Trade(models.Model):
    broker = models.ForeignKey(Broker, verbose_name='账户', on_delete=models.CASCADE)
    strategy = models.ForeignKey(Strategy, verbose_name='策略', on_delete=models.SET_NULL, null=True, blank=True)
    instrument = models.ForeignKey(Instrument, verbose_name='品种', on_delete=models.CASCADE)
    open_order = models.OneToOneField(Order, verbose_name='开仓报单', on_delete=models.SET_NULL,
                                      related_name='open_order', null=True, blank=True)
    close_order = models.OneToOneField(Order, verbose_name='平仓报单', on_delete=models.SET_NULL,
                                       related_name='close_order', null=True, blank=True)
    code = models.CharField('合约代码', max_length=16, null=True, blank=True)
    direction = models.CharField('方向', max_length=8, choices=DirectionType.choices)
    open_time = models.DateTimeField('开仓日期')
    close_time = models.DateTimeField('平仓日期', null=True, blank=True)
    shares = models.IntegerField('手数', null=True, blank=True)
    filled_shares = models.IntegerField('已成交手数', null=True, blank=True)
    closed_shares = models.IntegerField('已平仓手数', null=True, blank=True)
    avg_entry_price = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='持仓均价', null=True, blank=True)
    avg_exit_price = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='平仓均价', null=True, blank=True)
    profit = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='持仓盈亏', null=True, blank=True)
    frozen_margin = models.DecimalField(max_digits=12, decimal_places=3, verbose_name='冻结保证金', null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='手续费', null=True, blank=True)

    class Meta:
        verbose_name = '交易记录'
        verbose_name_plural = '交易记录列表'

    def __str__(self):
        return '{}{}{}手'.format(self.instrument, self.direction, self.shares)
