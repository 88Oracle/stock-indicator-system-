"""
性能可视化模块
功能：生成性能对比图表
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import sys
import os
from typing import Dict, List

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 添加src目录到路径 - 确保在所有导入之前
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(script_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 项目模块导入
from core.utils import Logger, FileUtils  # noqa


class PerformanceVisualizer:
    """性能可视化类"""

    def __init__(self, output_dir: str = None):
        """
        初始化可视化器

        参数:
        output_dir: 输出目录（默认为 project/output/charts）
        """
        if output_dir is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(script_dir, "output", "charts")

        self.output_dir = output_dir
        FileUtils.ensure_dir(output_dir)

    def plot_performance_comparison(self, polars_result: Dict, pandas_result: Dict, save_name: str = "performance_comparison.png"):
        """
        绘制性能对比柱状图

        参数:
        polars_result: Polars测试结果
        pandas_result: Pandas测试结果
        save_name: 保存文件名
        """
        Logger.info(f"生成性能对比图表...")

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Polars vs Pandas 性能对比', fontsize=16, fontweight='bold')

        # 1. 执行时间对比
        ax1 = axes[0, 0]
        categories = ['数据读取', '指标计算', '结果保存', '总耗时']
        polars_times = [
            polars_result.get('read_time', 0),
            polars_result.get('calc_time', 0),
            polars_result.get('save_time', 0),
            polars_result.get('total_time', 0)
        ]
        pandas_times = [
            pandas_result.get('read_time', 0),
            pandas_result.get('calc_time', 0),
            pandas_result.get('save_time', 0),
            pandas_result.get('total_time', 0)
        ]

        x = np.arange(len(categories))
        width = 0.35

        bars1 = ax1.bar(x - width/2, polars_times, width, label='Polars', color='#3498db')
        bars2 = ax1.bar(x + width/2, pandas_times, width, label='Pandas', color='#e74c3c')

        ax1.set_xlabel('操作类型')
        ax1.set_ylabel('时间 (秒)')
        ax1.set_title('执行时间对比')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}s',
                        ha='center', va='bottom', fontsize=8)

        # 2. 加速比
        ax2 = axes[0, 1]
        speedups = [
            pandas_times[i] / polars_times[i] if polars_times[i] > 0 else 0
            for i in range(len(categories))
        ]

        bars = ax2.bar(categories, speedups, color=['#2ecc71' if s >= 1 else '#e67e22' for s in speedups])
        ax2.axhline(y=1, color='red', linestyle='--', label='基准线 (1x)')
        ax2.set_xlabel('操作类型')
        ax2.set_ylabel('加速比 (倍)')
        ax2.set_title('Polars 相对 Pandas 的加速比')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}x',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

        # 3. 内存使用对比
        ax3 = axes[1, 0]
        memory_data = [
            polars_result.get('memory_used_mb', 0),
            pandas_result.get('memory_used_mb', 0)
        ]
        frameworks = ['Polars', 'Pandas']
        colors = ['#3498db', '#e74c3c']

        bars = ax3.bar(frameworks, memory_data, color=colors)
        ax3.set_ylabel('内存使用 (MB)')
        ax3.set_title('内存使用对比')
        ax3.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f} MB',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        # 4. 处理速度对比
        ax4 = axes[1, 1]
        speed_data = [
            polars_result.get('rows_per_second', 0),
            pandas_result.get('rows_per_second', 0)
        ]

        bars = ax4.bar(frameworks, speed_data, color=colors)
        ax4.set_ylabel('处理速度 (行/秒)')
        ax4.set_title('数据处理速度对比')
        ax4.grid(axis='y', alpha=0.3)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:,.0f}\n行/秒',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

        plt.tight_layout()

        # 保存图表
        output_path = os.path.join(self.output_dir, save_name)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        Logger.success(f"图表已保存: {output_path}")

        plt.close()

    def plot_time_breakdown_pie(self, result: Dict, framework_name: str, save_name: str = None):
        """
        绘制时间分解饼图

        参数:
        result: 测试结果
        framework_name: 框架名称 (Polars/Pandas)
        save_name: 保存文件名
        """
        if save_name is None:
            save_name = f"time_breakdown_{framework_name.lower()}.png"

        Logger.info(f"生成 {framework_name} 时间分解饼图...")

        fig, ax = plt.subplots(figsize=(10, 8))

        # 数据
        labels = ['数据读取', '指标计算', '结果保存']
        sizes = [
            result.get('read_time', 0),
            result.get('calc_time', 0),
            result.get('save_time', 0)
        ]
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        explode = (0.1, 0, 0)  # 突出显示第一个扇区

        # 绘制饼图
        wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels,
                                          colors=colors, autopct='%1.1f%%',
                                          shadow=True, startangle=90)

        # 美化
        for text in texts:
            text.set_fontsize(12)
            text.set_fontweight('bold')

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')

        ax.set_title(f'{framework_name} 时间分解\n(总耗时: {result.get("total_time", 0):.2f} 秒)',
                    fontsize=14, fontweight='bold', pad=20)

        # 添加图例，显示实际时间
        legend_labels = [f'{label}: {size:.2f}秒' for label, size in zip(labels, sizes)]
        ax.legend(legend_labels, loc='best', fontsize=10)

        plt.axis('equal')

        # 保存图表
        output_path = os.path.join(self.output_dir, save_name)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        Logger.success(f"图表已保存: {output_path}")

        plt.close()

    def plot_scalability_test(self, test_results: List[Dict], save_name: str = "scalability_test.png"):
        """
        绘制数据规模与性能关系曲线图

        参数:
        test_results: 多个测试结果的列表
        save_name: 保存文件名
        """
        Logger.info(f"生成可扩展性测试图表...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('数据规模与性能关系', fontsize=16, fontweight='bold')

        # 按数据规模排序
        test_results = sorted(test_results, key=lambda x: x.get('rows', 0))

        # 提取数据
        data_sizes = [r.get('rows', 0) for r in test_results]
        polars_times = [r.get('polars', {}).get('total_time', 0) for r in test_results]
        pandas_times = [r.get('pandas', {}).get('total_time', 0) for r in test_results]

        # 1. 执行时间曲线
        ax1.plot(data_sizes, polars_times, marker='o', linewidth=2,
                label='Polars', color='#3498db', markersize=8)
        ax1.plot(data_sizes, pandas_times, marker='s', linewidth=2,
                label='Pandas', color='#e74c3c', markersize=8)

        ax1.set_xlabel('数据规模 (行数)', fontsize=12)
        ax1.set_ylabel('执行时间 (秒)', fontsize=12)
        ax1.set_title('执行时间 vs 数据规模', fontsize=13, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)

        # 添加数值标签
        for i, (x, y1, y2) in enumerate(zip(data_sizes, polars_times, pandas_times)):
            if i % 2 == 0:  # 只显示部分标签，避免拥挤
                ax1.annotate(f'{y1:.1f}s', (x, y1), textcoords="offset points",
                           xytext=(0,10), ha='center', fontsize=8)
                ax1.annotate(f'{y2:.1f}s', (x, y2), textcoords="offset points",
                           xytext=(0,-15), ha='center', fontsize=8)

        # 2. 加速比曲线
        speedups = [pandas_times[i] / polars_times[i] if polars_times[i] > 0 else 0
                   for i in range(len(data_sizes))]

        ax2.plot(data_sizes, speedups, marker='D', linewidth=2,
                color='#2ecc71', markersize=8, label='加速比')
        ax2.axhline(y=1, color='red', linestyle='--', label='基准线 (1x)', alpha=0.7)

        ax2.set_xlabel('数据规模 (行数)', fontsize=12)
        ax2.set_ylabel('加速比 (倍)', fontsize=12)
        ax2.set_title('Polars 加速比 vs 数据规模', fontsize=13, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)

        # 添加数值标签
        for i, (x, y) in enumerate(zip(data_sizes, speedups)):
            if i % 2 == 0:
                ax2.annotate(f'{y:.2f}x', (x, y), textcoords="offset points",
                           xytext=(0,10), ha='center', fontsize=9, fontweight='bold')

        plt.tight_layout()

        # 保存图表
        output_path = os.path.join(self.output_dir, save_name)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        Logger.success(f"图表已保存: {output_path}")

        plt.close()

    def plot_indicator_comparison(self, indicator_counts: Dict, save_name: str = "indicator_comparison.png"):
        """
        绘制指标数量对比图

        参数:
        indicator_counts: 各类指标的数量字典
        save_name: 保存文件名
        """
        Logger.info(f"生成指标数量对比图...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('技术指标统计', fontsize=16, fontweight='bold')

        # 数据
        categories = list(indicator_counts.keys())
        counts = list(indicator_counts.values())

        # 1. 柱状图
        colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
        bars = ax1.barh(categories, counts, color=colors)

        ax1.set_xlabel('指标数量', fontsize=12)
        ax1.set_title('各类指标数量分布', fontsize=13, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)

        # 添加数值标签
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{int(width)}',
                    ha='left', va='center', fontsize=10, fontweight='bold')

        # 2. 饼图
        ax2.pie(counts, labels=categories, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=90)
        ax2.set_title('指标类型占比', fontsize=13, fontweight='bold')

        plt.tight_layout()

        # 保存图表
        output_path = os.path.join(self.output_dir, save_name)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        Logger.success(f"图表已保存: {output_path}")

        plt.close()

    def generate_all_charts(self, polars_result: Dict, pandas_result: Dict):
        """
        生成所有图表

        参数:
        polars_result: Polars测试结果
        pandas_result: Pandas测试结果
        """
        Logger.section("生成性能分析图表")

        # 1. 性能对比图
        self.plot_performance_comparison(polars_result, pandas_result)

        # 2. Polars 时间分解
        self.plot_time_breakdown_pie(polars_result, "Polars")

        # 3. Pandas 时间分解
        self.plot_time_breakdown_pie(pandas_result, "Pandas")

        # 4. 指标数量统计
        indicator_counts = {
            '趋势指标': 3,
            '动量指标': 3,
            '波动率指标': 4,
            '成交量指标': 3,
            '震荡指标': 3,
            '价格指标': 2,
            '高级趋势': 3,
            '高级波动率': 3,
            '高级成交量': 4,
            '高级震荡': 5
        }
        self.plot_indicator_comparison(indicator_counts)

        Logger.success(f"所有图表已生成完成！保存在: {self.output_dir}")


# 测试代码
if __name__ == "__main__":
    Logger.section("性能可视化测试")

    # 创建测试数据
    polars_result = {
        'framework': 'Polars',
        'rows': 218,
        'read_time': 0.096,
        'calc_time': 0.076,
        'save_time': 0.020,
        'total_time': 0.172,
        'memory_used_mb': 57.94,
        'rows_per_second': 2853
    }

    pandas_result = {
        'framework': 'Pandas',
        'rows': 218,
        'read_time': 0.047,
        'calc_time': 0.109,
        'save_time': 0.020,
        'total_time': 0.156,
        'memory_used_mb': 8.86,
        'rows_per_second': 2000
    }

    # 创建可视化器
    visualizer = PerformanceVisualizer()

    # 生成所有图表
    visualizer.generate_all_charts(polars_result, pandas_result)

    Logger.success("测试完成！")
