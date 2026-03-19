import fitz
import os

print(" Milestone 2 Started...")

folder = "input_papers"

# 📄 Extract text
def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text()

    text = text.replace("\n", " ")
    text = " ".join(text.split())

    return text


# 📑 Extract sections
def extract_sections(text):
    text = text.lower()

    abstract = ""
    method = ""
    result = ""

    if "abstract" in text:
        start = text.find("abstract")
        end = text.find("introduction", start)
        abstract = text[start:end] if end != -1 else text[start:start+1000]

    if "method" in text:
        start = text.find("method")
        end = text.find("result", start)
        method = text[start:end] if end != -1 else text[start:start+1000]

    if "result" in text:
        start = text.find("result")
        end = text.find("conclusion", start)
        result = text[start:end] if end != -1 else text[start:start+1000]

    return abstract, method, result


# 📁 Output file
output_file = open("processed_papers.txt", "w", encoding="utf-8")

for file in os.listdir(folder):
    if file.endswith(".pdf"):
        path = os.path.join(folder, file)

        print(" Processing:", file)

        text = extract_text(path)
        abstract, method, result = extract_sections(text)

        # 🔥 YOUR FORMAT
        output_file.write(file + "\n")
        output_file.write("ABSTRACT:\n" + abstract + "\n")
        output_file.write("METHOD:\n" + method + "\n")
        output_file.write("RESULT:\n" + result + "\n")
        output_file.write("\n" + "="*80 + "\n\n")

output_file.close()

print(" Done! File saved as processed_papers.txt")