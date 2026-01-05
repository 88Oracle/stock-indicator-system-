"""
统计系统中所有技术指标的总数

扫描indicators.py中的所有@staticmethod方法,统计每个类别的指标数量
"""

import sys
from pathlib import Path
import re

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.utils import Logger


def count_indicators():
    """统计indicators.py中的所有指标方法"""

    indicators_file = project_root / 'core' / 'indicators.py'

    with open(indicators_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 定义所有指标类
    indicator_classes = [
        'TrendIndicators',
        'MomentumIndicators',
        'VolatilityIndicators',
        'VolumeIndicators',
        'OscillatorIndicators',
        'PriceIndicators',
        'AdvancedTrendIndicators',
        'AdvancedVolatilityIndicators',
        'AdvancedVolumeIndicators',
        'AdvancedOscillatorIndicators',
        'ExtraIndicators'
    ]

    logger = Logger()
    logger.section("技术指标统计")

    total_methods = 0
    class_methods = {}

    for class_name in indicator_classes:
        # 查找类定义的开始
        class_pattern = rf'class {class_name}:'
        class_match = re.search(class_pattern, content)

        if not class_match:
            continue

        # 从类定义开始到下一个类定义或文件结尾
        start_pos = class_match.end()
        next_class_pattern = r'\nclass \w+:'
        next_class_match = re.search(next_class_pattern, content[start_pos:])

        if next_class_match:
            end_pos = start_pos + next_class_match.start()
            class_content = content[start_pos:end_pos]
        else:
            class_content = content[start_pos:]

        # 查找所有@staticmethod
        method_pattern = r'@staticmethod\s+def\s+(\w+)\('
        methods = re.findall(method_pattern, class_content)

        if methods:
            class_methods[class_name] = methods
            total_methods += len(methods)

    # 打印结果
    logger.info(f"指标类别数量: {len(class_methods)}\n")

    for class_name, methods in class_methods.items():
        logger.info(f"{class_name}: {len(methods)}个指标")
        for method in methods:
            print(f"  - {method}")
        print()

    logger.section("总计")
    logger.success(f"技术指标总数: {total_methods} 个")

    # 新增指标统计
    if 'ExtraIndicators' in class_methods:
        extra_count = len(class_methods['ExtraIndicators'])
        logger.info(f"其中新增指标: {extra_count} 个 (ExtraIndicators类)")

    return total_methods, class_methods


def main():
    """主函数"""
    total, class_methods = count_indicators()

    logger = Logger()
    logger.section("指标详情")

    # 按类别分组展示
    categories = {
        '趋势指标': ['TrendIndicators', 'AdvancedTrendIndicators'],
        '动量指标': ['MomentumIndicators'],
        '波动率指标': ['VolatilityIndicators', 'AdvancedVolatilityIndicators'],
        '成交量指标': ['VolumeIndicators', 'AdvancedVolumeIndicators'],
        '震荡指标': ['OscillatorIndicators', 'AdvancedOscillatorIndicators'],
        '价格指标': ['PriceIndicators'],
        '额外指标': ['ExtraIndicators']
    }

    for category, classes in categories.items():
        count = sum(len(class_methods.get(c, [])) for c in classes)
        if count > 0:
            logger.info(f"{category}: {count} 个")

    logger.section("系统能力")
    logger.info(f"✓ 支持 {total} 种技术指标")
    logger.info(f"✓ 涵盖 7 大类别")
    logger.info(f"✓ 基于 Polars 高性能计算")
    logger.info(f"✓ 单次计算可生成 76+ 个指标列")


if __name__ == '__main__':
    main()
