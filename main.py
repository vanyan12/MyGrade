# main.py
import sys
import json
import base64
from Cleaner import parse_and_filter_lines
from compress_pdf import compress_pdf_to_target
import requests
import re

API_KEY = "K89719042488957"

def fix_separated_lines(lines):
    fixed_lines = []
    for line in lines:
        # Check if the line is a grade (e.g., a floating-point number)
        if re.match(r"^\d+\.\d{2}$", line.strip()):
            # Append the grade to the previous line
            if fixed_lines:
                fixed_lines[-1] += f"\t{line.strip()}"
        else:
            fixed_lines.append(line.strip())
    return fixed_lines

def ocr_space_file(filename, api_key=API_KEY):
    payload = {
        'isOverlayRequired': True,
        'isTable': True,
        'filetype': 'PDF',
        'apikey': api_key,
        'language': 'auto',
        'OCREngine': 2
    }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image', files={filename: f}, data=payload)
    return r.content.decode()

def get_students_grades(valid_lines):
    with open("students.json", 'r') as f:
        students = json.load(f)["students"]

    results = []
    for student in students:
        student_id = student["id"]
        student_name = student["name"]
        grade = None

        # Search for the student's ID in valid_lines
        for line in valid_lines:
            if line["id"] == student_id:
                grade = line.get("grade")
                break

        results.append({
            "name": student_name,
            "id": student_id,
            "grade": grade
        })

    return {"students": results}

def process_pdf_and_get_grades(input_pdf):
    """
    Process a PDF file in /tmp and return grades for students.
    """
    compressed_pdf = "/tmp/compressed.pdf"

    # Compress PDF
    compress_pdf_to_target(
        input_pdf=input_pdf,
        output_pdf=compressed_pdf,
        poppler_path="./poppler",  # include Linux poppler binaries in project
        start_dpi=200,
        min_dpi=70,
        start_quality=85,
        min_quality=30
    )

    # OCR
    ocr_response = ocr_space_file(filename=compressed_pdf)
    ocr_data = json.loads(ocr_response)

    # Extract and clean lines
    all_lines = []
    for result in ocr_data.get("ParsedResults", []):
        text = result.get("ParsedText", "")
        lines = text.splitlines()
        all_lines.extend(line.strip() for line in lines if line.strip())

    all_lines = fix_separated_lines(all_lines)

    # Parse valid lines
    valid_lines = parse_and_filter_lines(all_lines)

    # Get student grades
    grades = get_students_grades(valid_lines)
    return grades

def main():
    """
    Appwrite function entry point:
    Expects JSON via stdin:
    {
        "pdf_base64": "<base64 of PDF>"
    }
    """
    try:
        input_body = sys.stdin.read()
        body = json.loads(input_body)
        pdf_base64 = body["pdf_base64"]

        input_pdf = "/tmp/input.pdf"
        with open(input_pdf, "wb") as f:
            f.write(base64.b64decode(pdf_base64))

        grades = process_pdf_and_get_grades(input_pdf)

        # Appwrite function response
        print(json.dumps(grades))

    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
