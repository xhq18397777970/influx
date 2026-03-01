import time
import requests
import logging
import hashlib
import numpy as np
from typing import Dict
from datetime import datetime, timedelta
import json

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
# --- 鉴权与请求模块 ---
 
def npa_summary_data(postdata, apiurl, method="POST"):
    user = "xiehanqi.jackson"
    ctime = str(int(time.time()))
    new_key = f"{user}|{ctime}"
    # 计算签名
    api_header_val = f"{hashlib.md5(new_key.encode()).hexdigest()}|{ctime}"
    url = f'http://npa-test.jd.com{apiurl}'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {'auth-api': api_header_val, 'auth-user': user, 'Content-Type': "application/json", 'User-Agent': user_agent}
    try:
        if method == "POST":
            response = requests.post(url, json=postdata, headers=headers)
        elif method == "GET":
            response = requests.get(url, params=postdata, headers=headers)
        else:
            return {}
        response.raise_for_status()
        logging.info(f"code:{response.status_code}, response:{response.text}")
        return response.json()
    except requests.RequestException as e:
        logging.error(f"API request error: {e}")
        return {}
 
def get_cluster_tp_api(groupname,begin_time,end_time):
    postdata = {
        "groupname": groupname,
        "begin_time": begin_time,
        "end_time": end_time
    }
    apiurl = "/prod-api/api/v2/analysis/deeplog/querytpn?format=json"
    result = npa_summary_data(postdata, apiurl)
    # --- 补充错误处理 ---
    # 1. 检查基础请求是否成功 (npa_summary_data 可能返回 None)
    if result is None:
        logging.error("Failed to fetch data due to request exception.")
        return {"status": "error", "message": "Request failed", "code": -1}
 
    # 2. 检查业务状态码 (假设 API 返回格式中包含 code 字段)
    # 很多 API 返回格式为 {"code": 200, "data": ...} 或 {"code": 500, "msg": "error"}
    if "code" in result:
        business_code = result.get("code")
        # 假设 200 表示成功，其他均为业务错误
        if business_code != 200: 
            error_msg = result.get("message", result.get("msg", "Unknown business error"))
            logging.error(f"API business error: code={business_code}, message={error_msg}")
            return {
                "status": "error", 
                "message": error_msg, 
                "code": business_code,
                "raw_response": result
            }
 
    # 3. 检查数据内容是否存在 (防止 code=200 但 data 为空)
    # 假设有效数据在 'data' 字段中
    # if "data" not in result or not result["data"]:
    #     logging.warning("API response successful but no data found.")
    #     return {"status": "empty", "message": "No data available", "code": 0}
 
    # 全部检查通过，返回完整结果
    return result
 
# --- 数据处理模块 ---
 
def extract_values(response):
    """
    计算接口返回数据中 connect_delay = total_delay_tp - srv_delay_tp 。
    """
    diff_series = []
    
    # 直接获取数据，不再判断 code==200 和 data 是否存在
    data_content = response.get('data', {})
    series_data = data_content.get('series_data', [])
    
    srv_delay_vals = []
    total_delay_vals = []
    
    # 提取特定序列的数据
    if isinstance(series_data, list):
        for item in series_data:
            if item.get('name') == 'srv_delay_tp':
                srv_delay_vals = item.get('value', [])
            elif item.get('name') == 'total_delay_tp':
                total_delay_vals = item.get('value', [])
    
    # 计算差值 (total_delay_tp - srv_delay_tp)
    if srv_delay_vals and total_delay_vals:
        min_len = min(len(srv_delay_vals), len(total_delay_vals))
        for i in range(min_len):
            diff_series.append(total_delay_vals[i] - srv_delay_vals[i])
            
    return diff_series
 
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
    # print(f"当前时段的均值: {mean_val}")
    # print(f"短期均值: {avg_C}")
 
    # 初始化告警信息
    alert_messages = []
    
    # 判断日环比是否 > 30%
    if day_ratio_val * 100 > 30:
        alert_messages.append(f"日环比>30%")
        
    # 判断短期环比是否 > 30%
    if short_ratio_val * 100 > 30:
        alert_messages.append(f"短期环比>30%")
    
    # 判断最大值是否超过固定阈值
    max_A = max(A) if A else 0
    if max_A >= x:
        alert_messages.append(f"Max = {max_A} >{x} (阈值)")
        print(max_A)
    
    # 组合最终告警文本
    if alert_messages:
        threshold_status = "异常 ," + ",".join(alert_messages)
    else:
        threshold_status = "正常"
    
    #----------------------TP_90、TP_95、峰值 添加
    # 排序数据
    sorted_data = sorted([float(x) for x in A])
    n = len(sorted_data)
    
    # 峰值（最大值）
    peak = max(sorted_data)
    
    # P90（第90百分位）
    idx_90 = int(0.9 * n)
    p90 = sorted_data[idx_90] if idx_90 < n else sorted_data[-1]
    
    # P95（第95百分位）
    idx_95 = int(0.95 * n)
    p95 = sorted_data[idx_95] if idx_95 < n else sorted_data[-1]
    return {
        "日环比": day_ratio_str,
        "短期环比": short_ratio_str,
        "均值": mean_val,
        "峰值":peak,
        "TP_90":p90,
        "TP_95":p95,
        "是否告警": threshold_status
    }
