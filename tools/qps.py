import time
import requests
import logging
import hashlib
import json
from typing import Dict, List, Any, Union
from datetime import datetime, timedelta
#qps：描述服务器单位时间内处理的请求数量。衡量服务器的处理请求能力
#bps: 描述网络传输速度，即每秒传输的数据量大小。衡量网络带宽和吞吐量




# 配置参数
CONFIG = {
    'appCode': 'JC_PIDLB',
    'token': '9b78f9ab773774f5b2c4b627ff007152',
    'api_url': 'http://deeplog-lb-api.jd.com/',
}

CONFIG_get_image = {
    'appCode': 'JC_PIDLB',
    'token': '9b78f9ab773774f5b2c4b627ff007152',
    'api_url': 'http://deeplog-ck-robot.jd.com/rest/api/convertDataIntoImages',
}

#鉴权
def get_auth_headers_get_image() -> dict:
    """生成鉴权请求头"""
    now = datetime.now()
    time_str = now.strftime("%H%M%Y%m%d")
    timestamp = str(int(time.time()))
    sign = hashlib.md5(f"#{CONFIG_get_image['token']}NP{time_str}".encode()).hexdigest()
    return {
        "Content-Type": "application/json",
        "appCode": CONFIG_get_image['appCode'],
        "sign": sign,
        "time": timestamp,
    }

def generate_timeseries_chart_url(
    data: Dict[str, Dict[str, float]],
    chart_type: str = "svg" ,
    metrics_name: str = None,
    base_line:float = None
) -> str:
    """
    生成时序图并返回在线预览链接
    Args:
        data: 时序数据 {指标名: {时间点: 数值}}     
    Returns:
        在线预览链接
    """
    # 根据chart_type设置filename
    if chart_type == "svg":
        filename = f"{metrics_name}.svg"
    # elif chart_type == "png":
    #     filename = "chart.png"
    # else:
    #     filename = "chart.png"  # 默认
    
    params = {
        "timeSeriesData": data,
        "filename": filename,  # 包含后缀的文件名
        "title": metrics_name,
        "width":1500,
        "height":700,
        "ossType" : 1,
        "showLegend":True,
        "usingBaseLine":True,
        "baseLine":base_line,
        "baseLineName":"阈值"
    }
    resp = requests.post(
        CONFIG_get_image['api_url'],
        headers=get_auth_headers_get_image(),
        json=params,
        timeout=300
    )
    result = resp.json()
    
    # print("生成图片的信息：\n")
    # print(result)
    if result.get("code") == 200:
        return result["data"]["src"]
    else:
        raise Exception(f"图表生成失败: {result.get('msg', '未知错误')}")


    
