import logging
import requests
import json
BASE_URL = "https://api.mingdao.com/v2"
APP_KEY = "db053d40289b363b"
SIGN = "N2FhMDljMGU3MWVhOGQ4NTU1MWYwNjY0Y2NhMzczZGQ2MzM0ODVjNGRjZWM0OTAzNTljOTAwMDI4OTFhNDIzZg=="

def send_post_request(api,params,appkey=APP_KEY,sign=SIGN):
    # 将传入的 JSON 字符串转化为字典对象
    params["appKey"] = appkey
    params["sign"] = sign
    logging.info(f"xxxxxxxxxxx result: {BASE_URL}{api}")
    
    # 设置请求头，指定内容类型为 JSON
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 发送 POST 请求
    response = requests.post(f"{BASE_URL}{api}", json=params, headers=headers)
    
    # 如果请求成功，则返回响应的 JSON 数据
    if response.status_code == 200:
        return response.json()
    else:
        # 如果请求失败，返回错误信息
        return {"error": f"Request failed with status code {response.status_code}"}
    
def filter(controlId,dataType,spliceType,filterType,value):
    return {
        "controlId": controlId,
        "dataType": dataType,
        "spliceType": spliceType,
        "filterType": filterType,
        "value": value
    }

def worksheetGetFilterRows(worksheetId,filters,pageIndex,pageSize,appkey=APP_KEY,sign=SIGN):
    api = "/open/worksheet/getFilterRows"
    params = {
        "worksheetId": worksheetId,
        "filters": filters,
        "pageIndex": pageIndex,
        "pageSize": pageSize,
        "listType": 1,
    }
    return send_post_request(api, params,appkey, sign)
