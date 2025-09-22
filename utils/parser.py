import re
import os
import yaml
import json
from typing import List


class ImageTagParser:
    def __init__(self, config_path="./config/settings.yaml"):
        """
        初始化，從 YAML 設定檔中載入圖片 base_url。
        :param config_path: 設定檔路徑
        """
        self.config = self.load_config(config_path)
        self.base_url = self.get_base_url_from_config()

    @staticmethod
    def load_config(path: str) -> dict:
        """
        載入 YAML 設定檔。
        :param path: 檔案路徑
        :return: 設定 dict
        """
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def get_base_url_from_config(self) -> str:
        """
        從 host_ip 和 port 組合 image_base_url。
        :return: 完整的 image_base_url 字串
        """
        host = self.config["server"]["host_ip"]
        port = self.config["server"]["port"]
        return f"http://{host}:{port}/images"

    def convert_image_tags(self, text: str) -> List[dict]:
        """
        將文字中格式為「（見圖:xxx）」的段落轉換為圖文交錯結構。
        :param text: 原始輸入文字
        :param config: 包含 image_base_url 的設定 dict
        :return: [{"type": "text", ...}, {"type": "image", ...}]
        """
        content = []
        pattern = re.compile(r"[（(]見圖[:：](.+?)[）)]")
        parts = pattern.split(text)

        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part.strip():
                    yield {"type": "text", "value": part.strip()}
                #    content.append({"type": "text", "value": part.strip()})
            else:
                # 如果路徑包含 ./trusted-cloud/image/ 就把它移除
                relative_path = part.strip().replace("./trusted-cloud/image/", "")
                path = self.base_url + "" + relative_path
                # 如果路徑包含 ./trusted-cloud/image/ 就把它移除
                #relative_path = relative_path.replace("./trusted-cloud/image/", "")
           #     content.append({
           #         "type": "image",
           #         "value": f"{self.base_url}/{relative_path}"
           #     })
                yield {"type": "image", "value": path}
   #     return content