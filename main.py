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

   
    #파일 프레임(파일추가, 선택 삭제)
    # file_frame = Frame(root)
    # file_frame.pack(fill="x",padx=5,pady=5) #간격 띄우기

    # btn_add_file = Button(file_frame,padx=5,pady=5,width=12,text="파일 추가",command = gui.add_file)
    # btn_add_file.pack(side="left")

   

    # btn_del_file = Button(file_frame,padx=5,pady=5,width=12,text="선택 삭제",command = gui.del_file)
    # btn_del_file.pack(side="right")

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
    gui.cmb_club.bind("<<ComboboxSelected>>", gui.import_system_list)

    isReal_var = BooleanVar(value=True)  # ← 추가
    isReal = True
    chk = Checkbutton(row1, text="운영서버 사용", variable=isReal_var, command=gui.update_isReal)
    chk.pack(side="left", padx=5, pady=5)

    btn1.pack(side="left", padx=5, pady=5)

    # 두 번째 줄
    row2 = Frame(path_frame)
    row2.pack(fill="x")
    lbl2 = Label(row2, text="시스템 리스트", width=15)
    lbl2.pack(side="left")
    gui.cmb_system = ttk.Combobox(row2, state="readonly", values=[], width=60)
    gui.cmb_system.pack(side="left", padx=1, pady=1)
    gui.cmb_system.bind("<<ComboboxSelected>>", gui.create_event_url)
    
    btn_load_events = Button(row2, text="이벤트 불러오기", width=15, command=gui.load_events)
    btn_load_events.pack(side="right", padx=5, pady=5)

    #api URL 프레임

    path_frame = LabelFrame(root, text="Event URL")
    path_frame.pack(fill="x",padx=5,pady=5,ipady=5)

    gui.txt_dest_path=Entry(path_frame) #"!.0" END
    gui.txt_dest_path.pack(side="left",fill="x",expand=True,padx=5,pady=5,ipady=4)#높이 변경
    # gui.txt_dest_path.insert(0,gui.api_test.base_url)

   
    
   # 옵션 프레임
    # frame_option = LabelFrame(root, text="옵션")
    # frame_option.pack(padx=5, pady=5, ipady=5)

    # 첫 번째 줄
    # row1 = Frame(frame_option)
    # row1.pack(fill="x")
    # Label(row1, text="이벤트명", width=8).pack(side="left", padx=5, pady=5)
    # event_name_var = StringVar()
    # Entry(row1, textvariable=event_name_var, width=15).pack(side="left", padx=5, pady=5)

    
    # Label(row1, text="시작일", width=6).pack(side="left", padx=2)
    # start_date_var = StringVar()
    # start_date_entry = DateEntry(row1, textvariable=start_date_var, width=12, date_pattern='yyyy-mm-dd')
    # start_date_entry.pack(side="left", padx=2)
    
    # Label(row1, text="종료일", width=6).pack(side="left", padx=2)
    # end_date_var = StringVar()
    # end_date_entry = DateEntry(row1, textvariable=end_date_var, width=12, date_pattern='yyyy-mm-dd')
    # end_date_entry.pack(side="left", padx=2)

    # Label(row1, text="인원수", width=6).pack(side="left", padx=2)
    # num_players_var = StringVar()
    # Entry(row1, textvariable=num_players_var, width=5).pack(side="left", padx=2)

    # Label(row1, text="타입", width=6).pack(side="left", padx=2)
    # opt_prod_type = ["soccer", "basketball", "baseball"]
    # cmb_prod_type = ttk.Combobox(row1, state="readonly", values=opt_prod_type, width=10)
    # cmb_prod_type.current(0)
    # cmb_prod_type.pack(side="left", padx=2)

    # Label(row1, text="권한", width=6).pack(side="left", padx=2)
    # opt_permission = ["club", "admin"]
    # cmb_permission = ttk.Combobox(row1, state="readonly", values=opt_permission, width=8)
    # cmb_permission.current(0)
    # cmb_permission.pack(side="left", padx=2)

    # # 두 번째 줄
    # row2 = Frame(frame_option)
    # row2.pack(fill="x")
    # Label(row2, text="게임타입", width=8).pack(side="left", padx=2)
    # opt_game_type = ["game", "practice"]
    # cmb_game_type = ttk.Combobox(row2, state="readonly", values=opt_game_type, width=8)
    # cmb_game_type.current(0)
    # cmb_game_type.pack(side="left", padx=2)

    # Label(row2, text="상업타입", width=8).pack(side="left", padx=2)
    # opt_commerce_type = ["members", "public"]
    # cmb_commerce_type = ttk.Combobox(row2, state="readonly", values=opt_commerce_type, width=8)
    # cmb_commerce_type.current(0)
    # cmb_commerce_type.pack(side="left", padx=2)

    # is_test_var = BooleanVar()
    # Checkbutton(row2, text="테스트", variable=is_test_var).pack(side="left", padx=5)

    # Label(row2, text="홈팀", width=6).pack(side="left", padx=2)
    # home_team_var = StringVar()
    # Entry(row2, textvariable=home_team_var, width=10).pack(side="left", padx=2)

    # Label(row2, text="어웨이팀", width=8).pack(side="left", padx=2)
    # away_team_var = StringVar()
    # Entry(row2, textvariable=away_team_var, width=10).pack(side="left", padx=2)

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

#    # 텍스트 프레임 (ScrolledText)
#     text_frame = LabelFrame(root, text="Text Area")
#     text_frame.pack(fill="x", padx=5, pady=5, ipady=5)

#     gui.text_area = scrolledtext.ScrolledText(text_frame, height=15, wrap=WORD)
#     gui.text_area.pack(fill="both", expand=True, padx=5, pady=5)

    #실행  프레임
    frame_run = Frame(root)
    frame_run.pack(fill="x",padx=5,pady=5)

    btn_close = Button(frame_run,padx = 5,pady=5, text="닫기",width=12,command=root.quit)
    btn_close.pack(side="right",padx=5,pady=5)

    btn_start = Button(frame_run,padx = 5,pady=5, text="시작",width=12,command=gui.start)
    btn_start.pack(side="right",padx=5,pady=5)

    #로그 뷰어


    # root.geometry("1280x300+50+50")
    root.resizable(False,False)# w,h 크기 변경 불가
    root.mainloop()
    # --------------------GUI part--------------------------------------------------
