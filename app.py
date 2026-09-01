import streamlit as st
import pandas as pd
import pickle

st.title("🦠 AMP Predictor")
st.write("ทำนายสายเปปไทด์ว่าเป็น Antimicrobial Peptide หรือไม่")

# โหลดโมเดล
@st.cache_resource
def load_model():
    with open('amp_stacking_model.pkl', 'rb') as f:
        return pickle.load(f)

model = load_model()
amino_acids = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 
               'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']

# สร้างแถบเมนู 2 แท็บ
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
            aac_data = {f"AAC_{aa}": [(sequence.count(aa) / len(sequence)) * 100] for aa in amino_acids}
            df_input = pd.DataFrame(aac_data)
            
            prob = model.predict_proba(df_input)[0]
            prob_amp = prob[1]
            
            st.markdown("---")
            # แสดงผลลัพธ์ 3 ระดับ
            if prob_amp >= 0.60:
                st.success(f"🟢 เป็น AMP (ความมั่นใจ {prob_amp*100:.2f}%)")
            elif prob_amp >= 0.40:
                st.warning(f"🟡 ข้อมูลก้ำกึ่ง (ความมั่นใจ {prob_amp*100:.2f}%)")
            else:
                st.error(f"🔴 ไม่ใช่ AMP (ความมั่นใจ {prob[0]*100:.2f}%)")

# ----- แท็บที่ 2: อัปโหลดไฟล์ FASTA ทีละหลายสาย -----
with tab2:
    st.write("รองรับไฟล์ `.fasta`, `.fas`, `.fa` หรือ `.txt` ที่มีเครื่องหมาย `>` นำหน้าชื่อเปปไทด์")
    uploaded_file = st.file_uploader("เลือกไฟล์ของคุณ", type=['fasta', 'fas', 'txt', 'fa'])
    
    if st.button("ทำนายผล (จากไฟล์)") and uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8').splitlines()
        sequences = {}
        curr_name = ""
        
        for line in content:
            line = line.strip()
            if line.startswith(">"):
                curr_name = line[1:]
                sequences[curr_name] = ""
            elif curr_name:
                sequences[curr_name] += line.upper()
                
        if not sequences:
            st.error("ไม่พบรูปแบบ FASTA ในไฟล์ กรุณาตรวจสอบว่ามีเครื่องหมาย `>` นำหน้าชื่อหรือไม่")
        else:
            results = []
            for name, seq in sequences.items():
                if any(aa not in amino_acids for aa in seq):
                    results.append({"ชื่อเปปไทด์": name, "ผลลัพธ์": "⚠️ พบอักขระแปลกปลอม", "ความมั่นใจ": "-"})
                    continue
                
                aac_data = {f"AAC_{aa}": [(seq.count(aa) / len(seq)) * 100] for aa in amino_acids}
                df_input = pd.DataFrame(aac_data)
                
                prob = model.predict_proba(df_input)[0]
                prob_amp = prob[1]
                
                # จัดรูปแบบตาราง 3 ระดับ
                if prob_amp >= 0.60:
                    status = "🟢 เป็น AMP"
                    conf = prob_amp * 100
                elif prob_amp >= 0.40:
                    status = "🟡 ข้อมูลก้ำกึ่ง"
                    conf = prob_amp * 100
                else:
                    status = "🔴 ไม่ใช่ AMP"
                    conf = prob[0] * 100
                
                results.append({"ชื่อเปปไทด์": name, "ผลลัพธ์": status, "ความมั่นใจ": f"{conf:.2f}%"})
            
            st.success(f"ทำนายสำเร็จทั้งหมด {len(results)} สาย")
            st.dataframe(pd.DataFrame(results), use_container_width=True)