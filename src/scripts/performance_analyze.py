import matplotlib
import pandas as pd
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import os
import psutil
import gc
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.indicators_talib import TechnicalIndicatorsTALib
from src.core.data_processor import DataProcessor

#忽略绘图警告
import warnings
warnings.filterwarnings('ignore',category=UserWarning,module='matplotlib')

class PerformanceAnalyzer:
    """性能分析器，用于比较不同数据处理方案的性能并生成可视化图表"""
    def __init__(self,db_path,csv_path,output_dir='output'):
        """
        初始化性能分析器
    
        参数:
        db_path: DuckDB数据库路径
        output_dir: 输出目录路径
        """
        self.db_path=db_path
        self.csv_path=csv_path
        self.output_dir=output_dir
        self.data_processor=DataProcessor(db_path,csv_path,output_dir)

        #确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    def get_memory_usage(self):
        """
        获取当前Python进程的内存使用情况
    
        返回值:
        float: 内存使用量(MB)
        """
        process=psutil.Process(os.getpid())
        mem_info=process.memory_info()
        return mem_info.rss / 1024 / 1024  # 转换为MB

    def detailed_performance_comparison(self,limit):
        """执行详细的性能比较，记录各阶段的时间和内存占用"""
        print(f"开始详细的性能比较，限制行数: {limit}")
        performance_data = {
            'pandas': {
                'read_csv_time': 0,
                'read_duckdb_time': 0,
                'process_time': 0, 
                'save_time': 0,
                'total_time': 0,
                'read_csv_memory': 0,
                'read_duckdb_memory': 0,
                'process_memory': 0,
                'save_memory': 0
            },
            'polars': {
                'read_csv_time': 0,
                'read_duckdb_time': 0,
                'process_time': 0, 
                'save_time': 0,
                'total_time': 0,
                'read_csv_memory': 0,
                'read_duckdb_memory': 0,
                'process_memory': 0,
                'save_memory': 0
            }
        }
    
        # 强制垃圾回收，清理内存，确保测量准确
        gc.collect()
        
        #测试Pandas+CSV读取方案
        print("测试Pandas+CSV读取方案:")
        try:
            # 读取数据
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            df_pandas_csv = self.data_processor.read_data_with_pandas_csv(limit)
            pandas_read_csv_time = time.perf_counter() - start_time
            pandas_read_csv_memory = self.get_memory_usage() - start_memory
        except Exception as e:
            print(f"Pandas+CSV读取出错: {e}")
            import traceback
            traceback.print_exc()


        # 测试Pandas+DuckDB方案
        print("测试Pandas+DuckDB方案:")
        try:
            # 读取数据
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            df_pandas = self.data_processor.read_data_with_pandas_duckdb(limit)
            pandas_read_duckdb_time = time.perf_counter() - start_time
            pandas_read_duckdb_memory = self.get_memory_usage() - start_memory
        
            # 计算指标
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            df_pandas_with_indicators = TechnicalIndicators.calculate_all_indicators(df_pandas, is_pandas=True)
            pandas_process_time = time.perf_counter() - start_time
            pandas_process_memory = self.get_memory_usage() - start_memory
            print(f"Pandas计算指标耗时: {pandas_process_time:.6f}秒")
        
            # 保存结果
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            self.data_processor.save_result_pandas(df_pandas_with_indicators)
            pandas_save_time = time.perf_counter() - start_time
            pandas_save_memory = self.get_memory_usage() - start_memory
            print(f"Pandas保存结果耗时: {pandas_save_time:.6f}秒")
        
            # 记录Pandas性能数据，使用高精度
            performance_data['pandas']['read_csv_time'] = pandas_read_csv_time
            performance_data['pandas']['read_duckdb_time'] = pandas_read_duckdb_time
            performance_data['pandas']['process_time'] = pandas_process_time
            performance_data['pandas']['save_time'] = pandas_save_time
            performance_data['pandas']['total_time'] = pandas_read_duckdb_time + pandas_process_time + pandas_save_time
            performance_data['pandas']['read_csv_memory'] = pandas_read_csv_memory
            performance_data['pandas']['read_duckdb_memory'] = pandas_read_duckdb_memory
            performance_data['pandas']['process_memory'] = pandas_process_memory
            performance_data['pandas']['save_memory'] = pandas_save_memory
        
            # 清理内存，准备下一轮测试
            del df_pandas, df_pandas_with_indicators
            gc.collect()
            time.sleep(0.2)  # 增加暂停时间，确保系统稳定
        
        except Exception as e:
            print(f"Pandas处理出错: {e}")
            import traceback
            traceback.print_exc()
    
        print()

        #测试Polars+CSV读取方案
        print("测试Polars+CSV读取方案:")
        try:
            # 读取数据
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            df_polars_csv = self.data_processor.read_data_with_polars_csv(limit)
            polars_read_csv_time = time.perf_counter() - start_time
            polars_read_csv_memory = self.get_memory_usage() - start_memory
        except Exception as e:
            print(f"Polars+CSV读取出错: {e}")
            import traceback
            traceback.print_exc()
    
        # 测试Polars+DuckDB方案
        print("测试Polars+DuckDB方案:")
        try:
            # 读取数据
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            df_polars = self.data_processor.read_data_with_polars_duckdb(limit)  
            polars_read_duckdb_time = time.perf_counter() - start_time
            polars_read_duckdb_memory = self.get_memory_usage() - start_memory
            # 不再重复打印，因为read_data_with_polars_duckdb方法内部已经打印了
        
            # 计算指标
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            df_polars_with_indicators = TechnicalIndicators.calculate_all_indicators(df_polars, is_pandas=False)
            polars_process_time = time.perf_counter() - start_time
            polars_process_memory = self.get_memory_usage() - start_memory
            print(f"Polars计算指标耗时: {polars_process_time:.6f}秒")
        
            # 保存结果
            start_time = time.perf_counter()
            start_memory = self.get_memory_usage()
            self.data_processor.save_result_polars(df_polars_with_indicators)
            polars_save_time = time.perf_counter() - start_time
            polars_save_memory = self.get_memory_usage() - start_memory
            print(f"Polars保存结果耗时: {polars_save_time:.6f}秒")
        
            # 记录Polars性能数据，使用高精度
            performance_data['polars']['read_csv_time'] = polars_read_csv_time
            performance_data['polars']['read_duckdb_time'] = polars_read_duckdb_time
            performance_data['polars']['process_time'] = polars_process_time
            performance_data['polars']['save_time'] = polars_save_time
            performance_data['polars']['total_time'] = polars_read_duckdb_time + polars_process_time + polars_save_time
            performance_data['polars']['read_csv_memory'] = polars_read_csv_memory
            performance_data['polars']['read_duckdb_memory'] = polars_read_duckdb_memory
            performance_data['polars']['process_memory'] = polars_process_memory
            performance_data['polars']['save_memory'] = polars_save_memory
        
        except Exception as e:
            print(f"Polars处理出错: {e}")
            import traceback
            traceback.print_exc()
    
        # 打印性能对比
        print("\n详细性能比较结果:")
    
        # 读取数据阶段比较
        pandas_csv_time = performance_data['pandas']['read_csv_time']
        polars_csv_time = performance_data['polars']['read_csv_time']
        pandas_duckdb_time = performance_data['pandas']['read_duckdb_time']
        polars_duckdb_time = performance_data['polars']['read_duckdb_time']
        pandas_csv_memory = performance_data['pandas']['read_csv_memory']
        polars_csv_memory = performance_data['polars']['read_csv_memory']
        pandas_duckdb_memory = performance_data['pandas']['read_duckdb_memory']
        polars_duckdb_memory = performance_data['polars']['read_duckdb_memory']
    
        print("\n读取数据:")
        print(f"  Pandas+CSV: {pandas_csv_time:.6f}秒, 内存使用: {abs(pandas_csv_memory):.3f}MB")
        print(f"  Polars+CSV: {polars_csv_time:.6f}秒, 内存使用: {abs(polars_csv_memory):.3f}MB")
        print(f"  Pandas+DuckDB: {pandas_duckdb_time:.6f}秒, 内存使用: {abs(pandas_duckdb_memory):.3f}MB")
        print(f"  Polars+DuckDB: {polars_duckdb_time:.6f}秒, 内存使用: {abs(polars_duckdb_memory):.3f}MB")
    
        # 添加一个小的epsilon值以避免除零错误
        epsilon = 1e-10
        if polars_csv_time > epsilon:
            speedup = pandas_csv_time / polars_csv_time
            print(f"  加速比: {speedup:.3f}倍")
        else:
            print("  加速比: Polars+CSV速度极快")
    
        if pandas_csv_memory > epsilon:
            memory_reduction = ((pandas_csv_memory - polars_csv_memory) / pandas_csv_memory) * 100
            print(f"  Pandas+CSV内存减少: {abs(memory_reduction):.3f}%")
        if polars_duckdb_time > epsilon:
            speedup = pandas_duckdb_time / polars_duckdb_time
            print(f"  加速比: {speedup:.3f}倍")
        else:
            print("  加速比: Polars+DuckDB速度极快")
        if pandas_duckdb_memory > epsilon:
            memory_reduction = ((pandas_duckdb_memory - polars_duckdb_memory) / pandas_duckdb_memory) * 100
            print(f"  DuckDB内存减少: {abs(memory_reduction):.3f}%")
    
        # 计算指标阶段比较
        pandas_process_time = performance_data['pandas']['process_time']
        polars_process_time = performance_data['polars']['process_time']
        pandas_process_memory = performance_data['pandas']['process_memory']
        polars_process_memory = performance_data['polars']['process_memory']
    
        print("\n计算指标:")
        # 处理内存负值问题，确保显示为非负数
        print(f"  Pandas+DuckDB: {pandas_process_time:.4f}秒, 内存使用: {abs(pandas_process_memory):.2f}MB")
        print(f"  Polars+DuckDB: {polars_process_time:.4f}秒, 内存使用: {abs(polars_process_memory):.2f}MB")
    
        if polars_process_time > epsilon:
            speedup = pandas_process_time / polars_process_time
            print(f"  加速比: {speedup:.2f}倍")
        else:
            print("  加速比: Polars速度极快")
    
        if pandas_process_memory > epsilon:
            memory_reduction = ((pandas_process_memory - polars_process_memory) / pandas_process_memory) * 100
            print(f"  内存减少: {abs(memory_reduction):.2f}%")
    
        # 保存结果阶段比较
        pandas_time = performance_data['pandas']['save_time']
        polars_time = performance_data['polars']['save_time']
        pandas_memory = performance_data['pandas']['save_memory']
        polars_memory = performance_data['polars']['save_memory']
    
        print("\n保存结果:")
        print(f"  Pandas+DuckDB: {pandas_time:.4f}秒, 内存使用: {abs(pandas_memory):.2f}MB")
        print(f"  Polars+DuckDB: {polars_time:.4f}秒, 内存使用: {abs(polars_memory):.2f}MB")
    
        if polars_time > epsilon:
            speedup = pandas_time / polars_time
            print(f"  加速比: {speedup:.2f}倍")
        else:
            print("  加速比: Polars速度极快")
    
        if pandas_memory > epsilon:
            memory_reduction = ((pandas_memory - polars_memory) / pandas_memory) * 100
            print(f"  内存减少: {abs(memory_reduction):.2f}%")
    
        # 总时间比较
        pandas_total = performance_data['pandas']['total_time']
        polars_total = performance_data['polars']['total_time']
    
        print("\n总耗时:")
        print(f"  Pandas+DuckDB: {pandas_total:.4f}秒")
        print(f"  Polars+DuckDB: {polars_total:.4f}秒")
    
        if polars_total > epsilon:
            total_speedup = pandas_total / polars_total
            print(f"  总加速比: {total_speedup:.2f}倍")
        else:
            print("  总加速比: Polars速度极快")
    
        # 将性能数据保存到CSV文件
        self.save_performance_data(performance_data)
    
        return performance_data
    
    def generate_comparison_charts(self, performance_data, chart_type='all'):
        """
        生成性能比较图表
    
        参数:
        performance_data: 性能数据字典
        chart_type: 图表类型 ('all', 'time', 'memory')
    
        返回值:
        list: 保存的图表文件路径列表
        """
        saved_charts = []
    
        # 转换性能数据为适合图表显示的格式
        phases = ['读取数据', '计算指标', '保存结果', '总耗时']
    
        # 提取数据并准备图表数据框
        chart_data = {
            'phase': phases,
            'pandas_time': [
                performance_data['pandas']['read_duckdb_time'],
                performance_data['pandas']['process_time'],
                performance_data['pandas']['save_time'],
                performance_data['pandas']['total_time']
            ],
            'polars_time': [
                performance_data['polars']['read_duckdb_time'],
                performance_data['polars']['process_time'],
                performance_data['polars']['save_time'],
                performance_data['polars']['total_time']
            ],
            'pandas_memory': [
                # 修复内存负值问题：使用max(0, ...)确保不会出现负值
                max(0, performance_data['pandas']['read_duckdb_memory']),
                max(0, performance_data['pandas']['process_memory']),
                max(0, abs(performance_data['pandas']['save_memory'])),  # 取绝对值确保显示
                max(0, performance_data['pandas']['process_memory'])  # 使用处理阶段的内存作为总内存
            ],
            'polars_memory': [
                max(0, performance_data['polars']['read_duckdb_memory']),
                max(0, performance_data['polars']['process_memory']),
                max(0, performance_data['polars']['save_memory']),
                max(0, performance_data['polars']['process_memory'])  # 使用处理阶段的内存作为总内存
            ]
        }
    
        df = pd.DataFrame(chart_data)
    
        # 设置中文字体，确保中文能正常显示
        plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC']
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
        # 生成时间对比图 - 使用对数坐标解决比例问题
        if chart_type in ['all', 'time']:
            fig, ax = plt.subplots(figsize=(10, 6))
        
            # 设置柱状图位置
            width = 0.35
            x = np.arange(len(df))
        
            # 绘制柱状图
            ax.bar(x - width/2, df['pandas_time'], width, label='Pandas+DuckDB', alpha=0.8)
            ax.bar(x + width/2, df['polars_time'], width, label='Polars+DuckDB', alpha=0.8)
        
            # 设置图表属性
            ax.set_xlabel('处理阶段')
            ax.set_ylabel('时间 (秒)')
            ax.set_title('不同方案的处理时间对比 (对数坐标)')
            ax.set_xticks(x)
            ax.set_xticklabels(df['phase'], rotation=45)
            ax.legend()
            ax.set_yscale('log')  # 使用对数坐标
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
        
            # 保存图表
            time_chart_path = os.path.join(self.output_dir, 'performance_time_comparison.png')
            plt.tight_layout()
            plt.savefig(time_chart_path, dpi=300)
            plt.close()
            saved_charts.append(time_chart_path)
            print(f"时间对比图已保存至: {time_chart_path}")
    
        # 生成内存对比图
        if chart_type in ['all', 'memory']:
            fig, ax = plt.subplots(figsize=(10, 6))
        
            # 设置柱状图位置
            width = 0.35
            x = np.arange(len(df))
        
            # 绘制柱状图
            ax.bar(x - width/2, df['pandas_memory'], width, label='Pandas+DuckDB', alpha=0.8)
            ax.bar(x + width/2, df['polars_memory'], width, label='Polars+DuckDB', alpha=0.8)
        
            # 设置图表属性
            ax.set_xlabel('处理阶段')
            ax.set_ylabel('内存使用 (MB)')
            ax.set_title('不同方案的内存使用对比')
            ax.set_xticks(x)
            ax.set_xticklabels(df['phase'], rotation=45)
            ax.legend()
        
            # 保存图表
            memory_chart_path = os.path.join(self.output_dir, 'performance_memory_comparison.png')
            plt.tight_layout()
            plt.savefig(memory_chart_path, dpi=300)
            plt.close()
            saved_charts.append(memory_chart_path)
            print(f"内存对比图已保存至: {memory_chart_path}")
    
        # 生成加速比图
        if chart_type in ['all']:
            # 计算加速比
            speedup_data = []
            for i in range(len(df)):
                if df['polars_time'][i] > 0:
                    speedup = df['pandas_time'][i] / df['polars_time'][i]
                else:
                    # 当Polars时间过小时，设置一个较大的加速比而不是0，并在图表上显示"极快"而不是具体数值。
                    speedup = 100  # 表示极大的加速比
                speedup_data.append(speedup)
        
            fig, ax = plt.subplots(figsize=(10, 6))
        
            # 绘制加速比柱状图
            bars = ax.bar(df['phase'], speedup_data, alpha=0.8, color='green')
        
            # 在柱状图上显示数值
            for bar in bars:
                height = bar.get_height()
                if height > 100:  # 如果加速比太大，显示"极快"而不是具体数值
                    ax.text(bar.get_x() + bar.get_width()/2., height, '极快', ha='center', va='bottom')
                else:
                    ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}x', ha='center', va='bottom')
        
            # 设置图表属性
            ax.set_xlabel('处理阶段')
            ax.set_ylabel('加速比 (Pandas/Polars)')
            ax.set_title('Polars相对于Pandas的加速比')
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df['phase'], rotation=45)
            ax.axhline(y=1, color='r', linestyle='-', alpha=0.3)
        
            # 保存图表
            speedup_chart_path = os.path.join(self.output_dir, 'performance_speedup_comparison.png')
            plt.tight_layout()
            plt.savefig(speedup_chart_path, dpi=300)
            plt.close()
            saved_charts.append(speedup_chart_path)
            print(f"加速比对比图已保存至: {speedup_chart_path}")
    
        # 生成总体性能雷达图
        if chart_type in ['all']:
            # 准备雷达图数据
            # 定义categories变量 - 修复雷达图问题
            categories = ['总耗时 (秒)', '总内存 (MB)']
        
            pandas_values = [df[df['phase'] == '总耗时']['pandas_time'].iloc[0], 
                           df[df['phase'] == '总耗时']['pandas_memory'].iloc[0]]
            polars_values = [df[df['phase'] == '总耗时']['polars_time'].iloc[0], 
                           df[df['phase'] == '总耗时']['polars_memory'].iloc[0]]
        
            # 归一化数据
            max_values = []
            for i in range(len(pandas_values)):
                max_val = max(pandas_values[i], polars_values[i])
                max_values.append(max_val if max_val > 0 else 1)  # 避免除零
        
            pandas_normalized = [v/max_values[i] if max_values[i] > 0 else 0 for i, v in enumerate(pandas_values)]
            polars_normalized = [v/max_values[i] if max_values[i] > 0 else 0 for i, v in enumerate(polars_values)]
        
            # 添加第一个值到末尾，使雷达图闭合
            categories_cycle = categories + [categories[0]]
            pandas_normalized_cycle = pandas_normalized + [pandas_normalized[0]]
            polars_normalized_cycle = polars_normalized + [polars_normalized[0]]
        
            # 计算角度
            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
            angles_cycle = angles + [angles[0]]
        
            # 创建雷达图
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
            # 绘制雷达图
            ax.plot(angles_cycle, pandas_normalized_cycle, 'o-', linewidth=2, label='Pandas+DuckDB')
            ax.plot(angles_cycle, polars_normalized_cycle, 'o-', linewidth=2, label='Polars+DuckDB')
            ax.fill(angles_cycle, pandas_normalized_cycle, alpha=0.25)
            ax.fill(angles_cycle, polars_normalized_cycle, alpha=0.25)
        
            # 设置图表属性
            ax.set_thetagrids(np.degrees(angles), categories)
            ax.set_title('总体性能对比雷达图 (数值越低越好)')
            ax.legend(loc='upper right')
        
            # 保存图表
            radar_chart_path = os.path.join(self.output_dir, 'performance_radar_comparison.png')
            plt.tight_layout()
            plt.savefig(radar_chart_path, dpi=300)
            plt.close()
            saved_charts.append(radar_chart_path)
            print(f"雷达图已保存至: {radar_chart_path}")
    
        return saved_charts

    def save_performance_data(self, performance_data):
        """
        将性能数据保存到CSV文件
    
        参数:
        performance_data: 性能数据字典
        """
        # 转换性能数据为适合CSV输出的格式
        phases = ['读取数据', '计算指标', '保存结果', '总耗时']
    
        csv_data = {
            'phase': phases,
            'pandas_time': [
                performance_data['pandas']['read_duckdb_time'],
                performance_data['pandas']['process_time'],
                performance_data['pandas']['save_time'],
                performance_data['pandas']['total_time']
            ],
            'polars_time': [
                performance_data['polars']['read_duckdb_time'],
                performance_data['polars']['process_time'],
                performance_data['polars']['save_time'],
                performance_data['polars']['total_time']
            ],
            'pandas_memory': [
                performance_data['pandas']['read_duckdb_memory'],
                performance_data['pandas']['process_memory'],
                performance_data['pandas']['save_memory'],
                performance_data['pandas']['process_memory']  # 使用处理阶段的内存作为总内存
            ],
            'polars_memory': [
                performance_data['polars']['read_duckdb_memory'],
                performance_data['polars']['process_memory'],
                performance_data['polars']['save_memory'],
                performance_data['polars']['process_memory']  # 使用处理阶段的内存作为总内存
            ]
        }
    
        # 创建DataFrame并保存到CSV
        df = pd.DataFrame(csv_data)
        csv_path = os.path.join(self.output_dir, 'performance_comparison_results.csv')
        df.to_csv(csv_path, index=False)
        print(f"性能比较结果已保存至: {csv_path}")

    def run_performance_analysis(self, limit=100000):
        """
        运行完整的性能分析
    
        参数:
        limit: 读取的数据行数
    
        返回值:
        tuple: (性能数据, 保存的图表文件路径列表)
        """
        # 进行详细性能比较
        performance_data = self.detailed_performance_comparison(limit)
    
        # 生成并保存所有类型的图表
        saved_charts = self.generate_comparison_charts(performance_data, chart_type='all')
    
        return performance_data, saved_charts


if __name__ == "__main__":
    # 数据库路径
    db_path = os.path.abspath('data/通达信数据_20251229.duckdb')
    csv_path = os.path.abspath('data/通达信数据_20251229.csv')
  
    # 创建性能分析器实例
    analyzer = PerformanceAnalyzer(db_path,csv_path)
  
    # 运行性能分析，设置limit为None处理全量数据
    analyzer.run_performance_analysis(limit=None)