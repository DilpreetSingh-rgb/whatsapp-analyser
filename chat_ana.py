import streamlit as st
import pandas as pd
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Class Syllabus Finder", page_icon="🎓", layout="wide")

# --- FUNCTION ---
def parse_whatsapp_chat(file_content):

    pattern = r'^\[?(\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\]?\s(?:-|:)?\s'
    
    data = []
    message = []
    date = ""
    
    lines = file_content.split('\n')
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            if message:
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

    if message:
        raw_text = ' '.join(message)
        split_msg = re.split(r':\s', raw_text, maxsplit=1)
        if len(split_msg) > 1:
            data.append([date_buffer, split_msg[0].strip(), split_msg[1].strip()])
        else:
            data.append([date_buffer, "System", raw_text])

    df = pd.DataFrame(data, columns=["DateTime", "Sender", "Message"])
    return df

# --- MAIN APP UI ---
st.title("🎓 Class Material Extractor")
st.markdown("""
**Goal:** Extract **Syllabus, Notes, and PDFs** sent specifically by **Teachers**.
""")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload WhatsApp Chat (.txt)", type="txt")

if uploaded_file is not None:
    # Decode file
    try:
        file_content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        file_content = uploaded_file.getvalue().decode("utf-16")

    with st.spinner('Analyzing Chat...'):
        df = parse_whatsapp_chat(file_content)
    
    # Get unique users list for the sidebar
    users_list = df['Sender'].unique().tolist()
    if 'System' in users_list: users_list.remove('System')
    users_list.sort()

    # --- SIDEBAR CONTROLS ---
    st.sidebar.header("👨‍🏫 Teacher Filters")
    
    # A. Select Teachers (Multi-Select)
    st.sidebar.info("Step 1: Select who your teachers are.")
    selected_teachers = st.sidebar.multiselect(
        "Select Teachers (You can pick multiple)", 
        users_list
    )

    # --- FILTERING LOGIC ---
    filtered_df = df.copy()

    # 1. Filter by Teachers
    if selected_teachers:
        filtered_df = filtered_df[filtered_df['Sender'].isin(selected_teachers)]
    else:
        st.info("👈 Please select at least one Teacher in the sidebar to start filtering.")

        # --- DISPLAY RESULTS ---
    if selected_teachers:
        st.subheader(f"Found {len(filtered_df)} messages from selected teachers")

        # Download Button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download This Teacher's Data",
            csv,
            "teacher_materials.csv",
            "text/csv",
            key='download-csv'
        )

        if not filtered_df.empty:
            for index, row in filtered_df.iterrows():
                st.markdown(f"""
                {row['DateTime']}\n
                - {row['Sender']} 👨‍🏫\n
                    - {row['Message']}\n
""")
        else:
            st.warning("No messages found. Try removing the keyword or unchecking 'Only Media'.")

else:
    st.info("👆 Upload your class group chat to extract teacher notes.")
