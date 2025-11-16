from utils.yaml import Yaml
import aiohttp
import asyncio
import json


class Api:
    """
    获取网络资源的接口工具，这里小云搜索为网盘搜索的资源接口，后续可以添加其他的网盘搜索
    接口文档地址： https://www.yunso.net/index/user/database.html
    """
    def __init__(self, config_file_path: str = None):
        self.config = config_file_path if config_file_path else "config.yaml"
        self.yaml = Yaml(self.config)
        self.config_data = self.yaml.read()

        self.xyss_api_Id  = self.config_data.get("xyss_api_id", "10602")
        self.xyss_api_Key = self.config_data.get("xyss_api_key", "4ac23e6eb211f452e045819c32c9f990bcec4230ef87e990989cbb330dbea8ec")
        self.xyss_api_Url = self.config_data.get("xyss_api_url", "https://www.yunso.net/api/opensearch.php")

    async def xyss_search(self, query: dict):
        """
        调用小云搜索接口，搜索指定的查询字符串, 该接口只会返回前100项目
        url?wd={word}&uk=&mode={mode}
        wd  白矮星	是	string  字符串	关键词。
        mode  模式	否	string  字符串	模式：`90001` 智能搜索（默认），`90002` 精准搜索。
        page  页	否	int  整数	页码。
        type  类型	否	string  字符串	用于返回的类型。留空则返回标准 JSON；如果 `type=text`，则返回 JSON，其中 `msg` 字段可直接回复用户。
        groupid  群组 ID	否	string  字符串	发送请求的群组 ID，例如来自私聊则为 `-1`。
        userid  用户 ID	否	string  字符串	发送请求的用户 ID。
        machineid	否	string  字符串	机器人 ID。
        appid	否	string  字符串	用于确认身份，请附带此参数以便账户限流等措施。例如：账户单日限制 1000 次。
        key  钥匙	否	string  字符串	确认身份，登录用户可以在授权API查询。
        original  源语言	否	int  整数	默认获取网盘原始链接。
        query {
            "wd": query.get("wd", ""),
            "mode": query.get("mode", "90002"),
            "page": query.get("page", 1),
        }
        return dict search results

        """
        params = {
            "wd": query.get("wd", ""),
            "mode": query.get("mode", "90002"),
            "page": query.get("page", 1)
        }
        params["appid"] = self.xyss_api_Id
        params["key"] = self.xyss_api_Key
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.xyss_api_Url, 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                    ssl=False,
                    ) as response:
                    if response.status == 200:
                        # print(f"请求成功，状态码：{response.status}")
                        # print(f"响应头：{response.headers}")
                        tt_content = await response.text()
                        print(f"响应内容：{tt_content}")
                        if "Warning" in tt_content or "Undefined" in tt_content:
                            print(f"请求失败，状态码：{response.status}")
                            return {"msg": "查询不到数据，可能资源已不存在","status":999,"data":[]}
                        
                        content_type = response.headers.get("Content-Type", "")
                        if "application/json" in content_type:
                            data = await response.json()
                            return {"msg":"success","status":200,"data":data, "total":len(data["Data"])}
                        else:
                            # text_content = await response.text()
                            data = json.loads(tt_content)
                            return {"msg":"success","status":200,"data":data, "total":len(data["Data"])}
                    else:
                        print(f"请求失败，状态码：{response.status}")
                        return None
        except aiohttp.ClientError as e:
            print(f"请求失败，错误信息：{e}")
            raise Exception(f"请求失败，错误信息：{e}")
        except asyncio.TimeoutError:
            print("请求超时")
            raise Exception("请求超时")
        except Exception as e:
            print(f"请求失败，错误信息：{e}")
            raise Exception(f"请求失败，错误信息：{e}")

    async def xyss_deal_result(self, query: dict):
        """
        处理搜索结果的并发查询接口
        
        流程：
        1. 先调用一次xyss_search获取初始结果
        2. 根据返回的Query_result_Total值判断是否需要并发查询更多结果
        3. 如果总数大于5，计算需要并发执行的次数并并发调用xyss_search
        4. 合并所有查询结果并返回
        
        Args:
            query: 搜索查询参数字典
                - wd: 搜索关键词
                - mode: 搜索模式
                - 其他参数同xyss_search
                
        Returns:
            dict: 包含所有合并结果的数据字典
        """
        # 第一步：获取初始结果
        first_result = await self.xyss_search(query)
        
        # 检查初始结果是否成功
        if not first_result or first_result.get('status') != 200:
            return first_result or {"msg": "全网没有查询到更多数据，请换一个重试", "status": 500, "data":[], "total":0}
        
        # 获取总结果数
        # 注意：这里根据API的实际返回结构来获取总数
        # 可能需要根据实际情况调整键名
        total_count = first_result.get('data', {}).get('Query_result_Total', 0)
        
        # 如果总数小于等于5，直接返回初始结果
        if total_count <= 5:
            return first_result
        
        # 计算需要并发执行的次数
        # 假设每次查询返回5条结果，总页数 = (总数 - 5) / 5
        # 向上取整确保获取所有结果
        import math
        page_count = math.ceil((total_count - 5) / 5)
        
        # 并发调用任务列表
        tasks = []
        
        # 创建并发任务，从第2页开始（第1页已获取）
        for page_num in range(2, page_count + 2):
            # 创建包含当前页码的查询参数
            page_query = query.copy()
            page_query['page'] = page_num
            # 添加到任务列表
            tasks.append(self.xyss_search(page_query))
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并所有成功的结果
        all_data = []
        
        # 添加第一页的结果
        if isinstance(first_result.get('data'), dict) and 'Data' in first_result['data']:
            all_data.extend(first_result['data']['Data'])
        
        # 处理后续页面的结果
        for result in results:
            # 检查结果是否成功
            if isinstance(result, dict) and result.get('status') == 200 and isinstance(result.get('data'), dict) and 'Data' in result['data']:
                all_data.extend(result['data']['Data'])
            elif isinstance(result, Exception):
                # 记录错误但不中断处理
                print(f"并发查询出错: {result}")
        
        # 返回合并后的结果
        # 分类 百度和夸克
        bd_data = []
        qk_data = []
        for item in all_data:
            if item.get("Scrurlname") == "百度":
                bd_data.append(item)
            elif item.get("Scrurlname") == "夸克":
                qk_data.append(item)
        
        return {
            "msg": "success",
            "status": 200,
            "data": {
                "Query_result_Total": total_count,
                "Data": all_data
            },
            "bd_data": {
                "Query_result_Total": len(bd_data),
                "Data": bd_data
            },
            "qk_data": {
                "Query_result_Total": len(qk_data),
                "Data": qk_data
            },
            "total": len(all_data),
            "concurrent_pages": page_count,
            "processed_count": len([r for r in results if isinstance(r, dict) and r.get('status') == 200])
        }