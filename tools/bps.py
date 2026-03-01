import time
import requests
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict
 
#net_bps_in 入口带宽（下载、数据进入设备）
#net_bps_out 出口带宽（上传、数据从设备出去）

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
#鉴权
def npa_summary_data(postdata, apiurl, method="POST"):
    user = "xiehanqi.jackson"
    ctime = str(int(time.time()))
    new_key = f"{user}|{ctime}"
    # 修正这里：使用 hashlib.md5() 来计算哈希值
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
            return {"error": "不支持的请求方法"}
            
        response.raise_for_status()
        result = response.json()
        logging.info(f"code:{response.status_code}, response:{response.text}")
        
        # 检查响应结果的三种情况
        if result.get('code') == 200:
            if result.get('data'):
                # 情况1: code=200且data数据存在不为空，成功直接返回接口数据
                return result
            else:
                # 情况3: code=200但data为空，返回接口数据，并新增属性message："接口数据为空"
                result['message'] = "入参数格式有误、或该时段接口返回数据为空"
                return result
        else:
            # 情况2: code!=200返回错误信息
            return {"error": f"API请求失败，code: {result.get('code')}, message: {result.get('message', '未知错误')}"}
            
    except requests.RequestException as e:
        logging.error(f"API request error: {e}")
        return {"error": f"API请求异常: {str(e)}"}
    except ValueError as e:
        logging.error(f"JSON解析错误: {e}")
        return {"error": "响应数据格式错误"}
 
#获取时间段，集群网络指标
def get_network_api(groupname, begin_time, end_time):
    postdata = {"groupname":groupname,"begin_time":begin_time,"end_time":end_time}
    apiurl = "/prod-api/api/v2/analysis/prometheus/core?format=json"
    result = npa_summary_data(postdata, apiurl)
    return result
 
def extract_network_data(data):
    """从原始数据中提取网络输入和输出数据列表
    """
    net_in_bps_max = []
    net_out_bps_max = []
    
    for item in data.get('data', []):
        if item.get('title') == '网络指标':
            for series in item.get('series_data', []):
                if series.get('name') == 'net_in_bps_max':
                    net_in_bps_max = series.get('value', [])
                elif series.get('name') == 'net_out_bps_max':
                    net_out_bps_max = series.get('value', [])
            break  # 找到网络指标数据后就停止遍历
    
    return net_in_bps_max, net_out_bps_max

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
def extract_bps_timeSeriesData(response_data):
    result = {}
    for chart in response_data.get('data', []):
        if chart.get('title') == '网络指标':
            for i, legend in enumerate(chart['legend_data']):
                if legend in ['net_in_bps_max', 'net_out_bps_max']:
                    result[legend] = dict(zip(
                        chart['x_data'], 
                        chart['series_data'][i]['value']
                    ))
    return result

#     name="get_cluster_network_analysis",
#     description="获取指定集群时间范围内的网络（出入口带宽）指标分析结果",
#     args_schema={
#         "type": "object",
#         "properties": {
#             "groupname": {"type": "string", "description": "集群名称(例如: ga-lan-jdns1)"},
#             "begin_time": {
#                 "type": "string",
#                 "description": "开始时间(例如: 2026-01-13 09:00:00),要求格式 YYYY-MM-DD HH:MM:SS ",
#             },
#             "end_time": {
#                 "type": "string",
#                 "description": "结束时间(例如: 2026-01-13 09:30:00)，要求格式 YYYY-MM-DD HH:MM:SS ",
#             },
#         },
#         "required": ["groupname", "begin_time", "end_time"],
#     }

def get_cluster_network_analysis(groupname, begin_time, end_time):
    """
    获取三个时间段的集群网络数据
    """
    # 获取昨天时间的参数
    B_groupname, B_begin_time, B_end_time = get_yesterday_time(groupname, begin_time, end_time)
    # 获取前30分钟的参数
    C_groupname, C_begin_time, C_end_time = get_previous_30_minutes(groupname, begin_time, end_time)
    
    # 调用API函数获取原始数据
    A_raw = get_network_api(groupname, begin_time, end_time)
    B_raw = get_network_api(B_groupname, B_begin_time, B_end_time)
    C_raw = get_network_api(C_groupname, C_begin_time, C_end_time)
    
    A_ts = extract_bps_timeSeriesData(A_raw)
    B_ts = extract_bps_timeSeriesData(B_raw)
    C_ts = extract_bps_timeSeriesData(C_raw)
    
    # print(A_ts)
    
    if "net_in_bps_max" in A_ts:
        A_ts["📊 当前趋势 (入口带宽)"] = A_ts.pop("net_in_bps_max")
    if "net_out_bps_max" in A_ts:
        A_ts["📊 当前趋势 (出口带宽)"] = A_ts.pop("net_out_bps_max")
        
    if "net_in_bps_max" in B_ts:
        B_ts["📈 日环比 (入口带宽)"] = B_ts.pop("net_in_bps_max")
    if "net_out_bps_max" in B_ts:
        B_ts["📈 日环比 (出口带宽)"] = B_ts.pop("net_out_bps_max")
        
    if "net_out_bps_max" in C_ts:
        C_ts["📈 30分钟环比 (出口带宽)"] = C_ts.pop("net_out_bps_max")
    if "net_in_bps_max" in C_ts:
        C_ts["📈 30分钟环比 (入口带宽)"] = C_ts.pop("net_in_bps_max")

        
    merge_data = merge_dicts(A_ts, day_add_1(B_ts), day_add_30(C_ts))
    
    image_url = generate_timeseries_chart_url(merge_data,"svg","网络指标",97960988447)

    
    # 从API返回数据中提取QPS值列表
    A_in_bps_max, A_out_bps_max = extract_network_data(A_raw)

    B_in_bps_max, B_out_bps_max = extract_network_data(B_raw)
    C_in_bps_max, C_out_bps_max = extract_network_data(C_raw)
    
    # 调用analyze_data函数进行分析
    in_bps_result = analyze_data(A_in_bps_max, B_in_bps_max, C_in_bps_max,97960988447)
    out_bps_result = analyze_data(A_out_bps_max, B_out_bps_max, C_out_bps_max,97960988447)

    
    obj = {
        "info":{
            "网络入口带宽":in_bps_result,
            "网络出口带宽":out_bps_result,
        },
        "image_url":image_url,  
    }
    return obj

# r = get_cluster_network_analysis("lf-lan-ha1", "2026-01-29 09:30:00", "2026-01-29 10:00:00")
# print(r)