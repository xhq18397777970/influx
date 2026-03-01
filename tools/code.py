import time
import requests
import logging
import hashlib
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime
from datetime import datetime, timedelta
import time 
import uuid

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


# 获取http_code数据,需要参数，起止时间、集群名称
def get_cluster_status_code_api(groupname,begin_time,end_time):
    postdata = {
        "groupname": groupname,
        "begin_time": begin_time,
        "end_time": end_time
    }
    apiurl = "/prod-api/api/v2/analysis/deeplog/querycode?format=json"
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

def extract_code_data(data):
    code_200_list = []
    code_503_list = []
    code_504_list = []
    
    for chart in data['data']:
        if '2xx' in chart['title']:
            for series in chart['series_data']:
                if series['name'] == '200':
                    code_200_list= series["value"]
    for chart in data['data']:
        if '5xx' in chart['title']:
            for series in chart['series_data']:
                if series['name'] == '503':
                    code_503_list = series["value"]
    for chart in data['data']:
        if '5xx' in chart['title']:
            for series in chart['series_data']:
                if series['name'] == '504':
                    code_504_list = series["value"]
    return code_200_list,code_503_list,code_504_list


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
def extract_status_code_percentages(data):
    """
    计算每个时间点的2xx、4xx、5xx状态码占比
    
    参数:
    data: API返回的原始数据
    
    返回:
    包含2xx、4xx、5xx百分比的时间序列字典
    """
    # 初始化结果字典
    result = {
        '2xx_percentages': {},
        '4xx_percentages': {},
        '5xx_percentages': {}
    }
    
    # 从原始数据中提取图表数据
    charts = data['data']
    
    # 找到2xx、3xx、4xx、5xx、other对应的数据
    chart_map = {}
    for chart in charts:
        title = chart['title']
        if '2xx' in title:
            chart_map['2xx'] = chart
        elif '3xx' in title:
            chart_map['3xx'] = chart
        elif '4xx' in title:
            chart_map['4xx'] = chart
        elif '5xx' in title:
            chart_map['5xx'] = chart
        elif 'other' in title.lower():
            chart_map['other'] = chart
    
    # 获取时间点列表（所有图表应该有相同的时间点）
    time_points = chart_map['2xx']['x_data']
    
    # 为每个时间点计算百分比
    for i, time_point in enumerate(time_points):
        total_2xx = 0
        total_3xx = 0
        total_4xx = 0
        total_5xx = 0
        total_other = 0
        
        # 计算2xx的总数
        if '2xx' in chart_map:
            for series in chart_map['2xx']['series_data']:
                total_2xx += series['value'][i]
        
        # 计算3xx的总数
        if '3xx' in chart_map:
            for series in chart_map['3xx']['series_data']:
                total_3xx += series['value'][i]
        
        # 计算4xx的总数
        if '4xx' in chart_map:
            for series in chart_map['4xx']['series_data']:
                total_4xx += series['value'][i]
        
        # 计算5xx的总数
        if '5xx' in chart_map:
            for series in chart_map['5xx']['series_data']:
                total_5xx += series['value'][i]
        
        # 计算other的总数
        if 'other' in chart_map:
            for series in chart_map['other']['series_data']:
                total_other += series['value'][i]
        
        # 计算总请求数
        total_requests = total_2xx + total_3xx + total_4xx + total_5xx + total_other
        
        # 计算百分比（保留两位小数）
        if total_requests > 0:
            result['2xx_percentages'][time_point] = round((total_2xx / total_requests) * 100, 2)
            result['4xx_percentages'][time_point] = round((total_4xx / total_requests) * 100, 2)
            result['5xx_percentages'][time_point] = round((total_5xx / total_requests) * 100, 2)
        else:
            result['2xx_percentages'][time_point] = 0.00
            result['4xx_percentages'][time_point] = 0.00
            result['5xx_percentages'][time_point] = 0.00
    
    return result

    # description="获取指定集群在时间范围内的状态码分析结果",
    # args_schema={
    #     "type": "object",
    #     "properties": {
    #         "groupname": {"type": "string", "description": "集群名称(例如: lf-lan-ha1)"},
    #         "begin_time": {
    #             "type": "string",
    #             "description": "开始时间(例如: 2025-01-07 00:00:00)",
    #         },
    #         "end_time": {
    #             "type": "string",
    #             "description": "结束时间(例如: 2025-01-08 17:00:00)",
    #         },
    #     },
    #     "required": ["groupname", "begin_time", "end_time"],
    # }

def get_cluster_status_code_analysis(groupname,begin_time,end_time):
    """
    获取集群状态码分析数据
    """
    # 获取昨天时间的参数
    B_groupname, B_begin_time, B_end_time = get_yesterday_time(groupname, begin_time, end_time)
    # 获取前30分钟的参数
    C_groupname, C_begin_time, C_end_time = get_previous_30_minutes(groupname, begin_time, end_time)
    
        # 并行调用API函数
    tasks = [
        (get_cluster_status_code_api, groupname, begin_time, end_time),
        (get_cluster_status_code_api, B_groupname, B_begin_time, B_end_time),
        (get_cluster_status_code_api, C_groupname, C_begin_time, C_end_time)
    ]
    A_raw, B_raw, C_raw = parallel_execute(tasks)
    
    # print(A_raw,B_raw,C_raw)
    
    A_200, A_503, A_504 = extract_code_data(A_raw)
    B_200, B_503, B_504 = extract_code_data(B_raw)
    C_200, C_503, C_504 = extract_code_data(C_raw)
    

    # 修改 tasks_analyze 的定义，将 analyze_data 函数及其参数分开
    tasks_analyze = [
        (analyze_data, A_200, B_200, C_200, 1155214),
        (analyze_data, A_503, B_503, C_503, 18000),
        (analyze_data, A_504, B_504, C_504, 10)
    ]
    code_200_result, code_503_result, code_504_result = parallel_execute(tasks_analyze)
    
    # print(code_200_result, code_503_result, code_504_result)
    time_serie_data = extract_status_code_percentages(A_raw)
    
    def separate_data(data):
        """将原始数据分离为2xx成功率和4xx/5xx错误率两个对象"""
        data_2xx = {'2xx_percentages': data['2xx_percentages']}
        data_4xx_5xx = {
            '4xx_percentages': data['4xx_percentages'],
            '5xx_percentages': data['5xx_percentages']
        }
        return data_2xx, data_4xx_5xx


    #2xx、4xx、5xx占比时序图(2xx单独放在一张图中，4xx、5xx放一块，观测更加直观)
    code_2xx ,code_4xx_5xx =separate_data(time_serie_data)

    code_2xx_image = generate_timeseries_chart_url(code_2xx,"svg","2xx占比",0)
    code_4xx_5xx_image = generate_timeseries_chart_url(code_4xx_5xx,"svg","4xx_5xx占比",0)
    
    obj = {
        "info":{
            "code_200":code_200_result,
            "code_503":code_503_result,
            "code_504":code_504_result
        },
        "image_url" :{
            "2xx": code_2xx_image,
            "4xx_5xx": code_4xx_5xx_image
        }

    }
    return obj


# r = get_cluster_status_code_analysis("lf-lan-ha1","2026-02-10 15:30:00","2026-02-10 16:00:00")
# print(r)
#