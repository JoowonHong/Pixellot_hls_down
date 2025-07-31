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
                selected_items.append(values)
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
                # Treeview 선택: (이벤트명, 홈팀, 어웨이팀, 날짜, 이벤트ID)
                return item_text[-1]
            # 기존 Listbox 문자열 처리
            parts = item_text.split(' - ')
            if len(parts) >= 2:
                event_id = parts[-1].strip()
                return event_id
            return None
        except Exception as e:
            print(f"이벤트 ID 추출 오류: {e}")
            return None

    def get_event_hls_urls(self, selected_items):
        """선택된 이벤트들의 HLS URL 목록을 반환"""
        if not self.api_test:
            print("API 객체가 없습니다.")
            return []
            
        hls_urls = []
        
        for item_text in selected_items:
            event_id = self.extract_event_id_from_text(item_text)
            if not event_id:
                print(f"이벤트 ID를 추출할 수 없습니다: {item_text}")
                continue
                
            try:
                # 이벤트 상세 정보 가져오기
                event_detail = self.api_test.get_api_data(f"events/{event_id}")
                
                if event_detail:
                    # URLs에서 hd 정보 추출
                    urls = event_detail.get('urls', {})
                    hd_url = urls.get('hd', '')
                    
                    # 이벤트 이름 추출 (다양한 필드 시도)
                    possible_name_fields = ['name', 'eventName', 'title', 'displayName', 'gameName', 'description']
                    event_name = 'Unknown Event'
                    
                    for field in possible_name_fields:
                        if field in event_detail and event_detail[field]:
                            event_name = event_detail[field]
                            print(f"이벤트 이름을 '{field}' 필드에서 찾음: '{event_name}'")
                            break
                    else:
                        print(f"이벤트 {event_id}: 이름 필드를 찾지 못함. 시도한 필드들: {possible_name_fields}")
                        print(f"사용 가능한 필드들: {list(event_detail.keys())}")
                        
                        # API에서 이름을 찾지 못한 경우, 선택된 텍스트에서 추출 시도
                        try:
                            # 형식: (이벤트명) 날짜시간 - 이벤트ID
                            if '(' in item_text and ')' in item_text:
                                start_idx = item_text.find('(') + 1
                                end_idx = item_text.find(')')
                                extracted_name = item_text[start_idx:end_idx].strip()
                                if extracted_name:
                                    event_name = extracted_name
                                    print(f"선택된 텍스트에서 이벤트 이름 추출: '{event_name}'")
                        except Exception as extract_err:
                            print(f"텍스트에서 이벤트 이름 추출 실패: {extract_err}")
                    
                    event_info = {
                        'event_id': event_id,
                        'event_name': event_name,
                        'hd_url': hd_url,
                        'display_text': item_text
                    }
                    
                    hls_urls.append(event_info)
                    print(f"이벤트 {event_id} HLS URL: {hd_url}")
                else:
                    print(f"이벤트 {event_id}의 상세 정보를 가져올 수 없습니다.")
                    
            except Exception as e:
                print(f"이벤트 {event_id} 처리 중 오류: {e}")
                continue
        
        return hls_urls

    def update_isReal(self,event =None):#미완성
        if self.isReal:
            self.isReal = False
        else:
            self.isReal = True
        print(self.isReal)
        pass

    #저장 경로 (폴더 선택)
    def create_event_url(self,event =None):
       
        self.txt_dest_path.delete(0,END)
        self.txt_dest_path.insert(0,self.reserve_api_url)
        print("촬영예약 URL:", self.reserve_api_url)
        selected = self.cmb_system.get()  # 선택된 문자열 예: "클럽A (123456)"
        # id만 추출
        if "(" in selected and ")" in selected:
            self.system_id = selected.split("(")[-1].replace(")", "")
        else:
            self.system_id = ""
        print("선택된 venue id:", self.system_id)

    def import_club_list(self):
        self.api_test = PixellotAPI(self.isReal)
        self.club_data = self.api_test.get_api_data("clubs")
        club_options = [f"{club.get('name', '')} ({club.get('_id', '')})" for club in self.club_data]
        
        # 콤보박스에 옵션 세팅
        self.cmb_club['values'] = club_options  
        
    
        # 리스트박스에도 클럽 리스트 추가
        # self.list_file.delete(0, END)  # 기존 리스트 초기화
        # for club_option in club_options:
        #  self.list_file.insert(END, club_option)
        # selected = self.cmb_club.get()  # 선택된 문자열 예: "클럽A (123456)"
    
    def import_club_list_table(self,event=NONE):

        self.api_test = PixellotAPI(self.isReal)
        self.club_data = self.api_test.get_api_data("clubs")
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

    def load_events(self):
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
                print("첫 번째 이벤트 전체 데이터:")
                print(events_data[0])
                print("=" * 50)
                print("이벤트에 있는 모든 키들:")
                print(list(events_data[0].keys()) if events_data[0] else "No keys")
                print("=" * 50)
            # Treeview 사용: 기존 row 삭제
            if self.treeview is not None:
                for row in self.treeview.get_children():
                    self.treeview.delete(row)
            else:
                self.list_file.delete(0, END)
            for i, event in enumerate(events_data):
                print(f"\n--- 이벤트 {i+1} 분석 ---")
                print(f"전체 이벤트 데이터: {event}")
                possible_name_fields = ['name', 'eventName', 'title', 'displayName', 'gameName', 'description']
                event_name = 'Unknown Event'
                for field in possible_name_fields:
                    if field in event and event[field]:
                        event_name = event[field]
                        print(f"이벤트 이름을 '{field}' 필드에서 찾음: '{event_name}'")
                        break
                else:
                    print(f"이름 필드를 찾지 못함. 시도한 필드들: {possible_name_fields}")
                event_id = event.get('_id', 'N/A')
                start_date = event.get('startDateTime', event.get('start$date', ''))
                # 홈팀/어웨이팀 추출
                home_team = ''
                away_team = ''
                if 'scoreboardData' in event:
                    home_team = event['scoreboardData'].get('homeTeam', '')
                    away_team = event['scoreboardData'].get('awayTeam', '')
                if not home_team:
                    home_team = event.get('homeTeam', '')
                if not away_team:
                    away_team = event.get('awayTeam', '')
                formatted_datetime = ''
                if start_date:
                    formatted_datetime = self.utc_to_seoul_time(start_date)
                print(f"최종 - Event name: '{event_name}', Home: '{home_team}', Away: '{away_team}', Event ID: '{event_id}', Seoul Time: '{formatted_datetime}'")
                # Treeview에 삽입
                if self.treeview is not None:
                    self.treeview.insert('', 'end', values=(event_name, home_team, away_team, formatted_datetime, event_id))
                else:
                    # 리스트 표시: (이벤트명) [homeTeam vs awayTeam] 날짜시간 - 이벤트ID
                    team_str = f" [{home_team} vs {away_team}]" if home_team or away_team else ''
                    if formatted_datetime:
                        display_text = f"({event_name}){team_str} {formatted_datetime} - {event_id}"
                    else:
                        display_text = f"({event_name}){team_str} - {event_id}"
                    self.list_file.insert(END, display_text)
            msgbox.showinfo("성공", f"{len(events_data)}개의 이벤트를 불러왔습니다.")
        except Exception as e:
            msgbox.showerror("오류", f"이벤트를 불러오는 중 오류가 발생했습니다: {str(e)}")
            print(f"Error loading events: {e}")



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
                event_name = event_info['event_name']
                event_id = event_info['event_id']
                hd_url = event_info['hd_url']
                
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
                
                if not hd_url:
                    print(f"이벤트 '{event_name}'에 HLS URL이 없습니다. 건너뜁니다.")
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
            
            for i, item_text in enumerate(selected_items):
                try:
                    # 이벤트 ID 추출
                    event_id = self.extract_event_id_from_text(item_text)
                    if not event_id:
                        print(f"이벤트 ID를 추출할 수 없습니다: {item_text}")
                        continue
                    print(f"처리 중: {i+1}/{selected_count} - 이벤트 ID: {event_id}")
                    # 이벤트 상세 정보 가져오기
                    event_detail = self.api_test.get_api_data(f"events/{event_id}")
                    if not event_detail:
                        print(f"이벤트 {event_id}의 상세 정보를 가져올 수 없습니다.")
                        continue
                    # 이벤트 이름 추출
                    possible_name_fields = ['name', 'eventName', 'title', 'displayName', 'gameName', 'description']
                    event_name = 'Unknown Event'
                    for field in possible_name_fields:
                        if field in event_detail and event_detail[field]:
                            event_name = event_detail[field]
                            break
                    else:
                        # API에서 이름을 찾지 못한 경우, 선택된 텍스트에서 추출 시도
                        try:
                            if '(' in item_text and ')' in item_text:
                                start_idx = item_text.find('(') + 1
                                end_idx = item_text.find(')')
                                extracted_name = item_text[start_idx:end_idx].strip()
                                if extracted_name:
                                    event_name = extracted_name
                        except:
                            pass
                    # 홈팀/어웨이팀 추출
                    home_team = ''
                    away_team = ''
                    # Pixellot API의 이벤트 상세에서 scoreboardData/homeTeam, awayTeam 또는 team1Name/team2Name 등 다양한 필드 시도
                    if 'scoreboardData' in event_detail:
                        home_team = event_detail['scoreboardData'].get('homeTeam', '')
                        away_team = event_detail['scoreboardData'].get('awayTeam', '')
                    if not home_team:
                        home_team = event_detail.get('homeTeam', '')
                    if not away_team:
                        away_team = event_detail.get('awayTeam', '')
                    # 시작일, 종료일 추출 (UTC -> 서울시간)
                    start_date_utc = event_detail.get('startDateTime', event_detail.get('start$date', ''))
                    end_date_utc = event_detail.get('endDateTime', event_detail.get('end$date', ''))
                    # 서울시간으로 변환
                    start_date_seoul = self.utc_to_seoul_time(start_date_utc) if start_date_utc else ''
                    end_date_seoul = self.utc_to_seoul_time(end_date_utc) if end_date_utc else ''
                    # 스튜디오 URL 생성
                    studio_url = f"https://corehub.aisportstv.com/Studio/StudioMgmt?eventid={event_id}"
                    # 데이터 추가 (컬럼 순서: 이벤트명, 홈팀, 어웨이팀, 이벤트ID ...)
                    studio_data.append({
                        '이벤트명': event_name,
                        '홈팀': home_team,
                        '어웨이팀': away_team,
                        '이벤트ID': event_id,
                        '시작일시(서울)': start_date_seoul,
                        '종료일시(서울)': end_date_seoul,
                        '스튜디오URL': studio_url
                    })
                    print(f"✓ 처리 완료: {event_name}")
                except Exception as e:
                    print(f"이벤트 처리 중 오류: {item_text} - {str(e)}")
                    continue
            
            if not studio_data:
                msgbox.showerror("오류", "처리할 수 있는 이벤트가 없습니다.")
                return
            
            # DataFrame 생성
            df = pd.DataFrame(studio_data)
            
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