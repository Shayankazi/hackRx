import requests
import fitz  # PyMuPDF
import sys
import os

# Step 1: Replace with your actual Together API Key
API_KEY = "d52e2b8016723bb26cba22ba154c39a4deef6332e9c56b844c0b7e6511c1a713"

API_URL = "https://api.together.xyz/inference"
MODEL_NAME = "lgai/exaone-deep-32b"  # updated to longer context model

# Step 2: Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        sys.exit(1)

# Step 3: Ask user for PDF path
pdf_path = input("Enter path to your PDF file: ").strip()

if not os.path.exists(pdf_path):
    print("❌ File does not exist. Please check the path.")
    sys.exit(1)

# Step 4: Extract text
policy_text = extract_text_from_pdf(pdf_path)

# Step 5: Get prompt from user
print("\nEnter your prompt/question (you can reference the document below). Press Enter when done:\n")
user_prompt = input(">> ")

# Step 6: Construct final prompt
final_prompt = f"""
Document:
\"\"\"
{policy_text}
\"\"\"

{user_prompt}
"""

# Step 7: API payload
payload = {
    "model": MODEL_NAME,
    "prompt": final_prompt,
    "max_tokens": 1024,
    "temperature": 0.2,
    "top_k": 50,
    "top_p": 0.7,
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Step 8: Make API call
response = requests.post(API_URL, headers=headers, json=payload)

# Step 9: Display results
if response.status_code == 200:
    print("\n📘 Response:\n")
    print(response.json()["output"]["choices"][0]["text"].strip())
else:
    print("❌ Error:", response.status_code)
    print(response.text)
