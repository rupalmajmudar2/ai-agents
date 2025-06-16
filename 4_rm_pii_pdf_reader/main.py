import fitz  # PyMuPDF
import json
import re
import os
import openai

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text("text")  # Extract text from page
    return text

# Function to redact PII values based on field names in extracted text
def redact_pii_fields(text, pii_field_names):
    original_pii = {}
    redacted_text = text
    for field in pii_field_names:
        # Pattern: FieldName: value OR FieldName value (value can be anything except newline)
        pattern = rf"({re.escape(field)}\s*[:]?\s+)([^\n\.]+)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            field_label, value = match
            original_pii[field] = value.strip()
            # Replace value with REDACTED
            redacted_text = re.sub(re.escape(field_label) + re.escape(value), field_label + "REDACTED", redacted_text)
    return redacted_text, original_pii

# Function to process the PDF, extract attributes and PII, and return a JSON
def process_pdf(pdf_path, pii_field_names, output_txt_path):
    # Extract text from the PDF
    text = extract_text_from_pdf(pdf_path)
    # Redact PII values
    anonymized_text, original_pii = redact_pii_fields(text, pii_field_names)
    # Save the anonymized text to a file
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(anonymized_text)
    # Create a JSON structure to hold the output data
    result = {
        "anonymized_text": anonymized_text,
        "original_pii": original_pii
    }
    return result

def find_similar_pii_fields_with_llm(text, canonical_fields, openai_api_key):
    from openai import OpenAI
    import json as pyjson
    client = OpenAI(api_key=openai_api_key)
    prompt = f"""
Given the following canonical PII field names: {canonical_fields}
Find all field names in the following text that are semantically similar or equivalent to the canonical list. Return a JSON mapping from each canonical field to a list of similar field names found in the text.

Text:
{text}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        content = response.choices[0].message.content
        mapping = pyjson.loads(content)
    except Exception:
        mapping = {}
    return mapping

# Define PII field names for anonymization
pii_field_names = [
    'Name',
    'Gender',
    'DateOfBirth',
    'Email',
    'Phone',
    'Address',
    'Zip'
]

# Example input PDF
input_pdf = 'original.pdf'
output_txt = 'anonymized.txt'

# Try to find the PDF in the script directory and workspace root
possible_paths = [
    os.path.join(os.path.dirname(__file__), input_pdf),
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', input_pdf)),
    os.path.abspath(input_pdf)
]
pdf_found = False
for path in possible_paths:
    if os.path.isfile(path):
        input_pdf = path
        pdf_found = True
        break

if not pdf_found:
    print('FileNotFoundError: Could not find original.pdf. Tried the following paths:')
    for path in possible_paths:
        print('  -', path)
    print('Please place original.pdf in one of these locations or specify the correct path.')
    exit(1)

# Extract text from PDF
pdf_text = extract_text_from_pdf(input_pdf)

# Use OpenAI to find similar field names
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError('Please set your OPENAI_API_KEY environment variable.')

similar_fields_mapping = find_similar_pii_fields_with_llm(pdf_text, pii_field_names, openai_api_key)
print('Similar PII field names found by LLM:')
print(json.dumps(similar_fields_mapping, indent=2))

# Expand pii_field_names with similar fields found by LLM
expanded_pii_fields = set(pii_field_names)
for field, similars in similar_fields_mapping.items():
    expanded_pii_fields.update(similars)

# Process the PDF and get the result in JSON format
result = process_pdf(input_pdf, list(expanded_pii_fields), output_txt)

# Print the result as JSON
print(json.dumps(result, indent=2))

# Optionally, save the result to a JSON file
with open("output.json", "w") as json_file:
    json_file.write(json.dumps(result, indent=4))
