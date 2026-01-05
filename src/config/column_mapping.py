"""
列名映射配置
用于将标准列名映射到数据库中的实际列名
"""

# 标准列名 -> 实际列名的映射
COLUMN_MAPPING = {
    # 基础价格列
    '收盘': '收盘价',
    '开盘': '今开',
    '最高': '最高',
    '最低': '最低',
    '昨收': '昨收',
    '现价': '现价',

    # 成交量相关
    '成交量': '总量',
    '总量': '总量',
    '成交额': '总金额',

    # 日期和代码
    '日期': '日期',
    '代码': '代码',
    '名称': '名称',
}

def get_mapped_column(standard_name: str) -> str:
    """
    获取映射后的列名

    参数:
    standard_name: 标准列名

    返回:
    str: 实际列名
    """
    return COLUMN_MAPPING.get(standard_name, standard_name)
