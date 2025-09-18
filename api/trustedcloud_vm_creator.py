import requests
import base64
import time

class TrustedCloudVMBuilder:
    # def __init__(self, token, project_id):
    def __init__(self, token):
        """
        初始化 TrustedCloudVMBuilder 實例。
        :param token: 用於 API 認證的 Bearer Token
        :param project_id: 所屬專案的 ID
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        # ip 變更改這就好
        self.url = 'http://kong.140-110-139-103.nip.io/'
        
        # self.project_id = project_id
        self.project_id = self.list_projects()[0]

        '''
        self.aps_api_url = f"https://api.trusted-cloud.nchc.org.tw/aps/api/v1/project/{self.project_id}/"
        self.vps_api_url = f"https://api.trusted-cloud.nchc.org.tw/vps/api/v1/project/{self.project_id}/"
        self.vrm_api_url = f"https://api.trusted-cloud.nchc.org.tw/vrm/api/v1/project/{self.project_id}/"
        '''
        self.aps_api_url = self.url + f"aps/api/v1/project/{self.project_id}/"
        self.vps_api_url = self.url + f"vps/api/v1/project/{self.project_id}/"
        self.vrm_api_url = self.url + f"vrm/api/v1/project/{self.project_id}/"


    def _generate_vm_name(self):
        """
        依據當前時間戳產生唯一 VM 名稱。
        :return: 產生的 VM 名稱字串
        """
        return f"vm{int(time.time())}"

    def _encode_password(self, plain_password):
        """
        將純文字密碼以 Base64 編碼。
        :param plain_password: 純文字密碼
        :return: Base64 編碼後的密碼字串
        """
        return base64.b64encode(plain_password.encode()).decode()

    def list_projects(self):
        """
        取得所有可用的專案清單並回傳。
        :return: 專案名稱與 ID 的 dict，例如 {'NCHC-可信賴雲平台內部維護管理': '2aee06c5-981b-4566-8633-4da1a08217f7'}
        """
        # url = "https://api.trusted-cloud.nchc.org.tw/iam/api/v1/projects"
        url = "http://kong.140-110-139-103.nip.io/iam/api/v1/projects"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 取得專案列表失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return

        data = response.json()

        # 正確抓取專案的 displayName 與 projectId
        project_ids = [
            item["project"]["projectId"]
            for item in data.get("projects", [])
            if "project" in item and item["project"].get("projectId")
        ]

        return project_ids

################################################################################################################
#       處理基本 ID
################################################################################################################

    def list_image(self):
        """
        取得所有可用的 image 清單並列印。
        :return: 無直接回傳值，會印出每個 image 的詳細資訊
        """
        url = self.vrm_api_url + "tags?creator=false&projectLimit=false&projectPublic=false&adminRole=false"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 取得規格列表失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return

        data = response.json()
        # 處理不必要資訊, 只留 name 和 id
        img_dict = {
            d["repository"].get("name") + "_" + d.get("name"): d.get("id")
            for d in data["tags"]
        }
        return img_dict

    def list_flavors(self):
        """
        取得所有可用的 VM 規格（flavors）清單並列印。
        :return: 無直接回傳值，會印出每個 flavor 的詳細資訊
        """
        url = self.vps_api_url + "flavors"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 取得規格列表失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return

        data = response.json()
        flavors = data.get("flavors", [])

        flavor_list = []
        '''
        print("所有 VM 規格及其 ID：")
        for flavor in flavors:
            flavor_id = flavor.get("id", "N/A")
            flavor_name = flavor.get("name", "N/A")
            flavor_vcpu = flavor.get("vcpu", "N/A")
            flavor_memory = flavor.get("memory", "N/A")
            flavor_disk = flavor.get("disk", "N/A")
            flavor_gpu = flavor.get("gpu", "N/A")
            print(f"- 名稱: {flavor_name}，ID: {flavor_id}, vcpu: {flavor_vcpu}, memory: {flavor_memory}, disk: {flavor_disk}, gpu: {flavor_gpu}")

            flavor_info = {
                "id": flavor.get("id", "N/A"),
                "name": flavor.get("name", "N/A"),
                "vcpu": flavor.get("vcpu", 0),
                "memory": flavor.get("memory", 0),
                "disk": flavor.get("disk", 0),
                "gpu": flavor.get("gpu", 0)
            }
            flavor_list.append(flavor_info)
        '''    
        data = response.json()
        # 處理不必要資訊，只留下 name 和 id
        flavor_dict = {
            flavor.get("name"): flavor.get("id")
            for flavor in data.get("flavors", [])
        }
        return flavor_dict

    def list_network(self):
        """
        取得所有可用的 network 清單並列印。
        :return: 無直接回傳值，會印出每個 network 的詳細資訊
        """
        url = self.vps_api_url + "networks"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 取得規格列表失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return

        data = response.json()
        # 處理不必要資訊, 只留 name 和 id
        net_dict = {
            d.get("name"): d.get("id")
            for d in data["networks"]
        }
        return net_dict

    def list_security_groups(self):
        """
        取得所有可用的 image 清單並列印。
        :return: 無直接回傳值，會印出每個 image 的詳細資訊
        """
        url = self.vps_api_url + "security_groups"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 取得規格列表失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return

        data = response.json()
        # 處理不必要資訊, 只留 name 和 id
        sec_dict = {
            d.get("name"): d.get("id")
            for d in data["security_groups"]
        }
        return sec_dict

    def get_core_gpu_ram_quota(api_token: str):
        """
        查詢並回傳 GPU 張數、vCPU 核心數、記憶體的剩餘可用量。
        
        :param api_token: Bearer Token
        :return: Tuple -> (gpu_remaining, vcpu_remaining, ram_remaining)
        """
        url = self.vps_api_url + 'quotas'
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ API 請求失敗，狀態碼：{response.status_code}")
            print("回應內容：", response.text)
            return None, None, None

        data = response.json()

        def calc_remaining(resource):
            limit = resource.get("limit")
            usage = resource.get("usage")
            if limit == -1:
                return float("inf")
            return limit - usage

        gpu = data.get("gpu", {})
        vcpu = data.get("vcpu", {})
        ram = data.get("ram", {})

        gpu_remaining = calc_remaining(gpu)
        vcpu_remaining = calc_remaining(vcpu)
        ram_remaining = calc_remaining(ram)

        print("🔍 資源剩餘情況：")
        print(f"🟢 GPU：{gpu_remaining} 張（已使用 {gpu.get('usage', '?')} / 限額 {gpu.get('limit', '?')}）")
        print(f"🟢 vCPU：{vcpu_remaining} 核心（已使用 {vcpu.get('usage', '?')} / 限額 {vcpu.get('limit', '?')}）")
        print(f"🟢 RAM：{ram_remaining} MB（已使用 {ram.get('usage', '?')} / 限額 {ram.get('limit', '?')}）")

        return gpu_remaining, vcpu_remaining, ram_remaining

    def list_applications_projects(self) -> dict:
        """
        取得所有可用的應用模組分類（module categories）清單並回傳。

        :return: 模組分類名稱與 ID 的 dict，例如 {'Jupyter Notebook (CPU/Container)': 'afd5ae1a-98db-4e14-9cf1-1786176c983f'}
        """
        url = self.aps_api_url + 'module-categories?limit=-1'
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 取得專案列表失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return {}

        data = response.json()

        # 正確抓取 displayName 與 projectId
        app_dict = {
            f"{item['name']}-{item['description']}": item["id"]
            for item in data.get("moduleCategories", [])
            if item.get("name") and item.get("id") and item.get("description")
        }
        return app_dict

    def list_module(self, module_name, module_category_id) -> dict:
        """
        根據指定的模組名稱與資料，回傳模組名稱與對應 ID 的字典。
        :param data: 從 API 回傳的資料（包含 modules list）
        :param module_name: 你想要當作 key 的名稱
        :return: 以 module_name 為 key 的 dict，例如 {'Jupyter': 'module-id'}
        """
        url = self.aps_api_url + 'module-category/' + module_category_id + '/modules?limit=-1'
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 取得 keypair 清單失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return {}

        data = response.json()

        module_dict = {
            module_name: item["id"]
            for item in data.get("modules", [])
            if item.get("name") and item.get("id")
        }
        print('module_dict')
        print(module_dict)
        
        return module_dict

    def list_keypairs(self) -> dict:
        """
        取得目前專案下的 SSH 金鑰對清單。
        :return: dict，例如 {"my key name": "keypair-uuid"}
        """
        url = self.vps_api_url + "keypairs"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            print(f"❌ 取得 keypair 清單失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return {}

        data = response.json()

        key_dict = {
            item["name"]: item["id"]
            for item in data.get("keypairs", [])
            if item.get("name") and item.get("id")
        }
        print('key_dict')
        print(key_dict)
        
        return key_dict

################################################################################################################
#       建立服務
################################################################################################################

    def create_vm(self, image_id: str, flavor_id: str, network_id: str, 
                    security_group_id: str, password_plain: str="JupyterTest123!"):
        """
        建立一台新的虛擬機器（VM）。
        :param image_id: 映像檔 ID（作業系統）
        :param flavor_id: 規格 ID（CPU、RAM 等）
        :param network_id: 網路 ID（NCHC 給的）
        :param security_group_id: 安全群組 ID
        :param password_plain: VM 登入密碼（預設為 JupyterTest123!）
        :return: 建立成功回傳 VM 資訊 JSON，失敗則回傳 None
        """
        vm_name = self._generate_vm_name()
        password_encoded = self._encode_password(password_plain)

        payload = {
            "name": vm_name,
            "description": "測試 chat 自動建立用 VM",
            "image_id": image_id,
            "flavor_id": flavor_id,
            "password": password_encoded,
            "nics": [
                {
                    "network_id": network_id,
                    "sg_ids": [security_group_id]
                }
            ],
            "volumes": []
        }

        response = requests.post(self.vps_api_url + 'servers', json=payload, headers=self.headers)

        if response.status_code == 201:
            print("✅ VM 建立成功")
            return response.json()
        else:
            print(f"❌ VM 建立失敗，HTTP {response.status_code}")
            print(response.text)
            return response

    def create_application(self,
        name: str,
        module_id: str,     # list_applications_projects
        flavor_id: str, 
        network_id: str,
        password: str,      # 讓 llm 收集
        security_group_ids: list,
        service_port: str,  # 讓 llm 收集
        ssh_key_pair: str, 
        ssh_port: str = "22",
        namespace: str = "public",
        description: str = ""
    ) -> dict:
        """
        建立新的 Application (例如 Jupyter Notebook)

        :param project_id: 專案 ID
        :param token: Bearer Token
        
        :param name: 應用程式名稱，可自己取
        :param module_id: 模組 ID
        :param flavor_id: flavor ID
        :param network_id: network ID
        :param password: 密碼
        :param security_group_ids: 安全組列表
        :param service_port: 服務埠號
        :param ssh_key_pair: SSH 金鑰 ID
        :param ssh_port: SSH 埠號 (預設 22)
        :param namespace: 命名空間 (預設 "public")
        :param description: 應用描述
        :return: API 回傳 JSON dict
        """

        url = self.aps_api_url + 'application'
        
        answers = {
            "flavor_id": flavor_id,
            "network_id": network_id,
            "password": password,
            "security_group_ids": security_group_ids,
            "service_port": service_port,
            "ssh_key_pair": ssh_key_pair,
            "ssh_port": ssh_port
        }

        payload = {
            "name": name,
            "description": description,
            "moduleId": module_id,
            "projectId": self.project_id,
            "namespace": namespace,
            "answers": answers
        }

        response = requests.post(url, json=payload, headers=self.headers)

        if response.status_code not in (200, 201):
            print(f"❌ 建立 Application 失敗，HTTP {response.status_code}")
            print("錯誤訊息：", response.text)
            return {}

        return response.json()
        
if __name__ == "__main__":

    # === 設定參數 ===
    token = "YOUR_TOKEN"
    project_id = "2aee06c5-981b-4566-8633-4da1a08217f7"
    image_id = "f02b6f78-0bc3-4cb3-84af-0644315db953"
    flavor_id = "0a0f4753-6bd2-4cc4-9dc7-fc80f8e85344"
    network_id = "2d39d8cc-7f97-4328-9115-b60836cf3f38"
    security_group_id = "d98bfd83-9a88-44ce-9690-544608a6775e"

    # === 建立 VM ===
    builder = TrustedCloudVMBuilder(token, project_id)

    # ✅ 取得所有可用的規格
    builder.list_flavors()
    
    # ✅ 建立 VM
    result = builder.create_vm(
        image_id=image_id,
        flavor_id=flavor_id,
        network_id=network_id,
        security_group_id=security_group_id,
        password_plain="JupyterTest123!"
    )
    
    # ✅ 建立 Jupyter
    result = builder.create_application( 
        name="app1752557543954",
        module_id="bc57d5fd-cc2e-4676-9e8f-3efca021cc20",
        flavor_id="20896844-f816-472f-b271-d2cbe3e540e8",
        network_id="2d39d8cc-7f97-4328-9115-b60836cf3f38",
        password="8Jk3Lm9Pq@",
        security_group_ids=["d98bfd83-9a88-44ce-9690-544608a6775e"],
        service_port="8888",
        ssh_key_pair="adc13d2a-08dc-4c14-bdf3-a091e96c876b",
        ssh_port="22",
        description="我的 Jupyter Notebook"
    )
