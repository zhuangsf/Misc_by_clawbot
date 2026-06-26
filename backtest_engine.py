#!/usr/bin/env python3
"""
追涨杀跌策略回测系统
基于3倍放量警报触发交易
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from itertools import product
from copy import deepcopy
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """交易记录"""
    entry_time: str
    exit_time: str
    direction: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    position_size: float  # 仓位比例
    volume_ratio: float  # 放量倍数
    pnl: float  # 盈亏金额
    pnl_pct: float  # 盈亏百分比
    kline_time: str  # 触发K线时间
    exit_reason: str  # 'stop_loss' or 'take_profit'


@dataclass
class StrategyParams:
    """策略参数配置"""
    # 仓位配置：{放量倍数: 仓位比例}
    position_config: Dict[float, float] = field(default_factory=lambda: {3: 1.0, 4: 2.0, 5: 3.0})
    
    # 卖出条件：第几根K线收盘卖出 (2, 3, 4, 5)
    exit_kline_count: int = 3
    
    # 止损比例 (0=跌破开盘价止损)
    stop_loss_pct: float = 0.0
    
    # 是否启用止损
    enable_stop_loss: bool = True
    
    # 交易成本 (千分之)
    transaction_cost: float = 0.001
    
    # 初始资金
    initial_capital: float = 10000.0


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, params: StrategyParams):
        self.params = params
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        
    def calculate_position_size(self, volume_ratio: float) -> float:
        """根据放量倍数计算仓位"""
        # 找到最接近的配置
        best_ratio = min(self.params.position_config.keys(), 
                        key=lambda x: abs(x - volume_ratio))
        return self.params.position_config[best_ratio]
    
    def run_backtest(self, volume_spikes: List[Dict], kline_data: List[Dict]) -> Dict:
        """
        运行回测
        
        Args:
            volume_spikes: 放量记录列表
            kline_data: K线数据列表 (按时间排序)
        
        Returns:
            回测结果
        """
        self.trades = []
        self.equity_curve = []
        
        # 标准化时间格式 (处理 2026-03-06T12:30:00 -> 2026-03-06 12:30:00)
        for k in kline_data:
            if 'T' in str(k.get('kline_time', '')):
                k['kline_time'] = str(k['kline_time']).replace('T', ' ')
        for s in volume_spikes:
            if 'T' in str(s.get('kline_time', '')):
                s['kline_time'] = str(s['kline_time']).replace('T', ' ')
        
        # 创建K线数据字典 {时间: 数据}
        kline_dict = {k['kline_time']: k for k in kline_data}
        
        # 按时间排序放量记录
        sorted_spikes = sorted(volume_spikes, key=lambda x: x.get('timestamp', ''))
        
        capital = self.params.initial_capital
        position = None  # 当前持仓
        entry_kline_time = None
        
        for spike in sorted_spikes:
            kline_time = spike.get('kline_time', '')
            
            if kline_time not in kline_dict:
                continue
            
            current_kline = kline_dict[kline_time]
            
            # 如果有空仓，检查是否触发交易
            if position is None:
                # 触发交易
                direction = 'long' if spike['price_direction'] == '涨' else 'short'
                position_size = self.calculate_position_size(spike['volume_ratio'])
                
                # 计算入场价
                entry_price = current_kline['close']
                entry_time = spike.get('timestamp', current_kline.get('kline_time', ''))
                
                # 设置止损价
                if direction == 'long':
                    stop_loss_price = current_kline['open']
                else:
                    stop_loss_price = current_kline['open']
                
                position = {
                    'direction': direction,
                    'entry_price': entry_price,
                    'entry_kline_time': kline_time,
                    'position_size': position_size,
                    'stop_loss_price': stop_loss_price,
                    'volume_ratio': spike['volume_ratio'],
                }
                entry_kline_time = kline_time
                
                logger.debug(f"开仓: {direction} {position_size}手 @ {entry_price}")
                
            else:
                # 检查是否需要平仓
                current_price = current_kline['close']
                current_time = current_kline['kline_time']
                
                # 计算从开仓K线起的K线数量
                kline_times = [k['kline_time'] for k in kline_data]
                if entry_kline_time in kline_times:
                    entry_idx = kline_times.index(entry_kline_time)
                    current_idx = kline_times.index(current_time)
                    kline_count = current_idx - entry_idx
                else:
                    kline_count = 0
                
                exit_reason = None
                should_close = False
                
                # 1. 检查止损条件
                if self.params.enable_stop_loss:
                    if position['direction'] == 'long' and current_price < position['stop_loss_price']:
                        should_close = True
                        exit_reason = 'stop_loss'
                    elif position['direction'] == 'short' and current_price > position['stop_loss_price']:
                        should_close = True
                        exit_reason = 'stop_loss'
                
                # 2. 检查止盈条件 (第N根K线收盘)
                if not should_close and kline_count >= self.params.exit_kline_count:
                    should_close = True
                    exit_reason = 'take_profit'
                
                if should_close:
                    # 计算盈亏
                    if position['direction'] == 'long':
                        pnl = (current_price - position['entry_price']) * position['position_size']
                        pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
                    else:
                        pnl = (position['entry_price'] - current_price) * position['position_size']
                        pnl_pct = (position['entry_price'] - current_price) / position['entry_price'] * 100
                    
                    # 扣除交易成本
                    transaction_cost = capital * self.params.transaction_cost * 2  # 买入+卖出
                    pnl -= transaction_cost
                    pnl_pct -= transaction_cost / capital * 100
                    
                    capital += pnl
                    
                    trade = Trade(
                        entry_time=position['entry_kline_time'],
                        exit_time=current_time,
                        direction=position['direction'],
                        entry_price=position['entry_price'],
                        exit_price=current_price,
                        position_size=position['position_size'],
                        volume_ratio=position['volume_ratio'],
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        kline_time=entry_kline_time,
                        exit_reason=exit_reason
                    )
                    self.trades.append(trade)
                    
                    logger.debug(f"平仓: {trade.exit_reason} | PnL: {pnl:.2f} ({pnl_pct:.2f}%)")
                    
                    # 清空持仓
                    position = None
                    entry_kline_time = None
            
            # 记录资金曲线
            self.equity_curve.append({
                'time': current_kline.get('kline_time', ''),
                'equity': capital,
                'position': position
            })
        
        return self.calculate_metrics(capital)
    
    def calculate_metrics(self, final_capital: float) -> Dict:
        """计算回测指标"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_pnl_pct': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'trades': [],
                'equity_curve': self.equity_curve
            }
        
        # 收益率序列
        returns = [t.pnl_pct for t in self.trades]
        
        # 总收益
        total_pnl = sum([t.pnl for t in self.trades])
        total_pnl_pct = (final_capital - self.params.initial_capital) / self.params.initial_capital * 100
        
        # 胜率
        winning_trades = [t for t in self.trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        
        # 平均盈亏
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        avg_loss = np.abs(np.mean([t.pnl for t in losing_trades])) if losing_trades else 0
        
        # 盈亏比
        profit_factor = abs(sum([t.pnl for t in winning_trades]) / sum([t.pnl for t in losing_trades])) if losing_trades else float('inf')
        
        # 最大回撤
        equity_values = [e['equity'] for e in self.equity_curve]
        max_drawdown = 0
        peak = equity_values[0] if equity_values else 0
        for equity in equity_values:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100 if peak > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 夏普率 (年化)
        if len(returns) > 1 and np.std(returns) > 0:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            # 年化 (假设每年约252个交易日，每个交易约16个15分钟K线)
            annualization_factor = np.sqrt(252) if std_return > 0 else 0
            sharpe_ratio = (avg_return / std_return) * annualization_factor if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades': [{
                'entry_time': t.entry_time,
                'exit_time': t.exit_time,
                'direction': t.direction,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'position_size': t.position_size,
                'volume_ratio': t.volume_ratio,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'exit_reason': t.exit_reason
            } for t in self.trades],
            'equity_curve': self.equity_curve
        }


