import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 파일 이름 분리
def get_file_name(check_type):
    return "room_inspection.csv" if check_type == "개인 호실 점검" else "public_inspection.csv"

# 페이지 상태 및 초기화
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# 데이터 저장 함수
def save_data(df, check_type):
    file_name = get_file_name(check_type)
    df.to_csv(file_name, index=False, encoding='utf-8-sig')

# --- 로그인 ---
if st.session_state.page == 'login':
    st.title("기숙사 점검 시스템")
    u = st.text_input("아이디")
    p = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if {"01":"1111", "02":"2222", "03":"3333", "04":"4444"}.get(u) == p:
            st.session_state.logged_in = True
            st.session_state.user_id = u
            st.session_state.page = 'main_menu'; st.rerun()
        else: st.error("로그인 실패!")

# --- 메인 메뉴 ---
elif st.session_state.page == 'main_menu':
    st.sidebar.write(f"사용자: {st.session_state.user_id}")
    if st.sidebar.button("로그아웃"): st.session_state.logged_in = False; st.session_state.page = 'login'; st.rerun()
    st.title("메인 메뉴")
    if st.button("신규 점검하기"): st.session_state.page = 'dormitory'; st.session_state.edit_idx = None; st.rerun()
    if st.button("이전 점검 내역 확인/수정"): st.session_state.page = 'history'; st.rerun()

# --- 학사 및 유형 선택 ---
elif st.session_state.page == 'dormitory':
    st.session_state.dorm_name = st.selectbox("학사 선택", ["구연학사", "현암학사", "봉소학사", "반야학사", "선행화학사"])
    st.session_state.check_type = st.radio("점검 유형", ["개인 호실 점검", "층별 공용시설 점검"])
    if st.button("다음"): st.session_state.page = 'input'; st.rerun()
    if st.button("메인으로"): st.session_state.page = 'main_menu'; st.rerun()

# --- 입력 및 수정 페이지 ---
elif st.session_state.page == 'input':
    is_edit = st.session_state.get('edit_idx') is not None
    st.title("점검 정보 입력")
    
    check_type = st.session_state.check_type
    file_name = get_file_name(check_type)
    df = pd.read_csv(file_name, encoding='utf-8-sig') if os.path.exists(file_name) else pd.DataFrame()
    
    old_data = df.iloc[st.session_state.edit_idx] if is_edit else None
    dorm = old_data["학사"] if is_edit else st.session_state.dorm_name
    st.info(f"학사: {dorm} | 유형: {check_type}")

    target_label = "점검 층수" if check_type == "층별 공용시설 점검" else "호실/층수"
    target = st.text_input(target_label, value=old_data["대상"] if is_edit else "")
    
    if check_type == "개인 호실 점검":
        items = ["침대", "바닥/벽", "가구류", "가전(냉장고/공유기)", "전등/콘센트", "위생시설", "샤워시설", "창문", "청소도구"]
    else:
        items = ["복도/계단", "화장실(공용)", "샤워실(공용)", "정수기", "전자레인지", "세탁실", "현관/출입문"]
    
    item_details = {}
    for item in items:
        val = old_data[item] if (is_edit and item in old_data and not pd.isna(old_data[item])) else ""
        with st.expander(f"📌 {item}"):
            if st.checkbox(f"{item} 문제 있음", key=f"chk_{item}", value=(val != "")):
                item_details[item] = st.text_input(f"{item} 상세 내용", key=f"txt_{item}", value=val)
            else:
                item_details[item] = ""

    if st.button("제출"):
        new_row = {"일시": datetime.now().strftime("%Y-%m-%d %H:%M"), "아이디": str(st.session_state.user_id),
                   "학사": dorm, "유형": check_type, "대상": target, **item_details}
        if is_edit: df = df.drop(st.session_state.edit_idx)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df, check_type)
        st.success("저장 완료!")
        st.session_state.edit_idx = None
        st.session_state.page = 'main_menu'; st.rerun()
    
    if st.button("취소/메인으로"): st.session_state.page = 'main_menu'; st.rerun()

# --- 이전 내역 페이지 ---
elif st.session_state.page == 'history':
    st.title("이전 점검 내역")
    selected_type = st.radio("보기 원하는 내역 선택", ["개인 호실 점검", "층별 공용시설 점검"])
    file_name = get_file_name(selected_type)
    
    if os.path.exists(file_name):
        df = pd.read_csv(file_name, encoding='utf-8-sig')
        st.dataframe(df, use_container_width=True)
        
        idx = st.number_input("대상 행 번호 (위 표의 인덱스)", min_value=0, max_value=len(df)-1, step=1)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ 선택 내역 수정하기"):
                st.session_state.edit_idx = idx
                st.session_state.check_type = selected_type
                st.session_state.page = 'input'; st.rerun()
        with col2:
            if st.button("🗑️ 선택 내역 삭제하기"):
                df = df.drop(idx).reset_index(drop=True)
                save_data(df, selected_type)
                st.success(f"{idx}번 행이 삭제되었습니다!")
                st.rerun()
        
        st.divider()
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(f"📥 {selected_type} 엑셀로 다운로드", csv, file_name, 'text/csv')
    else: 
        st.write("저장된 내역이 없습니다.")
    
    if st.button("메인으로"): st.session_state.page = 'main_menu'; st.rerun()
