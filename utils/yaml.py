import yaml
import os


class Yaml:
    """"
     读取YAML文件的工具类
    """
    def __init__(self, file_path: str):

        if not file_path.endswith(".yaml"):
            raise ValueError("文件路径必须以.yaml结尾")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件路径{file_path}不存在")
        
        self.file_path = file_path
        
    def read(self):
        """
        读取YAML文件的内容
        """
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            print(f"文件{self.file_path}内容为空")
            return {}
        
        return data
    