def load_kline_data(log_file: str) -> List[Dict]:
    """从日志文件加载K线数据"""
    data = []
    if not log_file:
        return data
    
    # 支持JSON格式
    if log_file.endswith('.json'):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                klines = json.load(f)
            for k in klines:
                data.append({
                    'kline_time': k.get('kline_time', ''),
                    'open': float(k.get('open', 0)),
                    'close': float(k.get('close', 0)),
                    'high': float(k.get('high', 0)),
                    'low': float(k.get('low', 0)),
                    'volume': float(k.get('volume', 0))
                })
            logger.info(f"从JSON加载 {len(data)} 条K线数据")
            return data
        except Exception as e:
            logger.error(f"加载JSON K线数据失败: {e}")
            return []
    
    if not log_file.endswith('.log'):
        return data
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        recent_lines = lines[-500:] if len(lines) > 500 else lines
        
        for line in recent_lines:
            if '✅ K线完成记录' in line:
                import re
                match = re.search(r'时间: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                vol_match = re.search(r'成交额: ([\d,\.]+[KM]?) USDT', line)
                
                if match and vol_match:
                    vol_str = vol_match.group(1)
                    if vol_str.endswith('M'):
                        volume = float(vol_str[:-1]) * 1_000_000
                    elif vol_str.endswith('K'):
                        volume = float(vol_str[:-1]) * 1_000
                    else:
                        volume = float(vol_str)
                    
                    data.append({
                        'kline_time': match.group(1),
                        'volume': volume,
                        'volume_str': vol_str
                    })
    except Exception as e:
        logger.error(f"加载K线数据失败: {e}")
    
    return data


def load_volume_spikes(spike_file: str) -> List[Dict]:
    """加载放量记录"""
    data = []
    if not spike_file or not spike_file.endswith('.log'):
        return data
    
    try:
        with open(spike_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    data.append(record)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        logger.warning(f"放量记录文件不存在: {spike_file}")
    except Exception as e:
        logger.error(f"加载放量记录失败: {e}")
    
    return data


def run_parameter_optimization(
    volume_spikes: List[Dict], 
    kline_data: List[Dict]
) -> List[Dict]:
    """运行参数优化"""
    
    # 定义参数组合
    position_configs = [
        {3: 1.0, 4: 1.5, 5: 2.0},  # 保守
        {3: 1.0, 4: 2.0, 5: 3.0},  # 基准
        {3: 1.5, 4: 3.0, 5: 4.5},  # 激进
        {3: 1.0, 4: 2.5, 5: 4.0},  # 中激进
    ]
    
    exit_counts = [2, 3, 4, 5]
    
    results = []
    param_id = 1
    
    logger.info(f"开始参数优化，共 {len(position_configs)} 种仓位配置 × {len(exit_counts)} 种止盈条件 = {len(position_configs) * len(exit_counts)} 种组合")
    
    for pos_config in position_configs:
        for exit_count in exit_counts:
            params = StrategyParams(
                position_config=pos_config,
                exit_kline_count=exit_count,
                enable_stop_loss=True,
                transaction_cost=0.001,
                initial_capital=10000
            )
            
            engine = BacktestEngine(params)
            metrics = engine.run_backtest(volume_spikes, kline_data)
            
            result = {
                'param_id': param_id,
                'position_config': pos_config,
                'exit_kline_count': exit_count,
                **metrics
            }
            results.append(result)
            
            logger.info(f"参数组合 {param_id}: 胜率{metrics['win_rate']:.1f}% | "
                       f"收益{metrics['total_pnl_pct']:.2f}% | "
                       f"夏普率{metrics['sharpe_ratio']:.2f} | "
                       f"最大回撤{metrics['max_drawdown']:.2f}%")
            
            param_id += 1
    
    return results


def find_best_params(results: List[Dict]) -> Dict:
    """找出最佳参数"""
    # 按夏普率排序
    sorted_results = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
    
    # 过滤掉没有交易的结果
    valid_results = [r for r in sorted_results if r['total_trades'] > 0]
    
    if not valid_results:
        return {
            'best': None,
            'ranking': [],
            'summary': '没有足够的交易数据进行评估'
        }
    
    # 综合评分：夏普率权重最高，其次收益，最后回撤
    best = valid_results[0]
    
    return {
        'best': best,
        'ranking': valid_results[:5],  # Top 5
        'summary': f"""
=== 最佳参数组合 ===
参数ID: {best['param_id']}
仓位配置: {best['position_config']}
止盈条件: 第{best['exit_kline_count']}根K线

=== 收益指标 ===
总交易次数: {best['total_trades']}
胜率: {best['win_rate']:.2f}%
总收益: {best['total_pnl_pct']:.2f}%
夏普率: {best['sharpe_ratio']:.3f}
最大回撤: {best['max_drawdown']:.2f}%

=== 盈亏分析 ===
平均盈利: {best['avg_win']:.2f}
平均亏损: {best['avg_loss']:.2f}
盈亏比: {best['profit_factor']:.2f}
"""
    }


def generate_report(results: List[Dict], best_result: Dict) -> str:
    """生成回测报告"""
    report = f"""
================================================================================
                    追涨杀跌策略回测报告
                    生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

一、回测概要
-----------
共测试 {len(results)} 组参数组合

{best_result['summary']}

二、Top 5 参数组合
------------------
"""
    for i, r in enumerate(best_result['ranking'], 1):
        report += f"""
{i}. 参数组合 #{r['param_id']}
   仓位配置: {r['position_config']}
   止盈条件: 第{r['exit_kline_count']}根K线
   交易次数: {r['total_trades']} | 胜率: {r['win_rate']:.1f}%
   收益: {r['total_pnl_pct']:+.2f}% | 夏普率: {r['sharpe_ratio']:.3f}
   最大回撤: {r['max_drawdown']:.2f}%
"""
    
    return report


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='策略回测')
    parser.add_argument('--spike-file', type=str, help='放量记录文件')
    parser.add_argument('--kline-file', type=str, help='K线日志文件')
    parser.add_argument('--output', type=str, default='backtest_report.txt', help='输出报告文件')
    
    args = parser.parse_args()
    
    # 加载数据
    volume_spikes = load_volume_spikes(args.spike_file)
    kline_data = load_kline_data(args.kline_file)
    
    logger.info(f"加载 {len(volume_spikes)} 条放量记录")
    logger.info(f"加载 {len(kline_data)} 条K线数据")
    
    if len(volume_spikes) < 10:
        logger.warning("放量记录太少，建议收集更多数据后再回测")
    
    # 运行回测
    results = run_parameter_optimization(volume_spikes, kline_data)
    best_result = find_best_params(results)
    
    # 生成报告
    report = generate_report(results, best_result)
    
    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n报告已保存到: {args.output}")
