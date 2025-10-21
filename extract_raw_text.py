import pdfplumber

def main():
    # Extract text from PDF
    with pdfplumber.open("reports/01.pdf") as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"Page {i+1}:")
            print(text)
            print("\n" + "="*80 + "\n")
            
            # Check if WYATT is in the text
            if "WYATT" in text:
                print(f"WYATT found on page {i+1}")
                # Get the context around WYATT
                lines = text.split("\n")
                for j, line in enumerate(lines):
                    if "WYATT" in line:
                        print(f"Line {j+1}: {line}")
                        if j > 0:
                            print(f"Previous line: {lines[j-1]}")
                        if j < len(lines) - 1:
                            print(f"Next line: {lines[j+1]}")
                print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()