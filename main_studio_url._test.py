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

    gui = Function()
    
    root = Tk()
    root.title("Piexellot API GUI")

   

    # 클럽 프레임
    
    path_frame = LabelFrame(root, text="클럽 리스트")
    path_frame.pack(fill="x", padx=5, pady=5, ipady=5)
    
    

    # 첫 번째 줄
    row1 = Frame(path_frame)
    row1.pack(fill="x")
    lbl1 = Label(row1, text="클럽 리스트", width=15)
    lbl1.pack(side="left")

    gui.cmb_club = ttk.Combobox(row1, state="readonly", values=[], width=60)
    gui.cmb_club.pack(side="left", padx=1, pady=1)

    btn1 = Button(row1, text="클럽 불러오기", width=15, command=gui.import_club_list)
    btn1.pack(side="left", padx=5, pady=5)

    gui.cmb_club.bind("<<ComboboxSelected>>", gui.import_system_list)

    isReal_var = BooleanVar(value=True)  # ← 추가
    isReal = True
    chk = Checkbutton(row1, text="운영 서버 사용", variable=isReal_var, command=gui.update_isReal)
    chk.pack(side="left", padx=5, pady=5)

   # 두 번째 줄
    row2 = Frame(path_frame)
    row2.pack(fill="x")
    lbl2 = Label(row2, text="시스템 리스트", width=15)
    lbl2.pack(side="left")
    gui.cmb_system = ttk.Combobox(row2, state="readonly", values=[], width=60)
    gui.cmb_system.pack(side="left", padx=1, pady=1)
    gui.cmb_system.bind("<<ComboboxSelected>>", gui.create_event_url)

    btn_load_events = Button(row2, text="이벤트 불러오기", width=15, command=gui.load_events)
    btn_load_events.pack(side="left", padx=5, pady=5)

    # 배치 수 입력
    batch_label = Label(row2, text="불러올 이벤트 수(x100)", width=18)
    batch_label.pack(side="left", padx=2)
    batch_entry = Entry(row2, width=5)
    batch_entry.insert(0, "1")
    batch_entry.pack(side="left", padx=2)
    gui.batch_entry = batch_entry

    # api URL 프레임

    # path_frame = LabelFrame(root, text="Event URL")
    # path_frame.pack(fill="x",padx=5,pady=5,ipady=5)

    # gui.txt_dest_path=Entry(path_frame) #"!.0" END
    # gui.txt_dest_path.pack(side="left",fill="x",expand=True,padx=5,pady=5,ipady=4)#높이 변경
    # gui.txt_dest_path.insert(0,gui.api_test.base_url)

   
    
   

    #리스트 프레임
    list_frame = LabelFrame(root, text="ID List")
    list_frame.pack(fill="x", padx=5, pady=5, ipady=5)

    # 전체 선택/해제 체크박스 프레임
    checkbox_frame = Frame(list_frame)
    checkbox_frame.pack(fill="x", padx=5, pady=(5,0))
    
    gui.select_all_var = BooleanVar()
    chk_select_all = Checkbutton(checkbox_frame, text="전체 선택/해제", variable=gui.select_all_var, command=gui.toggle_select_all)
    chk_select_all.pack(side="left")

    list_container = Frame(list_frame)
    list_container.pack(fill="both", padx=5, pady=5)

    scrollbar = Scrollbar(list_container)
    scrollbar.pack(side="right", fill='y')

    gui.list_file = Listbox(list_container, selectmode="extended", height=15, yscrollcommand=scrollbar.set)
    gui.list_file.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=gui.list_file.yview)

    
    #실행  프레임
    frame_run = Frame(root)
    frame_run.pack(fill="x",padx=5,pady=5)

    btn_close = Button(frame_run,padx = 5,pady=5, text="닫기",width=12,command=root.quit)
    btn_close.pack(side="right",padx=5,pady=5)

    btn_studio = Button(frame_run,padx = 5,pady=5, text="스튜디오 URL 만들기 시작",width=20,command=gui.create_studio_urls)
    btn_studio.pack(side="right",padx=5,pady=5)

    # btn_start = Button(frame_run,padx = 5,pady=5, text="시작",width=12,command=gui.start)
    # btn_start.pack(side="right",padx=5,pady=5)

    #로그 뷰어


    # root.geometry("1280x300+50+50")
    root.resizable(False,False)# w,h 크기 변경 불가
    root.mainloop()
    # --------------------GUI part--------------------------------------------------
