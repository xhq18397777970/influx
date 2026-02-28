import time
import requests
import logging
import hashlib
import json
import sys
import os
import uuid

from datetime import datetime, timedelta
import time
import requests
from datetime import datetime
import hashlib
from typing import Dict
import random

from concurrent.futures import ThreadPoolExecutor
def parallel_execute(tasks):
    """
    并行执行多个任务
    
    Args:
        tasks: 任务列表，每个任务是一个元组 (func, *args)
    
    Returns:
        list: 按任务顺序返回的结果列表
    """
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        # 提交所有任务
        futures = [executor.submit(task[0], *task[1:]) for task in tasks]
        # 按顺序获取结果
        return [future.result() for future in futures]

CONFIG = {
    'appCode': 'JC_PIDLB',
    'token': '9b78f9ab773774f5b2c4b627ff007152',
    'api_url': 'http://deeplog-ck-robot.jd.com/rest/api/convertDataIntoImages',
}


#鉴权
def get_auth_headers() -> dict:
    """生成鉴权请求头"""
    now = datetime.now()
    time_str = now.strftime("%H%M%Y%m%d")
    timestamp = str(int(time.time()))
    sign = hashlib.md5(f"#{CONFIG['token']}NP{time_str}".encode()).hexdigest()
    return {
        "Content-Type": "application/json",
        "appCode": CONFIG['appCode'],
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
        filename = f"{metrics_name}_{uuid.uuid4().hex}.{chart_type}"
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
        CONFIG['api_url'],
        headers=get_auth_headers(),
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


from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta

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

# 鉴权
def npa_summary_data(postdata, apiurl, method="POST"):
    user = "xiehanqi.jackson"
    ctime = str(int(time.time()))
    new_key = f"{user}|{ctime}"
    # 计算哈希值
    api_header_val = f"{hashlib.md5(new_key.encode()).hexdigest()}|{ctime}"
    url = f'http://npa-test.jd.com{apiurl}'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {
        'auth-api': api_header_val,
        'auth-user': user,
        'Content-Type': "application/json",
        'User-Agent': user_agent
    }
    try:
        if method == "POST":
            response = requests.post(url, json=postdata, headers=headers)
        elif method == "GET": # 修正：使用 elif 避免逻辑漏洞
            response = requests.get(url, params=postdata, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status() # 检查 HTTP 状态码 (4xx, 5xx 会抛异常)
        
        logging.info(f"code:{response.status_code}, response:{response.text}")
        return response.json()
    except requests.RequestException as e:
        logging.error(f"API request error: {e}")
        return None # 发生网络或HTTP错误时返回 None，便于上层判断


# 获取CPU数据,需要参数，起止时间、集群名称
def get_cluster_cpu_api(groupname,begin_time,end_time):
    postdata = {
        "groupname": groupname,
        "begin_time": begin_time,
        "end_time": end_time
    }
    apiurl = "/prod-api/api/v2/analysis/prometheus/core?format=json"
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
    if "data" not in result or not result["data"]:
        logging.warning("API response successful but no data found.")
        return {"status": "empty", "message": "No data available", "code": 0}
 
    # 全部检查通过，返回完整结果
    return result


def analyze_data(A, B, C, D,x):
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
    
    # 判断日环比是否 > 30%
    if day_ratio_val * 100 > 30:
        alert_messages.append(f"日环比>30%")
        
    # 判断短期环比是否 > 30%
    if short_ratio_val * 100 > 30:
        alert_messages.append(f"短期环比>30%")
    
    # 判断最大值是否超过固定阈值
    max_D = max(D) if D else 0
    if max_D >= x:
        alert_messages.append(f"Max = {max_D} >{x} (阈值)")
        print(max_D)
    
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

def extract_cpu_max(data):
    """
    从接口返回的数据中提取CPU平均值列表
    
    参数:
        data: 接口返回的完整数据字典
    
    返回:
        list: CPU平均值列表，如果找不到则返回空列表
    """
    if not isinstance(data, dict):
        return []
    
    # 检查响应码
    if data.get('code') != 200:
        print(f"错误响应码: {data.get('code')}")
        return []
    
    # 获取data字段
    data_list = data.get('data', [])
    
    # 查找CPU指标
    for item in data_list:
        if isinstance(item, dict) and item.get('title') == 'CPU指标':
            # 找到series_data
            series_data = item.get('series_data', [])
            
            # 查找cluster_cpu_avg数据
            for series in series_data:
                if series.get('name') == 'cluster_cpu_max':
                    return series.get('value', [])
    
    print("未找到CPU max 数据")
    return []
def extract_cpu_avg(data):
    """
    从接口返回的数据中提取CPU平均值列表
    
    参数:
        data: 接口返回的完整数据字典
    
    返回:
        list: CPU平均值列表，如果找不到则返回空列表
    """
    if not isinstance(data, dict):
        return []
    
    # 检查响应码
    if data.get('code') != 200:
        print(f"错误响应码: {data.get('code')}")
        return []
    
    # 获取data字段
    data_list = data.get('data', [])
    
    # 查找CPU指标
    for item in data_list:
        if isinstance(item, dict) and item.get('title') == 'CPU指标':
            # 找到series_data
            series_data = item.get('series_data', [])
            
            # 查找cluster_cpu_avg数据
            for series in series_data:
                if series.get('name') == 'cluster_cpu_avg':
                    return series.get('value', [])
    
    print("未找到CPU平均值数据")
    return []
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

def extract_cpu_timeSeriesData(api_response):
    """提取CPU指标数据并转换为指定格式"""
    if isinstance(api_response, str):
        data = json.loads(api_response)
    else:
        data = api_response
    
    # 获取CPU指标部分
    cpu_data = None
    for item in data.get("data", []):
        if item.get("title") == "CPU指标":
            cpu_data = item
            break
    
    if not cpu_data:
        return {}
    
    # 构建结果字典
    result = {
        "CPU使用率": {},
        "CPU最大值": {}
    }
    
    x_data = cpu_data.get("x_data", [])
    series = cpu_data.get("series_data", [])
    
    # 遍历每条数据系列
    for series_item in series:
        name = series_item.get("name")
        values = series_item.get("value", [])
        
        # 映射指标名称
        if name == "cluster_cpu_avg":
            key = "CPU使用率"

        elif name == "cluster_cpu_max":
            key = "CPU最大值"
        else:
            continue
        
        # 添加时间-值对
        for time, value in zip(x_data, values):
            result[key][time] = value
    
    return result


    
from app.tools.registry import tool
# 获取集群指定时间段的CPU分析结果
@tool(
    name="get_cluster_cpu_analysis",
    description="获取指定集群在时间范围内的CPU指标分析结果",
    args_schema={
        "type": "object",
        "properties": {
            "groupname": {"type": "string", "description": "集群名称(例如: lf-lan-ha1)"},
            "begin_time": {
                "type": "string",
                "description": "开始时间(要求格式 YYYY-MM-DD HH:MM:SS)",
            },
            "end_time": {
                "type": "string",
                "description": "结束时间(要求格式 YYYY-MM-DD HH:MM:SS)",
            },
        },
        "required": ["groupname", "begin_time", "end_time"],
    },
)
def get_cluster_cpu_analysis(groupname, begin_time, end_time):
    # 获取昨天时间的参数
    B_groupname, B_begin_time, B_end_time = get_yesterday_time(groupname, begin_time, end_time)
    # 获取前30分钟的参数
    C_groupname, C_begin_time, C_end_time = get_previous_30_minutes(groupname, begin_time, end_time)
    
    # 并行调用API函数
    tasks = [
        (get_cluster_cpu_api, groupname, begin_time, end_time),
        (get_cluster_cpu_api, B_groupname, B_begin_time, B_end_time),
        (get_cluster_cpu_api, C_groupname, C_begin_time, C_end_time)
    ]
    A_list, B_list, C_list = parallel_execute(tasks)
    
    A_ts = extract_cpu_timeSeriesData(A_list)
    B_ts = extract_cpu_timeSeriesData(B_list)
    if "CPU使用率" in A_ts:
        A_ts["📊 当前趋势 (平均值)"] = A_ts.pop("CPU使用率")
    if "CPU最大值" in A_ts:
        A_ts["📊 当前趋势 (峰值)"] = A_ts.pop("CPU最大值")
        
    if "CPU使用率" in B_ts:
        B_ts["📈 日环比 (平均值)"] = B_ts.pop("CPU使用率")
    if "CPU最大值" in B_ts:
        B_ts["📈 日环比 (峰值)"] = B_ts.pop("CPU最大值")

    C_ts = extract_cpu_timeSeriesData(C_list)
    if "CPU使用率" in C_ts:
        C_ts["📈 30分钟环比 (平均值)"] = C_ts.pop("CPU使用率")
    if "CPU最大值" in C_ts:
        C_ts["📈 30分钟环比 (峰值)"] = C_ts.pop("CPU最大值")
    
    
    merged_data = merge_dicts(A_ts, day_add_1(B_ts), day_add_30(C_ts))
    
    # print(merged_data)
    
    image_url = generate_timeseries_chart_url(merged_data,"svg","CPU指标",60)
    

    # 从API返回数据中提取CPU平均值列表
    tasks_extract = [
        (extract_cpu_avg,A_list),
        (extract_cpu_avg,B_list),
        (extract_cpu_avg,C_list)
    ]
    A_cpu_data, B_cpu_data, C_cpu_data = parallel_execute(tasks_extract)
    
    D_cpu_max_data = extract_cpu_max(A_list)
    
    obj = {
        "info":analyze_data(A_cpu_data, B_cpu_data, C_cpu_data,D_cpu_max_data, 60),
        "image_url": image_url,
        
    }
    
    # 使用提取的CPU数据进行分析
    return obj


# import time

# start = time.time()
# print(get_cluster_cpu_analysis("lf-lan-ha1", "2026-02-05 11:00:00", "2026-02-05 11:30:00"))
# print(f"耗时: {time.time()-start:.2f}s")