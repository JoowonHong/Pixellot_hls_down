
import requests
import pandas as pd
import json
import datetime
import pytz
import ffmpeg

class PixellotAPI():

    def __init__(self,isReal):
        
        if isReal ==False:
            BASE_URL = "https://api.stage.pixellot.tv/v1"  # stage API 기본 URL
            USERNAME = "yst_stage_api"
            PASSWORD = "yst4DByLQZELW7j7OWV0Mk79BIOVBs"
        elif isReal == True:
            BASE_URL = "https://api.pixellot.tv/v1" # 상용 API
            USERNAME = "yst_api"
            PASSWORD = "yst7tRTe7q7R3qFTfGvUg8TRayUuR9e"
        
        self.base_url = BASE_URL
        self.username = USERNAME
        self.password = PASSWORD
        self.token = self.get_api_token()
        self.request_body = None  

    def seoul_to_utc_iso(seoul_time_str):
        """
        서울 시간(YYYY-MM-DD HH:MM:SS) 문자열을 UTC ISO 포맷(YYYY-MM-DDTHH:MM:SS.000Z)으로 변환
        """
        seoul = pytz.timezone('Asia/Seoul')
        dt_seoul = seoul.localize(datetime.datetime.strptime(seoul_time_str, "%Y-%m-%d %H:%M:%S"))
        dt_utc = dt_seoul.astimezone(pytz.utc)
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def get_api_token(self):
        """
        API에 로그인하여 토큰을 받아오는 함수.

        Args:
            base_url (str): API의 기본 URL (로그인 엔드포인트 포함).
            username (str): 로그인에 사용할 사용자 이름.
            password (str): 로그인에 사용할 비밀번호.

        Returns:
            str: 반환된 토큰 값 (성공 시).
        """
        # 로그인 엔드포인트 URL
        login_url = f"{self.base_url}/login"  # 엔드포인트 URL 수정 필요

        # 요청에 필요한 데이터
        payload = {
            "username": self.username,
            "password": self.password
        }

        try:
            # POST 요청 보내기
            response = requests.post(login_url, json=payload)

            # HTTP 응답 상태 확인
            response.raise_for_status()

            # JSON 응답에서 토큰 추출
            token = response.json().get("token")  # 'token' 키는 API 문서에 따라 수정 필요

            if not token:
                raise ValueError("토큰이 응답에 포함되지 않았습니다.")

            print("토큰을 성공적으로 받아왔습니다.")
            return token

        except requests.exceptions.RequestException as e:
            print(f"요청 중 오류 발생: {e}")
        except ValueError as e:
            print(f"응답 처리 중 오류 발생: {e}")

        return None


    def get_api_data(self,endpoint):
        """
        API에서 데이터를 가져오는 함수.

        Returns:
            dict: API 응답 데이터 (성공 시).
        """
        if not self.token:
            print("토큰이 없습니다. 먼저 로그인하세요.")
            return None

        # 요청 URL 생성
        url = f"{self.base_url}/{endpoint}"

        # 인증 헤더 설정
        headers = {
            "Authorization": self.token  # 'Bearer'는 API 문서에 따라 수정 필요
        }   
        try:
            # GET 요청 보내기
            response = requests.get(url, headers=headers)

            # HTTP 응답 상태 확인
            response.raise_for_status()

            # JSON 응답 반환
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"요청 중 오류 발생: {e}")

        return None

    
    def post_api_data(self, endpoint, body=None):
        """
        API에 데이터를 POST 요청으로 보내는 함수.

        Args:
            endpoint (str): 요청하려는 API 엔드포인트.
            body (dict, optional): POST 요청에 포함할 데이터.

        Returns:
            dict: API 응답 데이터 (성공 시).
        """
        if not self.token:
            print("토큰이 없습니다. 먼저 로그인하세요.")
            return None

        # 요청 URL 생성
        url = f"{self.base_url}/{endpoint}"

        # 인증 헤더 설정
        headers = {
            "Authorization": self.token,  # 'Bearer'는 API 문서에 따라 수정 필요
            "Content-Type": "application/json"
        }

        try:
            # POST 요청 보내기
            response = requests.post(url, headers=headers, json=body)

            # HTTP 응답 상태 확인
            response.raise_for_status()

            # JSON 응답 반환
            return response.json()

        except requests.exceptions.RequestException as e:
            print (response.text)
            print(f"요청 중 오류 발생: {e}")

        return None

    def get_Club_ID(self, endpoint):
        """
        클럽 ID를 가져오는 함수.

        Args:
            endpoint (str): 요청하려는 API 엔드포인트.

        Returns:
            str: 클럽 ID (성공 시).
        """
        data = self.get_data(endpoint)
        if data and isinstance(data, list) and len(data) > 0:
            return data[0].get("_id")




    def create_event_body(self,strName, strStart, strEnd, strVenueID, strNumber):

        requestBody = {
        "eventName": strName,
        "start$date": strStart,
        "end$date": strEnd,
        "venue": {
            "_id": strVenueID
        },
        # "status": "archived",  # 필요시 주석 해제
        "scoreboardData": {
            "homeTeam": "Home",
            "awayTeam": "Guest",
            "enable": True
        },
        "productionType": "soccer",
        "numberOfPlayers": strNumber,
        "permission": "club",
        "gameType": "game",
        "commerceType": "members",
        "isTest": False
        }   
        


        requestBody2 ={
          "clubId": "617bca1b2cb00e8982a58201",
          "system": {
            "id": "633e7797e8a6956fe4376c2b"
          },
          "gameInfo": {
            "cameraAutoProduction": "auto-camera",
            "type": "game",
            "team1Players": [],
            "team2Players": [],
            "team1Id": "68746e0b57401a85bb66f26b",
            "team2Id": "68746dfe2103b81d645fa24e",
            "name": "basketball",
            "autoProduction": True
          },
          "streamConfig": {
            "hd": {
              "target": "app"
            },
            "pano": {
              "target": "app"
            }
          },
          "streamType": "zixi",
          "media": {
            "preRolls": {
              "live": {},
              "vod": {},
              "cutClip": {},
              "download": {}
            },
            "logos": {
              "live": None,
              "vod": None
            }
          },
          "location": {
            "name": ""
          },
          "permission": "club",
          "graphics": {
            "automaticGraphicsProduction": True
          },
          "sponsorsBanners": [],
          "allowBettingMode": False,
          "streamTargets": [],
          "startDateTime": "2025-07-14T08:00:00.000Z",
          "endDateTime": "2025-07-14T09:00:00.000Z",
          "geoBlocking": {
            "enabled": False,
            "source": "tenant"
          },
          "thumbnails": {
            "hd": ""
          },
          "commerceType": "members",
          "vodCommerceType": "members",
          "logo": "https://d36t7dxy4sauub.cloudfront.net/clubs/617bca1b2cb00e8982a58201/logo-original.c3647451040f3db290707d0d66382bab214c10485431c4a0.png",
          "isTest": True,
          "useCDN": True,
          "name": "hogka_lab_test",
          "extensions": {
            "extensionsIdsToApply": []
          }
        }

        return requestBody2




# 사용 예시
if __name__ == "__main__":


    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    api = PixellotAPI(isReal=True)  # isReal=True로 변경하여 상용 API 사용 가능
    
    

    endpotint = "clubs/67d29a24fee11674832605ef"  # 클럽 엔드포인트
    # data = api.get_api_data(endpotint)

    # print("데이터:", data)

    ffmpeg.input("https://dnw98ykn7b9iq.cloudfront.net/yst/687f7eafa0ad62889309d76d/cloud_hls/0_hd_hls.m3u8").output("output.mp4").run()
