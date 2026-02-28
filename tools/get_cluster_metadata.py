import time
import requests
import logging
import hashlib
import json


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
        # logging.info(f"code:{response.status_code}, response:{response.text}")
        
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
#获取集群概览
def get_overview(groupname, begin_time, end_time):
    postdata = {"groupname":groupname,"begin_time":begin_time,"end_time":end_time}
    apiurl= "/prod-api/api/v2/analysis/prometheus/summary?format=json"
    result = npa_summary_data(postdata,apiurl)
    return result


def format_overview_data(data):
    """
    提取接口返回数据中的中文指标名称和对应值
    """
    if isinstance(data, str):
        data = json.loads(data)
    
    result = {}
    for item in data.get('data', []):
        cn_name = item.get('cn_name')
        value = item.get('value')
        if cn_name and value is not None:
            result[cn_name] = value
    
    return result
from app.tools.registry import tool 
@tool(
    name="get_cluster_metadata",
    description="获取指定集群指定时间段元数据",
    args_schema={
        "type": "object",
        "properties": {
            "groupname": {"type": "string", "description": "集群名称(例如: ga-lan-jdns1)"},
            "begin_time": {
                "type": "string",
                "description": "开始时间(例如: 2026-01-13 09:00:00),要求格式 YYYY-MM-DD HH:MM:SS ",
            },
            "end_time": {
                "type": "string",
                "description": "结束时间(例如: 2026-01-13 09:30:00)，要求格式 YYYY-MM-DD HH:MM:SS ",
            },
        },
        "required": ["groupname", "begin_time", "end_time"],
    },
)
def get_cluster_metadata(groupname, begin_time, end_time):
    """
    """
    raw_data = get_overview(groupname, begin_time, end_time)
    return format_overview_data(raw_data)

#-------------------------------------------调度建议
# if __name__ == '__main__':
#     r = get_cluster_overview_analysis("lf-lan-ha1","2026-01-14 14:37:15","2026-01-14 15:07:15")
#     print(r)
