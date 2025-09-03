import tkinter.ttk as ttk
from tkinter import * #__all__
import pandas as pd
import tkinter.messagebox as msgbox
from tkinter import filedialog,scrolledtext #sub module
from tkcalendar import DateEntry

import os
import sys
import time
from Pixellot_api import PixellotAPI
from GUI_function import Function


if __name__ == "__main__":

    root = Tk()
    root.title("Piexellot API GUI")

    # 클럽 프레임
    path_frame = LabelFrame(root, text="Pixellot 정보")
    path_frame.pack(fill="x", padx=5, pady=5, ipady=5)

    # 첫 번째 줄
    row1 = Frame(path_frame)
    row1.pack(fill="x")
    lbl1 = Label(row1, text="Pixellot 클럽 리스트", width=18)
    lbl1.pack(side="left")

    # Function 객체 미리 생성 (treeview는 아래에서 할당)
    gui = Function()

    gui.cmb_club = ttk.Combobox(row1, state="readonly", values=[], width=100)
    gui.cmb_club.pack(side="left", padx=1, pady=1)

    btn1 = Button(row1, text="Pixellot 클럽 조회", width=15, command=gui.import_club_list)
    btn1.pack(side="left", padx=5, pady=5)

    gui.cmb_club.bind("<<ComboboxSelected>>", gui.import_system_list)

    isReal_var = BooleanVar(value=True)
    isReal = True
    chk = Checkbutton(row1, text="운영 서버 사용", variable=isReal_var, command=gui.update_isReal)
    chk.pack(side="left", padx=5, pady=5)

    # 두 번째 줄
    row2 = Frame(path_frame)
    row2.pack(fill="x")
    lbl2 = Label(row2, text="Pixellot 시스템 리스트", width=18)
    lbl2.pack(side="left")
    gui.cmb_system = ttk.Combobox(row2, state="readonly", values=[], width=100)
    gui.cmb_system.pack(side="left", padx=1, pady=1)
    gui.cmb_system.bind("<<ComboboxSelected>>", gui.create_event_url)
    
    # 출력 경로를 Pixellot 시스템 리스트 아래에 배치
    row3 = Frame(path_frame)
    row3.pack(fill="x")
    lbl_dest = Label(row3, text="촬영 예약 URL(구현 X)", width=18)
    lbl_dest.pack(side="left")
    gui.txt_dest_path = Entry(row3, width=80)
    gui.txt_dest_path.pack(side="left", padx=2, pady=2)


    #클럽 이벤트 조회 버튼 추가
    btn_load_events = Button(row2, text="클럽 이벤트 조회", width=15, command=gui.load_club_events)
    btn_load_events.pack(side="left", padx=5, pady=5)

    # 전체 이벤트 조회 버튼 추가
    btn_load_all_events = Button(row2, text="전체 이벤트 조회", width=15, command=gui.load_all_events)
    btn_load_all_events.pack(side="left", padx=5, pady=5)

    # 배치 수 입력
    batch_label = Label(row2, text="조회할 이벤트 수(x100)", width=18)
    batch_label.pack(side="left", padx=2)
    batch_entry = Entry(row2, width=5)
    batch_entry.insert(0, "1")
    batch_entry.pack(side="left", padx=2)
    gui.batch_entry = batch_entry

    # 리스트 프레임 (Treeview)
    list_frame = LabelFrame(root, text="Event List")
    list_frame.pack(fill="both", padx=5, pady=5, ipady=5, expand=True)

    # 전체 선택/해제 체크박스 프레임
    checkbox_frame = Frame(list_frame)
    checkbox_frame.pack(fill="x", padx=5, pady=(5,0))
    gui.select_all_var = BooleanVar()
    chk_select_all = Checkbutton(checkbox_frame, text="전체 선택/해제", variable=gui.select_all_var, command=gui.toggle_select_all)
    chk_select_all.pack(side="left")

    list_container = Frame(list_frame)
    list_container.pack(fill="both", padx=5, pady=5, expand=True)


    # HLS URL + venue_id + 시작/종료시간 + overlayUrl 컬럼 추가
    columns = ("이벤트명", "홈팀", "어웨이팀", "시작시간", "종료시간", "이벤트ID", "HLS URL", "장비ID", "장비명", "overlayUrl")
    treeview = ttk.Treeview(list_container, columns=columns, show="headings", height=30)
    for col, width in zip(columns, [30, 10, 10, 18, 18, 20, 40, 20, 20, 40]):
        treeview.heading(col, text=col)
        treeview.column(col, width=width*8, anchor="center")
    treeview.pack(side="left", fill="both", expand=True)


    scrollbar = Scrollbar(list_container, orient="vertical", command=treeview.yview)
    scrollbar.pack(side="right", fill='y')
    treeview.configure(yscrollcommand=scrollbar.set)

    gui.treeview = treeview

    #실행  프레임
    frame_run = Frame(root)
    frame_run.pack(fill="x",padx=5,pady=5)

    btn_close = Button(frame_run,padx = 5,pady=5, text="닫기",width=12,command=root.quit)
    btn_close.pack(side="right",padx=5,pady=5)

    btn_start = Button(frame_run,padx = 5,pady=5, text="HLS 영상 Download",width=18,command=gui.start)
    btn_start.pack(side="right",padx=5,pady=5)

    btn_studio = Button(frame_run,padx = 5,pady=5, text="스튜디오 URL 만들기",width=18,command=gui.create_studio_urls)
    btn_studio.pack(side="right",padx=5,pady=5)

    root.resizable(True,True)
    root.mainloop()
