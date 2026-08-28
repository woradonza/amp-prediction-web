import streamlit as st
import pandas as pd
import pickle

st.title("🦠 AMP Predictor")
st.write("ทำนายสายเปปไทด์ว่าเป็น Antimicrobial Peptide หรือไม่")

# 1. โหลดโมเดล (เปลี่ยนชื่อไฟล์ตามที่คุณบันทึกไว้)
@st.cache_resource
def load_model():
    with open('amp_stacking_model.pkl', 'rb') as f:
        return pickle.load(f)

model = load_model()
amino_acids = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 
               'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']

# 2. สร้างเมนูแบบแท็บ 2 ช่อง
tab1, tab2 = st.tabs(["✍️ กรอกสายเปปไทด์ (Single)", "📁 อัปโหลดไฟล์ FASTA (Multiple)"])

# ----- แท็บที่ 1: กรอกเองสายเดียว -----
with tab1:
    sequence = st.text_input("Peptide Sequence:").upper().strip()
    if st.button("ทำนายผล (สายเดียว)"):
        if not sequence:
            st.warning("กรุณากรอกสายเปปไทด์")
        elif any(aa not in amino_acids for aa in sequence):
            st.error("พบตัวอักษรที่ไม่ใช่กรดอะมิโนมาตรฐาน")
        else:
            # คำนวณ AAC (คูณ 100 เพื่อแปลงเป็นเปอร์เซ็นต์ตามที่เคยแก้ไว้)
            aac_data = {f"AAC_{aa}": [(sequence.count(aa) / len(sequence)) * 100] for aa in amino_acids}
            df_input = pd.DataFrame(aac_data)
            
            prediction = model.predict(df_input)[0]
            prob = model.predict_proba(df_input)[0]
            
            if prediction == 1:
                st.success(f"เป็น AMP (ความมั่นใจ {prob[1]*100:.2f}%)")
            else:
                st.error(f"ไม่ใช่ AMP (ความมั่นใจ {prob[0]*100:.2f}%)")

# ----- แท็บที่ 2: อัปโหลดไฟล์ FASTA ทีละหลายสาย -----
with tab2:
    st.write("รองรับไฟล์ `.fasta`, `.fas`, หรือ `.txt` ที่มีเครื่องหมาย `>` นำหน้าชื่อเปปไทด์")
    uploaded_file = st.file_uploader("เลือกไฟล์ของคุณ", type=['fasta', 'fas', 'txt', 'fa'])
    
    if st.button("ทำนายผล (จากไฟล์)") and uploaded_file is not None:
        # อ่านและแยกแยะไฟล์ FASTA
        content = uploaded_file.read().decode('utf-8').splitlines()
        sequences = {}
        curr_name = ""
        
        for line in content:
            line = line.strip()
            if line.startswith(">"):
                curr_name = line[1:] # ตัดเครื่องหมาย > ออกเพื่อใช้เป็นชื่อ
                sequences[curr_name] = ""
            elif curr_name:
                sequences[curr_name] += line.upper()
                
        if not sequences:
            st.error("ไม่พบรูปแบบ FASTA ในไฟล์ กรุณาตรวจสอบว่ามีเครื่องหมาย `>` นำหน้าชื่อหรือไม่")
        else:
            results = []
            # วนลูปทำนายทีละสายที่อ่านได้
            for name, seq in sequences.items():
                # ตรวจสอบความถูกต้องของตัวอักษร
                if any(aa not in amino_acids for aa in seq):
                    results.append({"ชื่อเปปไทด์": name, "ผลลัพธ์": "⚠️ พบอักขระแปลกปลอม", "ความมั่นใจ": "-"})
                    continue
                
                # คำนวณ AAC ของสายนั้น
                aac_data = {f"AAC_{aa}": [(seq.count(aa) / len(seq)) * 100] for aa in amino_acids}
                df_input = pd.DataFrame(aac_data)
                
                # ทำนาย
                pred = model.predict(df_input)[0]
                prob = model.predict_proba(df_input)[0]
                
                # จัดรูปแบบผลลัพธ์
                status = "🟢 เป็น AMP" if pred == 1 else "🔴 ไม่ใช่ AMP"
                conf = prob[1]*100 if pred == 1 else prob[0]*100
                
                results.append({"ชื่อเปปไทด์": name, "ผลลัพธ์": status, "ความมั่นใจ": f"{conf:.2f}%"})
            
            # นำผลลัพธ์ทั้งหมดมาแสดงเป็นตารางที่อ่านง่าย
            st.success(f"ทำนายสำเร็จทั้งหมด {len(results)} สาย")
            st.dataframe(pd.DataFrame(results), use_container_width=True)