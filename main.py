from fastapi import FastAPI, Request
import uvicorn
from utils import Api
import json
import os
import sys


dir_path = os.path.dirname(os.path.abspath(__file__))
quark_save_path = os.path.join(dir_path, "quark_auto_save")
sys.path.append(quark_save_path)
# 导入夸克自动保存模块
import quark_auto_save
from quark_auto_save import Config, Quark, MagicRename,QuarkOperator

app = FastAPI()


@app.post("/")
async def read_root(request: Request):
    # 获取整个请求
    request_dict = await request.body()
    print(f"request_dict: {request_dict}")
    # 解析json
    query_dict = json.loads(request_dict.decode("utf-8"))
    print(f"query_dict: {query_dict}")
    search_api = Api()
    q_dict = {}
    q_dict["wd"] = query_dict.get("wd")
    q_dict["page"] = query_dict.get("page", 1)
    result = await search_api.xyss_deal_result(q_dict)
    print(f"result: {result}")
    # 从result中获取第一个对象
    if result["status"] == 200:
        orgion_obj = result["qk_data"]["Data"][0]
        target_path = "/夸克分享资源/" + orgion_obj["ScrName"]
        await quark_save(orgion_obj, target_path)
    return result


async def quark_save(orgion_obj, target_path):
    # 获取quark的请求，然后保存到自己的网盘中，然后分享链接
    # 保存当前工作目录
    current_dir = os.getcwd()
    try:
        # 切换到quark_auto_save目录
        os.chdir(quark_save_path)
        # 提供正确的配置文件路径
        config_path = os.path.join(quark_save_path, "quark_config.json")
        q = QuarkOperator(config_path)
        tasklist = []
        t_dict = {}
        t_dict["taskname"] = orgion_obj["ScrName"]
        t_dict["shareurl"] = orgion_obj["Scrurl"]
        t_dict["savepath"] = target_path
        tasklist.append(t_dict)
        res = q.do_save(q.accounts[0], tasklist)
        print(f"res is {res}")
    finally:
        # 无论如何都要切换回原来的工作目录
        os.chdir(current_dir)


@app.post("/delete_time_file")
async def delete_time_file(request: Request):
    # 获取整个请求
    request_dict = await request.body()
    print(f"request_dict: {request_dict}")
    # 解析json
    query_dict = json.loads(request_dict.decode("utf-8"))
    print(f"query_dict: {query_dict}")
    filepath = query_dict.get("filepath")
    # 删除到达时间的文件
    q = QuarkOperator(os.path.join(quark_save_path, "quark_config.json"))
    q.delete_time_file(filepath)
    return {"msg": "删除成功"}


@app.post("/share_file")
async def share_file(request: Request):
    # 获取整个请求
    request_dict = await request.body()
    print(f"request_dict: {request_dict}")
    # 解析json
    query_dict = json.loads(request_dict.decode("utf-8"))
    print(f"query_dict: {query_dict}")
    sharefilelist = query_dict.get("sharefilelist")
    title = query_dict.get("title")
    # 删除到达时间的文件
    q = QuarkOperator(os.path.join(quark_save_path, "quark_config.json"))
    res = q.share_file(sharefilelist, title)
    return {"result": res}



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
