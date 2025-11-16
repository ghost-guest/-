from .utils import Api



class XyssDeal:
    """
    处理小云搜索返回的结果
    """
    def __init__(self):
        self.api = Api()
    
    # 批量调用小云搜索的接口，直至返回的数据全部拿到
    async def deal_result(self, result):
        """
        处理小云搜索返回的结果
        """
        