import streamlit as st
import pandas as pd
from docx import Document
from io import BytesIO
import time
import re
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import os

chrome_options = Options()

chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--single-process")
chrome_options.add_argument("--disable-dev-tools")
chrome_options.add_argument("--no-zygote")
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")

st.set_page_config(page_title="📤 WhatsApp Bot", page_icon="💬")
st.title("📤 WhatsApp Bot")

uploaded_excel = st.file_uploader("📄 Upload Excel file", type=['xlsx'])
uploaded_word = st.file_uploader("📝 Upload Word template", type=['docx'])

def generate_message(template_file, row_data):
    doc = Document(template_file)
    full_text = []
    pattern = re.compile(r"\((.*?)\)")
    for para in doc.paragraphs:
        text = para.text
        matches = pattern.findall(text)
        for match in matches:
            if match in row_data:
                value = str(row_data[match])
                text = text.replace(f"({match})", value)
        full_text.append(text)
    return "\n".join(full_text)

def clean_phone_number(raw_phone):
    cleaned = re.sub(r'\D', '', str(raw_phone))
    if cleaned.startswith("0"):
        cleaned = cleaned[1:]
    return "20" + cleaned if cleaned.startswith("1") and len(cleaned) == 10 else None

def send_whatsapp_message(phone_number, message):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        st.info("Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='textbox'], div[data-tab]")))

        st.success("Logged in successfully, opening chat...")
        encoded_message = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={phone_number}&text={encoded_message}"
        driver.get(url)

        st.info("Sending message...")
        wait = WebDriverWait(driver, 30)
        send_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]')))
        send_button.click()
        time.sleep(5)
    except Exception as e:
        st.error(f"⚠️ Failed to send message: {e}")
    finally:
        driver.quit()

if uploaded_excel and uploaded_word:
    df = pd.read_excel(uploaded_excel)
    st.success("✅ Files uploaded successfully")

    st.subheader("📋 Review generated messages")

    messages_list = []
    for idx, row in df.iterrows():
        message = generate_message(uploaded_word, row)
        messages_list.append({"Name": row.get("Student Name", f"Student {idx+1}"), "Phone": row.get("Phone", ""), "Message": message})
        with st.expander(f"📨 Message for: {row.get('Student Name', f'Student {idx+1}')}"):
            st.code(message)

    st.markdown("---")

    test_number = st.text_input("📞 Test WhatsApp number")
    if st.button("🧪 Send test message") and test_number:
        try:
            test_message = messages_list[0]['Message']
            send_whatsapp_message(clean_phone_number(test_number), test_message)
            st.success("✅ Test message sent")
        except Exception as e:
            st.error(f"❌ Test message failed: {e}")

    available_columns = df.columns.tolist()
    name_col = None
    for col in available_columns:
        if "name" in col.lower():
            name_col = col
            break

    if name_col:
        selected_students = st.multiselect("Select students to send messages to:", df[name_col].tolist(), default=df[name_col].tolist())
    else:
        selected_students = []
        st.warning("⚠️ Could not find a column with student names.")

    if st.button("🚀 Send messages via WhatsApp"):
        for idx, row in df.iterrows():
            if name_col and row[name_col] not in selected_students:
                continue
            phone = clean_phone_number(row.get('Phone', ''))
            if not phone:
                st.error(f"❌ Invalid phone number: {row.get('Phone', '')} for student {row.get(name_col, f'Student {idx+1}')}.")
                continue
            message = generate_message(uploaded_word, row)
            st.write(f"📤 Sending to {row.get(name_col, f'Student {idx+1}')} at {phone}...")
            try:
                send_whatsapp_message(phone, message)
                st.success(f"✅ Message sent to {row.get(name_col, f'Student {idx+1}')}")
            except Exception as e:
                st.error(f"❌ Failed to send to {row.get(name_col, f'Student {idx+1}')} at {phone}: {e}")

    csv_output = pd.DataFrame(messages_list)
    csv_data = csv_output.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download messages as CSV", data=csv_data, file_name="whatsapp_messages.csv", mime="text/csv")