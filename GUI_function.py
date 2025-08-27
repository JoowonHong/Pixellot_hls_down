import tkinter.ttk as ttk
from tkinter import * #__all__
import pandas as pd
import tkinter.messagebox as msgbox
from tkinter import filedialog,scrolledtext #sub module
import datetime
import pytz
import ffmpeg
import subprocess
import threading
import re
import unicodedata

import os
import sys
import time
from Pixellot_api import PixellotAPI


#기능 함수 구현

class Function:
    def create_event_url(self, event=None):
        """선택된 venue의 URL을 txt_dest_path에 표시"""
        self.txt_dest_path.delete(0, END)
        self.txt_dest_path.insert(0, self.reserve_api_url)
        print("촬영예약 URL:", self.reserve_api_url)
        selected = self.cmb_system.get()  # 선택된 venue
        # venue id만 추출
        if "(" in selected and ")" in selected:
            self.system_id = selected.split("(")[-1].replace(")", "")
        else:
            self.system_id = ""
        print("선택된 venue id:", self.system_id)
    def update_isReal(self, event=None):
        """운영 서버 사용 여부 토글"""
        self.isReal = not self.isReal
        print(f"isReal: {self.isReal}")
    def import_club_list(self):
        """클럽 리스트를 Pixellot API에서 불러와 콤보박스에 세팅"""
        self.api_test = PixellotAPI(self.isReal)
        self.club_data = self.api_test.get_api_data("clubs")
        club_options = [f"{club.get('name', '')} ({club.get('_id', '')})" for club in self.club_data]
        self.cmb_club['values'] = club_options

    # 생성자

    def __init__(self,listfile=None,txt_dest_path=None,cmb_club=None,cmb_system=None,cmb_line=None, batch_entry=None, treeview=None):
         # 현재 스크립트 파일의 디렉토리를 얻기
        self.current_directory = os.path.dirname(os.path.realpath(__file__))
        self.list_file = listfile  # 기존 Listbox (호환성)
        self.treeview = treeview  # Treeview (이벤트 목록용)
        self.txt_dest_path = txt_dest_path
        self.cmb_club = cmb_club
        self.cmb_system = cmb_system
        self.cmb_line = cmb_line
        self.club_data = None
        
        self.text_area = None
        self.select_all_var = None  # 전체 선택 체크박스 변수

        self.isReal = True
        self.api_test= None
        
        self.reserve_api_url = None
        self.system_id = None
        self.batch_entry = batch_entry  # Entry 위젯 참조
  # --------------------GUI part--------------------------------------------------

    def utc_to_seoul_time(self, utc_time_str):
        """
        UTC 시간 문자열을 서울 시간으로 변환
        """
        try:
            # UTC 시간대와 서울 시간대 설정
            utc = pytz.UTC
            seoul = pytz.timezone('Asia/Seoul')
            
            # ISO 형식에서 날짜시간 파싱
            if 'T' in utc_time_str:
                # Z 제거하고 파싱
                clean_time = utc_time_str.replace('Z', '').split('.')[0]  # 밀리초 제거
                dt_utc = datetime.datetime.strptime(clean_time, "%Y-%m-%dT%H:%M:%S")
                dt_utc = utc.localize(dt_utc)
                
                # 서울 시간으로 변환
                dt_seoul = dt_utc.astimezone(seoul)
                return dt_seoul.strftime("%Y-%m-%d %H:%M")
            else:
                return utc_time_str[:16] if len(utc_time_str) >= 16 else utc_time_str
        except Exception as e:
            print(f"시간 변환 오류: {e}")
            return utc_time_str[:16] if len(utc_time_str) >= 16 else utc_time_str

    def multi_command1(self):
        self.import_club_list()
        self.create_event_url()  # 예시: 리스트박스에 클럽 리스트 보여주기

    #파일 추가
    def add_file(self):
        files = filedialog.askopenfilenames(title="Detection할 파일을 선택하세요 ", 
                                            filetypes=(("MP4 파일","*.mp4"),("모든 파일","*.*")),
                                            initialdir=self.current_directory)
        #사용자가 선택한 파일 목록
        for file in files:
            self.list_file.insert(END,file)

    # 선택 삭제
    def del_file(self):
        # print(list_file.curselection)
        for index in reversed(self.list_file.curselection()):
            self.list_file.delete(index)

    def toggle_select_all(self):
        """전체 선택/해제 기능 (Treeview 기반)"""
        if hasattr(self, 'treeview') and self.treeview is not None:
            all_items = self.treeview.get_children()
            if self.select_all_var.get():
                # 전체 선택
                self.treeview.selection_set(all_items)
                print("전체 선택됨 (Treeview)")
            else:
                # 전체 해제
                self.treeview.selection_remove(all_items)
                print("전체 선택 해제됨 (Treeview)")

    def get_selected_items(self):
        """선택된 항목들의 값을 반환 (Treeview 기반)"""
        if hasattr(self, 'treeview') and self.treeview is not None:
            selected_items = []
            for item_id in self.treeview.selection():
                values = self.treeview.item(item_id, 'values')
                # 항상 tuple로 반환
                selected_items.append(tuple(values))
            return selected_items
        return []

    def get_selected_count(self):
        """선택된 항목의 개수를 반환 (Treeview 기반)"""
        if hasattr(self, 'treeview') and self.treeview is not None:
            return len(self.treeview.selection())
        return 0

    def extract_event_id_from_text(self, item_text):
        """이벤트 텍스트(문자열) 또는 tuple에서 이벤트 ID를 추출"""
        try:
            if isinstance(item_text, tuple):
                # Treeview 선택: (이벤트명, 홈팀, 어웨이팀, 날짜, 종료일시, 이벤트ID, HLS URL, venue_id, venue_name)
                # 이벤트ID는 6번째(인덱스 5)
                return item_text[5]
            # 기존 Listbox 문자열 처리
            parts = item_text.split(' - ')
            if len(parts) >= 2:
                event_id = parts[-1].strip()
                # 이벤트ID가 24자리 hex 등 실제 고유ID일 때만 반환
                import re
                if re.match(r'^[a-fA-F0-9]{24}$', event_id):
                    return event_id
                return None
            return None
        except Exception as e:
            print(f"이벤트 ID 추출 오류: {e}")
            return None

    def get_event_hls_urls(self, selected_items):
        """선택된 이벤트들의 HLS URL 목록을 반환"""
        hls_urls = []
        columns = []
        # Try to get columns from treeview if available
        if hasattr(self, 'treeview') and self.treeview is not None and hasattr(self.treeview, 'columns'):
            columns = self.treeview["columns"]
        for item in selected_items:
            if not isinstance(item, tuple):
                continue
            print("아이템:", item)
            print("아이템형식:", type(item))
            event_name = item[0] if len(item) > 0 else ''
            home_team = item[1] if len(item) > 1 else ''
            away_team = item[2] if len(item) > 2 else ''
            start_date = item[3] if len(item) > 3 else ''
            end_date = item[4] if len(item) > 4 else ''
            event_id = item[5] if len(item) > 5 else ''
            hd_url = item[6] if len(item) > 6 else ''
            venue_id = item[7] if len(item) > 7 else ''
            venue_name = item[8] if len(item) > 8 else ''
            # hd_url이 없으면 건너뜀 (이벤트ID는 있는데 HLS URL이 없는 경우)
            if event_id and not hd_url:
                continue
            event_info = {
                'event_id': event_id,
                'event_name': event_name,
                'hd_url': hd_url,
                'venue_id': venue_id,
                'venue_name': venue_name,
                'display_text': item
            }
            hls_urls.append(event_info)
            print(f"이벤트 {event_id} HLS URL: {hd_url}, Venue ID: {venue_id}, Venue Name: {venue_name}")
        return hls_urls
        club_options = [f"({club.get('name', '')}) {club.get('_id', '')}" for club in self.club_data]
    
        # 리스트박스에도 클럽 리스트 추가
        self.list_file.delete(0, END)  # 기존 리스트 초기화
        for club_option in club_options:
            self.list_file.insert(END, club_option)
        
    def import_system_list(self,event=None):
     
        selected = self.cmb_club.get()  # 선택된 문자열 예: "클럽A (123456)"
        # id만 추출
        if "(" in selected and ")" in selected:
            club_id = selected.split("(")[-1].replace(")", "")
        else:
            club_id = ""
        print("선택된 클럽 id:", club_id)
        
        data = self.api_test.get_api_data(f"clubs/{club_id}")
        self.reserve_api_url = f"{self.api_test.base_url}/clubs/{club_id}/events"
        print(data)

        # venues에서 id와 name 추출
        venues = data.get('venues', [])
        venue_options = [f"({venue.get('name', '')}) {venue.get('_id', '')}" for venue in venues]
        self.cmb_system['values'] = venue_options

        self.cmb_system.set('')  # 두 번째 콤보박스 선택값 초기화
    
        # if venue_options:
        #   self.cmb_system.current(0)

    def import_events_list_table(self):
        df = pd.DataFrame()
        self.api_test = PixellotAPI(self.isReal)

        # Entry 위젯에서 batch_count 값 읽기
        batch_count = 1
        if self.batch_entry is not None:
            try:
                val = int(self.batch_entry.get())
                if val > 0 and val <= 100:
                    batch_count = val
            except Exception:
                pass

        for i in range(0, batch_count * 100, 100):
            num1 = 100
            num2 = i

            ENDPOINT_EVENTS = f"events?limit={num1}&skip={num2}"
            TEAMS_DATA = self.api_test.get_api_data(ENDPOINT_EVENTS)

            if TEAMS_DATA:
                print("받아온 데이터:", TEAMS_DATA)
                df = pd.concat([df, pd.DataFrame(TEAMS_DATA)], ignore_index=True)
            else:
                print("데이터를 가져오지 못했습니다.")
                break  # 데이터가 없으면 반복 종료

        # 리스트박스에 팀 리스트 추가
        self.list_file.delete(0, END)  # 기존 리스트 초기화

        if not df.empty:
            for _, team in df.iterrows():
                team_name = team.get('name', 'Unknown')
                team_id = team.get('_id', 'N/A')
                self.list_file.insert(END, f"({team_name}) {team_id}")
        else:
            self.list_file.insert(END, "팀 데이터가 없습니다.")

    def load_club_events(self):
        """선택된 클럽의 이벤트를 불러와서 리스트박스에 표시 (batch_entry 값 사용)"""
        if not self.api_test:
            msgbox.showwarning("경고", "먼저 클럽을 불러와 주세요.")
            return
        selected_club = self.cmb_club.get()
        if not selected_club:
            msgbox.showwarning("경고", "먼저 클럽을 선택해 주세요.")
            return
        # 클럽 ID 추출
        if "(" in selected_club and ")" in selected_club:
            club_id = selected_club.split("(")[-1].replace(")", "")
        else:
            msgbox.showerror("오류", "클럽 ID를 추출할 수 없습니다.")
            return
        try:
            # batch_entry에서 batch_count 읽기
            batch_count = 1
            if hasattr(self, 'batch_entry') and self.batch_entry is not None:
                try:
                    val = int(self.batch_entry.get())
                    if val > 0 and val <= 100:
                        batch_count = val
                except Exception:
                    pass
            events_data = []
            for i in range(0, batch_count * 100, 100):
                limit = 100
                skip = i
                endpoint = f"clubs/{club_id}/events?limit={limit}&skip={skip}"
                batch_data = self.api_test.get_api_data(endpoint)
                if batch_data:
                    print(f"받아온 이벤트 데이터 (skip={skip}, limit={limit}): {len(batch_data)}개")
                    events_data.extend(batch_data)
                else:
                    print(f"더 이상 가져올 이벤트가 없습니다. (총 {len(events_data)}개 수집)")
                    break
            if not events_data:
                msgbox.showinfo("정보", "이벤트 데이터가 없습니다.")
                return
            if events_data and len(events_data) > 0:
                print("=" * 50)
                # print("첫 번째 이벤트 전체 데이터:")
                # print(events_data[0])
                # print("=" * 50)
                # print("이벤트에 있는 모든 키들:")
                # print(list(events_data[0].keys()) if events_data[0] else "No keys")
                # print("=" * 50)
            # Treeview 사용: 기존 row 삭제
            if self.treeview is not None:
                for row in self.treeview.get_children():
                    self.treeview.delete(row)
            else:
                self.list_file.delete(0, END)
            # venue_id와 venue_name 매핑 준비
            venue_id_name_map = {}
            # venues 정보 가져오기 (클럽 상세에서)
            selected_club = self.cmb_club.get()
            club_id = ''
            if '(' in selected_club and ')' in selected_club:
                club_id = selected_club.split('(')[-1].replace(')', '')
            if club_id:
                club_detail = self.api_test.get_api_data(f"clubs/{club_id}")
                venues = club_detail.get('venues', []) if club_detail else []
                for venue in venues:
                    vid = venue.get('_id', '')
                    vname = venue.get('name', '')
                    if vid:
                        venue_id_name_map[vid] = vname
            # 이벤트ID 리스트 생성 (반복문 전에 선언)
            event_id_list = []

            overlay_url_map = {}
            event_rows = []
            # 1. 모든 이벤트 정보에 대해 event_rows 생성 (overlayUrl은 나중에 추가)
            for idx, event in enumerate(events_data):
                event_id = event.get('_id', 'N/A')
                possible_name_fields = ['name', 'eventName', 'title', 'displayName', 'gameName', 'description']
                event_name = 'Unknown Event'
                for field in possible_name_fields:
                    if field in event and event[field]:
                        event_name = event[field]
                        # print(f"이벤트 이름을 '{field}' 필드에서 찾음: '{event_name}'")
                        break
                else:
                    print(f"이름 필드를 찾지 못함. 시도한 필드들: {possible_name_fields}")
                event_id_list.append(event_id)
                start_date = event.get('startDateTime', event.get('start$date', ''))
                home_team = ''
                away_team = ''
                if 'scoreboardData' in event:
                    home_team = event['scoreboardData'].get('homeTeam', '')
                    away_team = event['scoreboardData'].get('awayTeam', '')
                if not home_team:
                    home_team = event.get('homeTeam', '')
                if not away_team:
                    away_team = event.get('awayTeam', '')
                formatted_datetime = self.utc_to_seoul_time(start_date) if start_date else ''
                hls_url = ''
                if 'urls' in event and isinstance(event['urls'], dict):
                    hls_url = event['urls'].get('hd', '')
                venue_id = ''
                venue_name = ''
                if 'venue' in event and isinstance(event['venue'], dict):
                    venue_id = event['venue'].get('_id', '')
                    venue_name = venue_id_name_map.get(venue_id, '')
                    if len(venue_name) > 12:
                        venue_name = venue_name[12:]
                end_date = event.get('endDateTime', event.get('end$date', ''))
                end_datetime = self.utc_to_seoul_time(end_date) if end_date else ''
                event_rows.append([event_name, home_team, away_team, formatted_datetime, end_datetime, event_id, hls_url, venue_id, venue_name])

            # 2. 모든 이벤트ID에 대해 overlayUrl 병렬 조회하여 event_rows에 추가
            import threading
            def fetch_overlay(idx, event_id):
                vas_response = self.api_test.get_api_data(f"events/{event_id}/vas")
                overlay_url = ''
                if vas_response and isinstance(vas_response, dict):
                    if 'overlayProvider' in vas_response and isinstance(vas_response['overlayProvider'], dict):
                        overlay_url = vas_response['overlayProvider'].get('overlayUrl', '')
                        if not overlay_url:
                            overlay_url = vas_response.get('overlayUrl', '')
                    else:
                        overlay_url = vas_response.get('overlayUrl', '')
                event_rows[idx].append(overlay_url)
                overlay_url_map[event_id] = overlay_url

            threads = []
            for idx, event in enumerate(events_data):
                event_id = event.get('_id', 'N/A')
                t = threading.Thread(target=fetch_overlay, args=(idx, event_id))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()

            # overlayUrl 정보 가져오기 (진행상황 출력)
            # print(f"overlayUrl 조회 시작: 총 {len(event_id_list)}개 이벤트")
            # for idx, event_id in enumerate(event_id_list, 1):
            #     print(f"[{idx}/{len(event_id_list)}] events/{event_id}/vas 조회 완료.")
            # print("=== 모든 이벤트 overlayUrl 결과 ===")
            # for event_id, overlay_url in overlay_url_map.items():
            #     print(f"{event_id}: {overlay_url}")
            # print("overlayUrl 조회 및 출력 완료!")
            # Treeview에 데이터 삽입 (overlayUrl 추가)
            if self.treeview is not None:
                for row in event_rows:
                    self.treeview.insert('', 'end', values=row)
            else:
                for row in event_rows:
                    team_str = f" [{row[1]} vs {row[2]}]" if row[1] or row[2] else ''
                    formatted_datetime = row[3]
                    overlay_url = row[-1]
                    event_id = row[5]
                    if formatted_datetime:
                        display_text = f"({row[0]}){team_str} {formatted_datetime} - {event_id} - {overlay_url}"
                    else:
                        display_text = f"({row[0]}){team_str} - {event_id} - {overlay_url}"
                    self.list_file.insert(END, display_text)
                # 이벤트ID 리스트 출력 (마지막에 한번만)
                # print(f"불러온 이벤트ID 리스트: {event_id_list}")
            msgbox.showinfo("성공", f"{len(events_data)}개의 이벤트를 불러왔습니다.")
        except Exception as e:
            msgbox.showerror("오류", f"이벤트를 불러오는 중 오류가 발생했습니다: {str(e)}")
            print(f"Error loading events: {e}")



    def load_all_events(self):
        """전체 이벤트를 불러와서 Treeview에 표시 (batch_entry 값 사용)"""
       # self.api_test가 None이면 초기화
        if self.api_test is None:
            self.api_test = PixellotAPI(self.isReal)
        batch_count = 1
        if hasattr(self, 'batch_entry') and self.batch_entry is not None:
            try:
                val = int(self.batch_entry.get())
                if val > 0 and val <= 100:
                    batch_count = val
            except Exception:
                pass
        events_data = []
        for i in range(0, batch_count * 100, 100):
            limit = 100
            skip = i
            endpoint = f"events?limit={limit}&skip={skip}"
            batch_data = self.api_test.get_api_data(endpoint)
            if batch_data:
                print(f"받아온 전체 이벤트 데이터 (skip={skip}, limit={limit}): {len(batch_data)}개")
                events_data.extend(batch_data)
            else:
                print(f"더 이상 가져올 이벤트가 없습니다. (총 {len(events_data)}개 수집)")
                break
        if not events_data:
            msgbox.showinfo("정보", "전체 이벤트 데이터가 없습니다.")
            return
        # Treeview 사용: 기존 row 삭제
        if self.treeview is not None:
            for row in self.treeview.get_children():
                self.treeview.delete(row)
        else:
            self.list_file.delete(0, END)
        # 이벤트ID 리스트 생성 (반복문 전에 선언)
        event_id_list = []
        event_rows = []
        overlay_url_map = {}
        import threading
        # 1. 모든 이벤트 정보에 대해 event_rows 생성 (overlayUrl은 나중에 추가)
        for idx, event in enumerate(events_data):
            event_id = event.get('_id', 'N/A')
            possible_name_fields = ['name', 'eventName', 'title', 'displayName', 'gameName', 'description']
            event_name = 'Unknown Event'
            for field in possible_name_fields:
                if field in event and event[field]:
                    event_name = event[field]
                    break
            event_id_list.append(event_id)
            start_date = event.get('startDateTime', event.get('start$date', ''))
            end_date = event.get('endDateTime', event.get('end$date', ''))
            home_team = ''
            away_team = ''
            if 'scoreboardData' in event:
                home_team = event['scoreboardData'].get('homeTeam', '')
                away_team = event['scoreboardData'].get('awayTeam', '')
            if not home_team:
                home_team = event.get('homeTeam', '')
            if not away_team:
                away_team = event.get('awayTeam', '')
            formatted_datetime = self.utc_to_seoul_time(start_date) if start_date else ''
            end_datetime = self.utc_to_seoul_time(end_date) if end_date else ''
            hls_url = ''
            if 'urls' in event and isinstance(event['urls'], dict):
                hls_url = event['urls'].get('hd', '')
            venue_id = ''
            venue_name = ''
            if 'venue' in event and isinstance(event['venue'], dict):
                venue_id = event['venue'].get('_id', '')
                venue_name = event['venue'].get('name', '')
                if len(venue_name) > 12:
                    venue_name = venue_name[12:]
            event_rows.append([event_name, home_team, away_team, formatted_datetime, end_datetime, event_id, hls_url, venue_id, venue_name])

        # 2. 모든 이벤트ID에 대해 overlayUrl 병렬 조회하여 event_rows에 추가
        def fetch_overlay(idx, event_id):
            vas_response = self.api_test.get_api_data(f"events/{event_id}/vas")
            overlay_url = ''
            if vas_response and isinstance(vas_response, dict):
                if 'overlayProvider' in vas_response and isinstance(vas_response['overlayProvider'], dict):
                    overlay_url = vas_response['overlayProvider'].get('overlayUrl', '')
                    if not overlay_url:
                        overlay_url = vas_response.get('overlayUrl', '')
                else:
                    overlay_url = vas_response.get('overlayUrl', '')
            event_rows[idx].append(overlay_url)

        threads = []
        for idx, event in enumerate(events_data):
            event_id = event.get('_id', 'N/A')
            t = threading.Thread(target=fetch_overlay, args=(idx, event_id))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        # overlayUrl 정보 가져오기 (진행상황 출력)
        # print(f"overlayUrl 조회 시작: 총 {len(event_id_list)}개 이벤트")
        # for idx, event_id in enumerate(event_id_list, 1):
        #     print(f"[{idx}/{len(event_id_list)}] events/{event_id}/vas 조회 완료.")
        # print("=== 모든 이벤트 overlayUrl 결과 ===")
        # for event_id, overlay_url in overlay_url_map.items():
        #     print(f"{event_id}: {overlay_url}")
        # print("overlayUrl 조회 및 출력 완료!")
        # Treeview에 데이터 삽입 (overlayUrl 추가)
        if self.treeview is not None:
            for row in event_rows:
                self.treeview.insert('', 'end', values=row)
        else:
            for row in event_rows:
                team_str = f" [{row[1]} vs {row[2]}]" if row[1] or row[2] else ''
                formatted_datetime = row[3]
                overlay_url = row[-1]
                event_id = row[5]
                if formatted_datetime:
                    display_text = f"({row[0]}){team_str} {formatted_datetime} - {event_id} - {overlay_url}"
                else:
                    display_text = f"({row[0]}){team_str} - {event_id} - {overlay_url}"
                self.list_file.insert(END, display_text)
        # 이벤트ID 리스트 출력 (마지막에 한번만)
        # print(f"불러온 전체 이벤트ID 리스트: {event_id_list}")
        msgbox.showinfo("성공", f"{len(events_data)}개의 전체 이벤트를 불러왔습니다.")

    def start(self):
        print("선택된 venue id:", self.system_id)
        
        # 선택된 이벤트들 확인
        selected_items = self.get_selected_items()
        selected_count = self.get_selected_count()
        
        print(f"선택된 이벤트 수: {selected_count}")
        
        if selected_count == 0:
            msgbox.showwarning("경고", "선택된 이벤트가 없습니다.")
            return
        
        # HLS URL 정보 가져오기
        print("=" * 50)
        print("HLS URL 정보를 가져오는 중...")
        print("=" * 50)
        
        try:
            hls_urls = self.get_event_hls_urls(selected_items)
            
            if not hls_urls:
                msgbox.showerror("오류", "HLS URL을 가져올 수 없습니다.")
                return
            
            # 결과 출력
            print("\n=== HLS URL 목록 ===")
            result_text = "HLS URL 목록:\n\n"
            
            for i, event_info in enumerate(hls_urls, 1):
                # 컬럼명 일치에 따라 '이벤트명' 또는 'event_name' 사용
                event_name = event_info.get('이벤트명', event_info.get('event_name', ''))
                event_id = event_info.get('이벤트ID', event_info.get('event_id', ''))
                hd_url = event_info.get('HLS URL', event_info.get('hd_url', ''))

                print(f"{i}. 이벤트명: {event_name}")
                print(f"   이벤트ID: {event_id}")
                print(f"   HLS URL: {hd_url}")
                print()

                result_text += f"{i}. {event_name}\n"
                result_text += f"   ID: {event_id}\n"
                if hd_url:
                    result_text += f"   URL: {hd_url}\n"
                else:
                    result_text += f"   URL: 없음\n"
                result_text += "\n"

            # 결과를 메시지박스로 표시하고 다운로드 여부 확인
            if len(result_text) > 500:
                display_text = result_text[:500] + "...\n\n자세한 내용은 콘솔을 확인하세요."
            else:
                display_text = result_text
                
            # 다운로드 여부 확인
            download_choice = msgbox.askyesno("HLS URL 결과", 
                                            display_text + "\n\n지금 다운로드를 시작하시겠습니까?")
            
            if download_choice:
                # 다운로드 실행 (스레드로 실행하여 GUI 블록 방지)
                download_thread = threading.Thread(target=self.hls_url_download, args=(hls_urls,), daemon=True)
                download_thread.start()

            # print(hls_urls)
            return hls_urls  # 다른 함수에서 사용할 수 있도록 반환
            
        except Exception as e:
            error_msg = f"HLS URL을 가져오는 중 오류가 발생했습니다: {str(e)}"
            print(error_msg)
            msgbox.showerror("오류", error_msg)
            return []
        

    def hls_url_download(self, hls_urls):
        """HLS URL을 사용하여 비디오 다운로드"""
        if not hls_urls:
            print("HLS URL이 없습니다.")
            return
            
        print("HLS URL 다운로드 시작...")
        
        # 다운로드 폴더 생성 (실행파일 위치 기준)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = self.current_directory
        download_folder = os.path.join(base_dir, "downloads")
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
            print(f"다운로드 폴더 생성: {download_folder}")
        
        download_results = []
        
        for i, event_info in enumerate(hls_urls):
            try:
                # hd_url 추출
                hd_url = event_info.get('hd_url', '')
                event_name = event_info.get('event_name', 'Unknown')
                event_id = event_info.get('event_id', 'unknown_id')

                # HLS URL 정보가 없으면 팝업 후 건너뜀
                if not hd_url:
                    msgbox.showinfo("HLS URL 정보 없음", f"이벤트명: {event_name}\n이벤트ID: {event_id}\nHLS URL 정보가 없습니다.\n다운로드를 건너뜁니다.")
                    print(f"이벤트 '{event_name}'에 HLS URL이 없습니다. 건너뜁니다.")
                    continue

                # 라이브 스트림 안내: hlsid=HTTP_ID_ 포함시 팝업 및 건너뜀
                if 'hlsid=HTTP_ID_' in hd_url:
                    msgbox.showinfo("라이브 스트림 안내", f"이벤트명: {event_name}\n이 영상은 현재 라이브 중입니다.\n다운로드는 녹화 완료 후 가능합니다.")
                    print(f"[라이브 중] {event_name} - {hd_url}")
                    continue

                # 안전한 파일명 생성 (특수문자 제거 및 한국어 처리)
                import unicodedata

                # 한국어와 영문, 숫자, 기본 특수문자만 허용
                safe_chars = []
                for c in event_name:
                    if c.isalnum() or c in (' ', '-', '_', '.'):
                        safe_chars.append(c)
                    elif ord(c) >= 0xAC00 and ord(c) <= 0xD7A3:  # 한글 범위
                        safe_chars.append(c)
                    else:
                        safe_chars.append('_')  # 기타 특수문자는 언더스코어로 대체

                safe_name = ''.join(safe_chars).strip()

                # 파일명이 너무 길면 자르기
                if len(safe_name) > 100:
                    safe_name = safe_name[:100]

                # 빈 이름 방지
                if not safe_name:
                    safe_name = f"event_{event_id}"

                output_filename = f"{safe_name}_{event_id}.mp4"
                output_path = os.path.join(download_folder, output_filename)

                print(f"\n다운로드 {i+1}/{len(hls_urls)}")
                print(f"이벤트명: {event_name}")
                print(f"HLS URL: {hd_url}")
                print(f"저장 경로: {output_path}")

                # HLS URL 유효성 검사
                if not hd_url.startswith(('http://', 'https://')):
                    print(f"❌ 유효하지 않은 URL: {hd_url}")
                    raise Exception(f"유효하지 않은 URL 형식: {hd_url}")

                # ffmpeg를 사용하여 HLS 다운로드
                print(f"⏳ ffmpeg 다운로드 시작...")

                try:
                    # conda 환경의 ffmpeg 경로 사용
                    ffmpeg_path = r"C:\Users\jwhon\anaconda3\Library\bin\ffmpeg.exe"

                    # 가장 리눅스 일반적인 경로
                    # ffmpeg_path = "/usr/bin/ffmpeg"

                    # 실시간 progress와 로그를 위해 ffmpeg-python 사용
                    # GPU 가속 옵션 (기본값: False, CPU 복사 모드)
                    use_gpu = False  # True로 변경하면 GPU 가속 사용
                    self.download_with_progress(ffmpeg_path, hd_url, output_path, event_name, use_gpu)

                    # 파일이 실제로 생성되었는지 확인
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        print(f"✓ 다운로드 완료: {output_filename}")
                        print(f"✓ 파일 크기: {os.path.getsize(output_path)} bytes")
                    else:
                        raise Exception("파일이 생성되지 않았거나 크기가 0입니다.")

                except Exception as ffmpeg_err:
                    error_details = str(ffmpeg_err)
                    print(f"❌ ffmpeg 오류: {error_details}")
                    raise Exception(f"ffmpeg 다운로드 실패: {error_details}")

                print(f"✓ 다운로드 완료: {output_filename}")
                download_results.append({
                    'event_name': event_name,
                    'event_id': event_id,
                    'output_path': output_path,
                    'status': 'success'
                })

            except ffmpeg.Error as e:
                error_msg = f"ffmpeg 오류 - 이벤트 '{event_name}': {e.stderr.decode() if e.stderr else str(e)}"
                print(f"✗ {error_msg}")
                download_results.append({
                    'event_name': event_name,
                    'event_id': event_id,
                    'status': 'failed',
                    'error': error_msg
                })

            except Exception as e:
                error_msg = f"다운로드 오류 - 이벤트 '{event_name}': {str(e)}"
                print(f"✗ {error_msg}")
                download_results.append({
                    'event_name': event_name,
                    'event_id': event_id,
                    'status': 'failed',
                    'error': error_msg
                })
        
        # 결과 요약
        success_count = len([r for r in download_results if r['status'] == 'success'])
        failed_count = len([r for r in download_results if r['status'] == 'failed'])
        
        print(f"\n=== 다운로드 완료 ===")
        print(f"성공: {success_count}개")
        print(f"실패: {failed_count}개")
        print(f"다운로드 폴더: {download_folder}")
        
        # 메시지박스로 결과 표시
        result_msg = f"다운로드 완료!\n\n성공: {success_count}개\n실패: {failed_count}개\n\n저장 위치: {download_folder}"
        msgbox.showinfo("다운로드 결과", result_msg)
        
        return download_results

    def download_with_progress(self, ffmpeg_path, hd_url, output_path, event_name, use_gpu=False):
        """Progress bar와 실시간 로그를 포함한 ffmpeg 다운로드"""
        
        # Progress 창 생성
        progress_window = Toplevel()
        progress_window.title(f"다운로드 중: {event_name}")
        progress_window.geometry("600x400")
        progress_window.resizable(True, True)
        
        # 창을 최상위로 설정
        progress_window.transient()
        progress_window.grab_set()
        
        # Progress bar
        progress_label = Label(progress_window, text="다운로드 준비 중...", font=("Arial", 10))
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate', length=400)
        progress_bar.pack(pady=10, padx=20, fill=X)
        progress_bar.start()
        
        # 속도와 남은 시간 표시
        stats_label = Label(progress_window, text="", font=("Arial", 9))
        stats_label.pack(pady=5)
        
        # 로그 텍스트 영역
        log_frame = Frame(progress_window)
        log_frame.pack(pady=10, padx=20, fill=BOTH, expand=True)
        
        Label(log_frame, text="실시간 로그:", font=("Arial", 9, "bold")).pack(anchor=W)
        
        log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, font=("Consolas", 8))
        log_text.pack(fill=BOTH, expand=True)
        
        # 취소/닫기 버튼
        def on_cancel_or_close():
            self.cancel_download()
            if progress_window.winfo_exists():
                progress_window.destroy()

        cancel_button = Button(progress_window, text="취소", command=on_cancel_or_close)
        cancel_button.pack(pady=10)
        
        self.download_cancelled = False
        self.download_process = None
        
        def update_log(message):
            """로그 메시지 업데이트"""
            try:
                # 메시지 인코딩 안전 처리
                if isinstance(message, bytes):
                    message = message.decode('utf-8', errors='replace')
                elif not isinstance(message, str):
                    message = str(message)
                
                log_text.insert(END, message + "\n")
                log_text.see(END)
                progress_window.update_idletasks()
            except Exception as e:
                # 로그 출력 실패 시에도 프로그램이 중단되지 않도록
                try:
                    log_text.insert(END, f"[로그 출력 오류: {str(e)}]\n")
                    log_text.see(END)
                except:
                    pass  # 창이 닫힌 경우 무시
        
        def parse_ffmpeg_progress(line):
            """ffmpeg 출력에서 진행률 정보 추출"""
            # time=00:01:23.45 형태에서 시간 추출
            time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
            if time_match:
                hours, minutes, seconds, centiseconds = time_match.groups()
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                return total_seconds
            
            # bitrate와 speed 정보 추출
            bitrate_match = re.search(r'bitrate=\s*(\d+\.?\d*)kbits/s', line)
            speed_match = re.search(r'speed=\s*(\d+\.?\d*)x', line)
            
            return None, bitrate_match.group(1) if bitrate_match else None, speed_match.group(1) if speed_match else None
        
        try:
            # 환경 변수 설정 (한국어 인코딩 지원)
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['LANG'] = 'ko_KR.UTF-8'
            
            update_log(f"다운로드 시작: {event_name}")
            update_log(f"URL: {hd_url}")
            update_log(f"저장 위치: {output_path}")
            update_log("=" * 50)
            
            # ffmpeg-python 라이브러리 사용
            try:
                # 입력 스트림 생성
                input_stream = ffmpeg.input(hd_url)
                
                # 출력 옵션 구성
                output_options = {
                    'loglevel': 'info',
                    'stats': None,
                    'y': None  # 기존 파일 덮어쓰기
                }
                
                if use_gpu:
                    # GPU 가속 사용 (NVIDIA)
                    update_log("🚀 GPU 가속 모드로 다운로드...")
                    output_options.update({
                        'c:v': 'h264_nvenc',  # NVIDIA GPU 인코더
                        'preset': 'p1',       # 빠른 프리셋
                        'c:a': 'copy'         # 오디오는 복사
                    })
                    # GPU 가속을 위한 글로벌 인수
                    input_stream = input_stream.video.hwaccel('cuda')
                else:
                    # CPU 복사 모드 (기본값)
                    update_log("📁 CPU 복사 모드로 다운로드...")
                    output_options.update({
                        'c:v': 'copy',  # 비디오 코덱 복사 (재인코딩 안함)
                        'c:a': 'copy'   # 오디오 코덱 복사 (재인코딩 안함)
                        # 'c': 'copy'
                    })
                
                # 출력 스트림 생성
                output_stream = ffmpeg.output(input_stream, output_path, **output_options)
                
                # ffmpeg 명령어 실행 (cmd 지정)
                update_log("🚀 ffmpeg-python으로 다운로드 시작...")
                
                # progress를 위해 subprocess 방식과 결합
                cmd = ffmpeg.compile(output_stream, cmd=ffmpeg_path)
                update_log(f"실행 명령어: {' '.join(cmd[:5])}...")
                
                # subprocess로 실행하여 실시간 로그 확인
                self.download_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace',
                    env=env,
                    bufsize=1
                )
                
                duration = None
                current_time = 0
                start_time = time.time()
                
                # 실시간으로 ffmpeg 출력 읽기
                for line in self.download_process.stdout:
                    if self.download_cancelled:
                        self.download_process.terminate()
                        break
                        
                    try:
                        line = line.strip()
                        if line:
                            # 주요 정보만 로그 출력
                            if any(keyword in line.lower() for keyword in ['duration', 'stream', 'time=', 'speed=', 'error', 'warning', 'input', 'output']):
                                update_log(line)
                            
                            # Duration 정보 추출
                            if 'Duration:' in line:
                                duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
                                if duration_match:
                                    hours, minutes, seconds, centiseconds = duration_match.groups()
                                    duration = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
                                    update_log(f"🎬 총 길이: {duration}초 ({hours}:{minutes}:{seconds})")
                            
                            # Progress 정보 추출
                            progress_info = parse_ffmpeg_progress(line)
                            if isinstance(progress_info, tuple):
                                time_val, bitrate, speed = progress_info
                                current_time = time_val if time_val else current_time
                            else:
                                current_time = progress_info if progress_info else current_time
                            
                            if current_time and duration and duration > 0:
                                progress_percent = min((current_time / duration) * 100, 100)
                                elapsed_time = time.time() - start_time
                                
                                # indeterminate 모드에서 determinate 모드로 변경
                                if progress_bar['mode'] == 'indeterminate':
                                    progress_bar.stop()
                                    progress_bar.config(mode='determinate', maximum=100)
                                
                                progress_bar['value'] = progress_percent
                                
                                # 남은 시간 계산
                                if progress_percent > 0:
                                    estimated_total_time = elapsed_time / (progress_percent / 100)
                                    remaining_time = estimated_total_time - elapsed_time
                                    
                                    progress_label.config(text=f"다운로드 중... {progress_percent:.1f}% ({current_time}초 / {duration}초)")
                                    stats_label.config(text=f"남은 시간: {int(remaining_time//60)}분 {int(remaining_time%60)}초")
                                
                                progress_window.update_idletasks()
                                
                    except Exception as line_error:
                        # 개별 라인 처리 오류는 로그만 남기고 계속 진행
                        update_log(f"[라인 처리 오류: {str(line_error)}]")
                        continue
                
                # 프로세스 완료 대기
                if not self.download_cancelled:
                    self.download_process.wait()
                    if self.download_process.returncode == 0:
                        progress_label.config(text="✅ 다운로드 완료!")
                        progress_bar['value'] = 100
                        stats_label.config(text="완료!")
                        update_log("✅ 다운로드 성공!")
                        cancel_button.config(text="닫기")
                        cancel_button.config(command=lambda: progress_window.destroy() if progress_window.winfo_exists() else None)
                    else:
                        progress_label.config(text="❌ 다운로드 실패!")
                        stats_label.config(text="실패!")
                        update_log(f"❌ 다운로드 실패! (오류 코드: {self.download_process.returncode})")
                        cancel_button.config(text="닫기")
                        cancel_button.config(command=lambda: progress_window.destroy() if progress_window.winfo_exists() else None)
                else:
                    update_log("❌ 사용자에 의해 취소됨")
                    progress_label.config(text="취소됨")
                    cancel_button.config(text="닫기")
                    cancel_button.config(command=lambda: progress_window.destroy() if progress_window.winfo_exists() else None)
                    
            except ffmpeg.Error as ffmpeg_err:
                error_msg = f"ffmpeg-python 라이브러리 오류: {ffmpeg_err.stderr.decode('utf-8', errors='replace') if ffmpeg_err.stderr else str(ffmpeg_err)}"
                update_log(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            update_log(f"❌ 오류: {str(e)}")
            progress_label.config(text="오류 발생!")
            cancel_button.config(text="닫기")
            cancel_button.config(command=lambda: progress_window.destroy() if progress_window.winfo_exists() else None)
            raise e
        finally:
            # 3초 후 자동으로 창 닫기 (수동으로 닫지 않은 경우)
            if not self.download_cancelled and self.download_process and self.download_process.returncode == 0:
                progress_window.after(1500, lambda: progress_window.destroy() if progress_window.winfo_exists() else None)

    def cancel_download(self):
        """다운로드 취소"""
        self.download_cancelled = True
        if self.download_process:
            try:
                self.download_process.terminate()
            except:
                pass

    def create_studio_urls(self):
        """선택된 이벤트들의 스튜디오 URL이 포함된 Excel 파일 생성"""
        # 선택된 이벤트들 확인
        selected_items = self.get_selected_items()
        selected_count = self.get_selected_count()
        
        print(f"선택된 이벤트 수: {selected_count}")
        
        if selected_count == 0:
            msgbox.showwarning("경고", "선택된 이벤트가 없습니다.")
            return
        
        if not self.api_test:
            msgbox.showwarning("경고", "먼저 클럽을 불러와 주세요.")
            return
        
        try:
            studio_data = []
            print("선택된 이벤트들의 스튜디오 URL 생성 중...")
            # venue_id와 venue_name 매핑 준비
            venue_id_name_map = {}
            selected_club = self.cmb_club.get()
            club_id = ''
            if '(' in selected_club and ')' in selected_club:
                club_id = selected_club.split('(')[-1].replace(')', '')
            if club_id:
                club_detail = self.api_test.get_api_data(f"clubs/{club_id}")
                venues = club_detail.get('venues', []) if club_detail else []
                for venue in venues:
                    vid = venue.get('_id', '')
                    vname = venue.get('name', '')
                    if vid:
                        venue_id_name_map[vid] = vname

            # overlayUrl 병렬 조회를 위한 준비
            overlay_url_map = {}
            def fetch_overlay(event_id):
                vas_response = self.api_test.get_api_data(f"events/{event_id}/vas")
                overlay_url = ''
                if vas_response and isinstance(vas_response, dict):
                    if 'overlayProvider' in vas_response and isinstance(vas_response['overlayProvider'], dict):
                        overlay_url = vas_response['overlayProvider'].get('overlayUrl', '')
                        if not overlay_url:
                            overlay_url = vas_response.get('overlayUrl', '')
                    else:
                        overlay_url = vas_response.get('overlayUrl', '')
                overlay_url_map[event_id] = overlay_url

            # 이벤트ID 추출 및 overlayUrl 병렬 조회
            event_id_list = []
            threads = []
            for i, item_text in enumerate(selected_items):
                event_id = self.extract_event_id_from_text(item_text)
                if event_id:
                    event_id_list.append(event_id)
                    t = threading.Thread(target=fetch_overlay, args=(event_id,))
                    threads.append(t)
                    t.start()
            for t in threads:
                t.join()

            # 이벤트 상세 정보 및 studio_data 생성 (selected_items에서 직접 추출)
            for i, item in enumerate(selected_items):
                try:
                    # dict 기반 접근
                    if isinstance(item, dict):
                        event_id = item.get('이벤트ID', '')
                        event_name = item.get('이벤트명', '')
                        home_team = item.get('홈팀', '')
                        away_team = item.get('어웨이팀', '')
                        start_date_seoul = item.get('시작일시', '')
                        end_date_seoul = item.get('종료일시', '')
                        venue_name = item.get('venue_name', '')
                    else:
                        event_id = self.extract_event_id_from_text(item)
                        event_name = item[0] if len(item) > 0 else ''
                        home_team = item[1] if len(item) > 1 else ''
                        away_team = item[2] if len(item) > 2 else ''
                        start_date_seoul = item[3] if len(item) > 3 else ''
                        end_date_seoul = item[4] if len(item) > 4 else ''
                        venue_name = item[8] if len(item) > 8 else ''
                    if not event_id:
                        print(f"이벤트 ID를 추출할 수 없습니다: {item}")
                        continue
                    print(f"처리 중: {i+1}/{selected_count} - 이벤트 ID: {event_id}")
                    studio_url = f"https://corehub.aisportstv.com/Studio/StudioMgmt?eventid={event_id}"
                    overlay_url = overlay_url_map.get(event_id, '')
                    studio_data.append({
                        '이벤트명': event_name,
                        '홈팀': home_team,
                        '어웨이팀': away_team,
                        '이벤트ID': event_id,
                        '시작일시(서울)': start_date_seoul,
                        '종료일시(서울)': end_date_seoul,
                        '장비명': venue_name,
                        '스튜디오URL': studio_url,
                        'overlayUrl': overlay_url
                    })
                    print(f"✓ 처리 완료: {event_name}")
                except Exception as e:
                    print(f"이벤트 처리 중 오류: {item} - {str(e)}")
                    continue
            
            if not studio_data:
                msgbox.showerror("오류", "처리할 수 있는 이벤트가 없습니다.")
                return
            
            # DataFrame 생성 및 '장비명' 기준 정렬
            df = pd.DataFrame(studio_data)
            df = df.sort_values(by='장비명', na_position='last').reset_index(drop=True)
            
            # 파일 저장 위치 선택 (CSV)
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"studio_urls_{current_time}.csv"
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
            else:
                exe_dir = self.current_directory
            file_path = filedialog.asksaveasfilename(
                title="CSV 파일 저장",
                defaultextension=".csv",
                initialfile=default_filename,
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=exe_dir
            )
            if not file_path:
                print("파일 저장이 취소되었습니다.")
                return
            try:
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                print(f"✅ CSV 파일 저장 완료: {file_path}")
                result_msg = f"스튜디오 URL CSV 파일이 생성되었습니다!\n\n"
                result_msg += f"• 처리된 이벤트: {len(studio_data)}개\n"
                result_msg += f"• 저장 위치: {file_path}\n\n"
                result_msg += "파일을 열어서 확인하시겠습니까?"
                open_file = msgbox.askyesno("완료", result_msg)
                if open_file:
                    try:
                        os.startfile(file_path)
                    except Exception as open_err:
                        print(f"파일 열기 오류: {open_err}")
                        msgbox.showinfo("알림", f"파일이 저장되었습니다: {file_path}")
            except Exception as save_err:
                error_msg = f"CSV 파일 저장 중 오류가 발생했습니다: {str(save_err)}"
                print(error_msg)
                msgbox.showerror("저장 오류", error_msg)
                return
            
            # 콘솔에 결과 출력
            print("\n=== 스튜디오 URL 생성 결과 ===")
            for i, data in enumerate(studio_data, 1):
                print(f"{i}. {data['이벤트명']}")
                print(f"   시작: {data['시작일시(서울)']}")
                print(f"   종료: {data['종료일시(서울)']}")
                print(f"   스튜디오 URL: {data['스튜디오URL']}")
                print(f"   overlayUrl: {data['overlayUrl']}")
                print()
            
            return df
            
        except Exception as e:
            error_msg = f"스튜디오 URL 생성 중 오류가 발생했습니다: {str(e)}"
            print(error_msg)
            msgbox.showerror("오류", error_msg)
            return None

    def yesno(text):
        response = msgbox.askyesno("Make AR Video",text)

        if response ==1:
            print("Yes")
        elif response ==0:
            print("No")
        return response