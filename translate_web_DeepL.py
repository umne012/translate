import streamlit as st
import os
import tempfile
import time
import urllib.request
from urllib.error import URLError, HTTPError
import json
import deepl

# 시크릿에서 auth_key 가져오기
auth_key = st.secrets["auth_key"]
# DeepL 번역기 초기화
translator = deepl.Translator(auth_key)

def process_srt_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
        block = []
        sequence_number = 1

        for line in infile:
            if line.strip():
                block.append(line.strip())
            else:
                if len(block) >= 3:
                    outfile.write(f"{sequence_number}\n")
                    sequence_number += 1

                    outfile.write(block[1] + "\n")
                    korean_text = block[2] if any('\uAC00' <= char <= '\uD7A3' for char in block[2]) else None
                    thai_text = block[2] if any('\u0E00' <= char <= '\u0E7F' for char in block[2]) else None

                    if korean_text and not thai_text:
                        thai_translation = translator.translate_text(korean_text, "ko", "th")
                        outfile.write(korean_text + "\n")
                        outfile.write(thai_translation + "\n\n")
                    elif thai_text and not korean_text:
                        korean_translation = translator.translate_text(thai_text, "th", "ko")
                        outfile.write(korean_translation + "\n")
                        outfile.write(thai_text + "\n\n")
                    else:
                        outfile.write(block[2] + "\n")
                        outfile.write("NO TRANSLATION AVAILABLE\n\n")
                block = []
                time.sleep(0.5)

def fix_srt_labeling(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
        lines = infile.readlines()

        new_lines = []
        subtitle_number = 1

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.isdigit():
                new_lines.append(f"{subtitle_number}\n")
                subtitle_number += 1
                i += 1
            elif "-->" in line:
                new_lines.append(lines[i])
                i += 1
            elif line == "":
                new_lines.append("\n")
                i += 1
            else:
                new_lines.append(lines[i])
                i += 1

        outfile.writelines(new_lines)

def main():
    st.title("SRT File Translator and Fixer(DeepL)")

    uploaded_file = st.file_uploader("Upload an SRT file", type="srt")
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp_input:
            temp_input.write(uploaded_file.read())
            input_file = temp_input.name

        output_translated_file = tempfile.NamedTemporaryFile(delete=False, suffix="_translated.srt").name
        output_fixed_file = tempfile.NamedTemporaryFile(delete=False, suffix="_fixed.srt").name

        process_srt_file(input_file, output_translated_file)
        fix_srt_labeling(output_translated_file, output_fixed_file)

        with open(output_fixed_file, "rb") as file:
            st.download_button(
                label="Download Fixed Translated SRT File",
                data=file,
                file_name="fixed_output_translated.srt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