def get_yesterday_time(cluster_name, start_time, end_time):
    def shift(time_str):
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return (dt - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    return cluster_name, shift(start_time), shift(end_time)


def get_previous_30_minutes(device_id, time1, time2):
    def shift(time_str):
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return (dt - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    
    return device_id, shift(time1), shift(time2)

def datetime_str_to_timestamp(dt_str: str) -> int:
    """将时间字符串转换为毫秒时间戳"""
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        return int(dt.timestamp() * 1000)
    except ValueError:
        # 尝试容错处理，如果只有日期
        try:
            dt = datetime.strptime(dt_str, '%Y-%m-%d')
            return int(dt.timestamp() * 1000)
        except ValueError:
            raise ValueError(f"时间格式错误: {dt_str}，应为 'YYYY-MM-DD HH:MM:SS'")
 
def get_np_auth_headers(app_code: str, token: str) -> dict:
    now = datetime.now()
    # 修正时间格式:%H%M%Y%m%d (小时分钟年月日)
    time_str = now.strftime("%H%M%Y%m%d")
    timestamp = str(int(time.time() * 1000))
    # 签名字符串
    sign_str = f"#{token}NP{time_str}"
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
 
    headers = {
        "Content-Type": "application/json;charset=utf-8",  
        "appCode": app_code,
        "sign": sign,
        "time": timestamp,
    }
    return headers
 
def get_cluster_qps_api(cluster_name: str, start_time: str, end_time: str) -> dict:
    """
    获取集群流量QPS信息 (底层接口调用)
    
    Args:
        cluster_name: 集群名称
        start_time: 开始时间字符串 (YYYY-MM-DD HH:MM:SS)
        end_time: 结束时间字符串 (YYYY-MM-DD HH:MM:SS)
        
    Returns:
        dict: 包含QPS数据的字典或错误信息
    """
    # 转换时间格式
    try:
        start_ts = datetime_str_to_timestamp(start_time)
        end_ts = datetime_str_to_timestamp(end_time)
    except ValueError as e:
        return {"code": -1, "message": str(e)}
 
    headers = get_np_auth_headers(CONFIG['appCode'], CONFIG['token'])
    url = f"{CONFIG['api_url']}v1/search"
    
    params = {
        "size": 10,  # 这里的size可能需要注意，如果是大量数据点可能需要调整或分页
        "bizName": "lbha",
        "resource": "count",
        "timeRange": {
            "start": start_ts,
            "end": end_ts
        },
        "interval": "10s", 
        "match": [{
            "eq": {
                "lb-node-name": [cluster_name]
            } 
        }],
        "algorithm": {
            "algorithmName": "sum",
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=params, timeout=30)
        response.raise_for_status()
        raw_data = response.json()
        return raw_data
        
    except requests.exceptions.RequestException as e:
        error_info = {
            "code": -1,
            "message": f"请求失败: {str(e)}",
            "error_type": type(e).__name__
        }
        if hasattr(e, 'response') and e.response is not None:
            error_info["response_text"] = e.response.text
            error_info["status_code"] = e.response.status_code
        return error_info
# --- 数据提取与转换 ---

def extract_values(data):
    """
    从接口返回的数据中提取所有值构成列表
    """
    # 确保数据格式正确
    if not isinstance(data, dict) or 'response' not in data:
        print(data)
        raise ValueError("数据格式不正确，缺少'response'字段")
    
    # 提取所有value值
    values = []
    for item in data['response']:
        if isinstance(item, dict) and 'value' in item:
            values.append(item['value'])
    return values


def analyze_data(A, B, C,x):
    """
    计算数据的日环比、短期环比、均值并判断是否超过阈值。
    环比结果格式化为箭头+符号+百分比的字符串。
    上涨：↑+xx.xx%
    下降：↓-xx.xx%
    
    参数:
    A (list): 当前时段数据列表
    B (list): 上一个周期数据列表 (用于日环比)
    C (list): 短期历史数据列表 (用于短期环比)
    x (int): 阈值
    
    返回:
    dict: 包含计算结果的字典
    """
    
    # 计算均值，处理列表为空的情况以防除零错误
    avg_A = sum(A) / len(A) if A else 0
    avg_B = sum(B) / len(B) if B else 0
    avg_C = sum(C) / len(C) if C else 0
    
    # 计算日环比数值
    try:
        day_ratio_val = (avg_A - avg_B) / avg_B
    except ZeroDivisionError:
        day_ratio_val = 0
 
    # 计算短期环比数值
    try:
        short_ratio_val = (avg_A - avg_C) / avg_C
    except ZeroDivisionError:
        short_ratio_val = 0
 
    # 格式化逻辑：上涨用↑和+，下降用↓和-
    # 这里的符号与数值本身的正负号一致
    
    # 日环比字符串生成
    if day_ratio_val >= 0:
        day_ratio_str = f"↑{day_ratio_val * 100:+.2f}%"
    else:
        day_ratio_str = f"↓{day_ratio_val * 100:+.2f}%"
 
    # 短期环比字符串生成
    if short_ratio_val >= 0:
        short_ratio_str = f"↑{short_ratio_val * 100:+.2f}%"
    else:
        short_ratio_str = f"↓{short_ratio_val * 100:+.2f}%"
 
    # 均值
    mean_val = int(avg_A)
 
    # 初始化告警信息
    alert_messages = []
    
 # 判断日环比绝对值是否 > 20%（修改为20%）
    if abs(day_ratio_val * 100) > 20:
        alert_messages.append(f"日环比>{20}%")
        
    # 判断短期环比绝对值是否 > 20%（修改为20%）
    if abs(short_ratio_val * 100) > 20:
        alert_messages.append(f"短期环比>{20}%")
    
    # 判断最大值是否超过固定阈值
    max_A = max(A) if A else 0
    if max_A >= x:
        alert_messages.append(f"Max = {max_A} >{x} (阈值)")
        # print(max_A)
    
    # 组合最终告警文本
    if alert_messages:
        threshold_status = "异常 ," + ",".join(alert_messages)
    else:
        threshold_status = "正常"
 
    return {
        "日环比": day_ratio_str,
        "短期环比": short_ratio_str,
        "均值": mean_val,
        "是否告警": threshold_status
    }


def day_add_1(data):
    """
    将字典中所有时间键整体向后推移1天
    """
    result = {}
    for metric, time_dict in data.items():
        new_time_dict = {}
        for time_str, value in time_dict.items():
            # 将字符串时间转换为datetime，加上1天，再转回字符串
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            new_dt = dt + timedelta(days=1)
            new_time_str = new_dt.strftime("%Y-%m-%d %H:%M:%S")
            new_time_dict[new_time_str] = value
        
        result[metric] = new_time_dict
    
    return result
def day_add_30(data, minutes=30):
    """
    将字典中所有时间键整体向后推移指定分钟数
    
    Args:
        data: 包含时间戳作为键的嵌套字典
        minutes: 要推移的分钟数（默认30分钟）
        
    Returns:
        更新后的字典
    """
    return {
        metric: {
            (datetime.strptime(t, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=minutes))
            .strftime("%Y-%m-%d %H:%M:%S"): v
            for t, v in time_dict.items()
        }
        for metric, time_dict in data.items()
    }
    
def merge_dicts(dict1, dict2, dict3):
    """
    合并两个监控指标字典
    如果键相同，第二个字典的值会覆盖第一个字典的值
    """
    return {**dict1, **dict2, **dict3}

def extract_qps_timeSeriesData(response_data):
    """
    提取并格式化接口返回的数据
    
    Args:
        response_data: 接口返回的原始数据（字典格式）
    
    Returns:
        dict: 格式化后的数据，格式如sample_data
    """
    try:
        # 解析响应数据
        data_list = response_data.get('response', [])
        if not data_list:
            return {"QPS": {}}
        
        # 创建结果字典
        result = {"QPS": {}}
        
        # 处理每个数据点
        for item in data_list:
            timestamp = item.get('time')
            value = item.get('value')
            
            if timestamp is not None and value is not None:
                # 将毫秒时间戳转换为可读时间格式
                # 注意：这里假设时间戳是毫秒级
                dt = datetime.fromtimestamp(timestamp / 1000)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                
                # 将值转换为浮点数（可根据需要调整）
                formatted_value = float(value)
                
                # 添加到结果中
                result["QPS"][formatted_time] = formatted_value
        
        return result
    
    except Exception as e:
        print(f"数据处理出错: {e}")
        return {"QPS": {}}


    # name="get_cluster_qps_analysis",
    # description="获取指定集群时间范围内的QPS(流量)指标分析结果",
    # args_schema={
    #     "type": "object",
    #     "properties": {
    #         "groupname": {"type": "string", "description": "集群名称(例如: ga-lan-jdns1)"},
    #         "begin_time": {
    #             "type": "string",
    #             "description": "开始时间(例如: 2026-01-13 09:00:00),要求格式 YYYY-MM-DD HH:MM:SS ",
    #         },
    #         "end_time": {
    #             "type": "string",
    #             "description": "结束时间(例如: 2026-01-13 09:30:00)，要求格式 YYYY-MM-DD HH:MM:SS ",
    #         },
    #     },
    #     "required": ["groupname", "begin_time", "end_time"],
    # }
def get_cluster_qps_analysis(groupname, begin_time, end_time):
    """
    获取三个时间段的集群QPS数据
    """
    # 获取昨天时间的参数
    B_groupname, B_begin_time, B_end_time = get_yesterday_time(groupname, begin_time, end_time)
    # 获取前30分钟的参数
    C_groupname, C_begin_time, C_end_time = get_previous_30_minutes(groupname, begin_time, end_time)
    
    # 调用API函数获取原始数据
    A_raw = get_cluster_qps_api(groupname, begin_time, end_time)
    B_raw = get_cluster_qps_api(B_groupname, B_begin_time, B_end_time)
    C_raw = get_cluster_qps_api(C_groupname, C_begin_time, C_end_time)
    
    A_ts = extract_qps_timeSeriesData(A_raw)
    B_ts = extract_qps_timeSeriesData(B_raw)
    C_ts = extract_qps_timeSeriesData(C_raw)
    
    if "QPS" in A_ts:
        A_ts["📊 当前趋势"] = A_ts.pop("QPS")
    if "QPS" in B_ts:
        B_ts["📈 日环比"] = B_ts.pop("QPS")
    if "QPS" in C_ts:
        C_ts["📈 30分钟环比"] = C_ts.pop("QPS")
    
    merge_data = merge_dicts(A_ts, day_add_1(B_ts), day_add_30(C_ts))

    image_url = generate_timeseries_chart_url(merge_data,"svg","QPS",1300000)

    
    # 从API返回数据中提取QPS值列表
    A_qps_data = extract_values(A_raw)
    B_qps_data = extract_values(B_raw)
    C_qps_data = extract_values(C_raw)

    obj = {
        "info":analyze_data(A_qps_data, B_qps_data, C_qps_data,1300000),
        "image_url": image_url,
    }
    

    return obj

# r = get_cluster_qps_analysis("lf-lan-ha1","2026-02-05 08:00:00","2026-02-05 8:30:00")
# print(r)