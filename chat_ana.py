import streamlit as st
import pandas as pd
import re
from io import BytesIO

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Group Chat Extractor", page_icon="🎓", layout="wide")

# ---------------- FUNCTION TO PARSE CHAT ----------------
def parse_whatsapp_chat(file_content):

    pattern = r'^\[?(\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\]?\s(?:-|:)?\s'
    
    data = []
    message = []
    date_buffer = None
    
    lines = file_content.split('\n')
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            if message and date_buffer:
                raw_text = ' '.join(message)
                split_msg = re.split(r':\s', raw_text, maxsplit=1)
                if len(split_msg) > 1:
                    data.append([date_buffer, split_msg[0].strip(), split_msg[1].strip()])
                else:
                    data.append([date_buffer, "System", raw_text])
            
            date_buffer = match.group(1)
            remaining_text = line[match.end():]
            message = [remaining_text]
        else:
            message.append(line.strip())

    # Add last message
    if message and date_buffer:
        raw_text = ' '.join(message)
        split_msg = re.split(r':\s', raw_text, maxsplit=1)
        if len(split_msg) > 1:
            data.append([date_buffer, split_msg[0].strip(), split_msg[1].strip()])
        else:
            data.append([date_buffer, "System", raw_text])

    df = pd.DataFrame(data, columns=["DateTime", "Sender", "Message"])
    return df


# ---------------- MAIN UI ----------------
st.title("🎓 WhatsApp Group Material Extractor")
st.markdown("Extract **Syllabus, Notes, PDFs** sent by Teachers")

uploaded_file = st.file_uploader("Upload WhatsApp Chat (.txt)", type="txt")

if uploaded_file is not None:

    # Decode file
    try:
        file_content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        file_content = uploaded_file.getvalue().decode("utf-16")

    with st.spinner("Analyzing Chat..."):
        df = parse_whatsapp_chat(file_content)

    # Remove System messages
    users_list = df['Sender'].unique().tolist()
    if 'System' in users_list:
        users_list.remove('System')
    users_list.sort(reverse=True)


    # ---------------- SIDEBAR ----------------
    st.sidebar.header("👨‍🏫 Teacher Filters")

    selected_teachers = st.sidebar.multiselect(
        "Select Teachers",
        users_list
    )

    # ---------------- FILTERING ----------------
    filtered_df = df.copy()

    if selected_teachers:
        filtered_df = filtered_df[filtered_df['Sender'].isin(selected_teachers)]
    else:
        st.info("👈 Please select at least one teacher from sidebar")
    
    # ---------------- DISPLAY RESULTS ----------------
    if selected_teachers:

        st.subheader(f"📊 Found {len(filtered_df)} messages")

        # -------- SUMMARY --------
        summary = filtered_df['Sender'].value_counts().reset_index()
        summary.columns = ['Teacher', 'Message Count']

        st.write("### 📈 Message Summary")
        st.dataframe(summary)

        # -------- DOWNLOAD CSV --------
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download as CSV",
            csv,
            "teacher_materials.csv",
            "text/csv",
            key='download-csv'
        )

        # -------- DOWNLOAD EXCEL --------
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Teacher Data')
            summary.to_excel(writer, index=False, sheet_name='Summary')

        excel_data = output.getvalue()

        st.download_button(
            "📥 Download as Excel",
            excel_data,
            "teacher_materials.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key='download-excel'
        )

        # -------- SHOW MESSAGES --------
        if not filtered_df.empty:
            st.write("### 📚 Messages")
            for index, row in filtered_df.iterrows():
                st.markdown(f"""
**{row['DateTime']}**  
👨‍🏫 **{row['Sender']}**  
{row['Message']}  
---
""")
        else:
            st.warning("No messages found with current filters.")

else:
    st.info("👆 Upload your WhatsApp group chat file to begin.")
