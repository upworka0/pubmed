import textract


def extract_text(pdf_path):
    text = textract.process(pdf_path)
    return text