def extract_connect_delay_timeSeriesData(api_response):
    """
    转换API响应数据为指定格式
    
    Args:
        api_response: 原始的API响应字典
    
    Returns:
        dict: 转换后的格式
    """
    try:
        # 解析JSON字符串（如果传入的是字符串）
        if isinstance(api_response, str):
            data = json.loads(api_response)
        else:
            data = api_response
        
        if data.get('code') != 200:
            raise ValueError(f"API返回错误: {data.get('message', 'Unknown error')}")
        
        chart_data = data['data']
        x_data = chart_data['x_data']
        
        # 查找系列数据
        series = {}
        for s in chart_data['series_data']:
            series[s['name']] = s['value']
        
        srv_delay = series.get('srv_delay_tp', [])
        total_delay = series.get('total_delay_tp', [])
        
        if len(x_data) != len(srv_delay) or len(x_data) != len(total_delay):
            raise ValueError("x轴数据与y轴数据长度不匹配")
        
        # 计算connect_delay
        result = {"connect_delay": {}}
        for timestamp, srv_val, total_val in zip(x_data, srv_delay, total_delay):
            connect_delay = total_val - srv_val
            result["connect_delay"][timestamp] = round(connect_delay, 1)
        
        return result
        
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"数据格式错误: {str(e)}")
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


# --- 综合分析模块 ---
    # name="get_connect_delay_analysis",
    # description="获取集群建连耗时(TP)分析结果",
    # args_schema={
    #     "type": "object",
    #     "properties": {
    #         "groupname": {"type": "string", "description": "集群名称(例如: lf-lan-ha1)"},
    #         "begin_time": {
    #             "type": "string",
    #             "description": "开始时间(例如: 2026-01-14 11:00:00)",
    #         },
    #         "end_time": {
    #             "type": "string",
    #             "description": "结束时间(例如: 2026-01-14 11:30:00)",
    #         },
    #     },
    #     "required": ["groupname", "begin_time", "end_time"],
    # }
def get_cluster_connect_delay_analysis(groupname, begin_time, end_time):
    """
    获取三个时间段的集群QPS数据
    """
    # 获取昨天时间的参数
    B_groupname, B_begin_time, B_end_time = get_yesterday_time(groupname, begin_time, end_time)
    # 获取前30分钟的参数
    C_groupname, C_begin_time, C_end_time = get_previous_30_minutes(groupname, begin_time, end_time)
    
    # 调用API函数获取原始数据
    A_raw = get_cluster_tp_api(groupname, begin_time, end_time)
    B_raw = get_cluster_tp_api(B_groupname, B_begin_time, B_end_time)
    C_raw = get_cluster_tp_api(C_groupname, C_begin_time, C_end_time)
    
    
    A_ts = extract_connect_delay_timeSeriesData(A_raw)
    B_ts = extract_connect_delay_timeSeriesData(B_raw)
    C_ts = extract_connect_delay_timeSeriesData(C_raw)
    
    if "connect_delay" in A_ts:
        A_ts["📊 当前趋势"] = A_ts.pop("connect_delay")
        
    if "connect_delay" in B_ts:
        B_ts["📈 日环比"] = B_ts.pop("connect_delay")
        
    if "connect_delay" in C_ts:
        C_ts["📈 30分钟环比"] = C_ts.pop("connect_delay")
    
    merge_data = merge_dicts(A_ts, day_add_1(B_ts), day_add_30(C_ts))
    
    image_url = generate_timeseries_chart_url(merge_data,"svg","LB建连耗时",20)

    # 从API返回数据中提取QPS值列表
    A_tp_data = extract_values(A_raw)
    B_tp_data = extract_values(B_raw)
    C_tp_data = extract_values(C_raw)
    
    
    obj = {
        "info":analyze_data(A_tp_data, B_tp_data, C_tp_data,20),
        "image_url":image_url
    }
    return obj

# r = get_cluster_connect_delay_analysis("lf-lan-ha1","2026-02-05 10:00:00","2026-02-05 10:30:00")
# print(r)
