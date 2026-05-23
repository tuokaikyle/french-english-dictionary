marker_start = '''<h3>A</h3>'''
marker_end = '''<p><b>zymotique</b>, <i>adj.</i>, zymotic.</p>'''

import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'pg74672-images.html')
output_path = os.path.join(script_dir, 'fr_en.html')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the first occurrence of the markers
start_idx = content.find(marker_start)
end_idx = content.find(marker_end)

if start_idx != -1 and end_idx != -1:
    # Extract content starting after marker_start and ending after marker_end
    start_pos = start_idx + len(marker_start)
    end_pos = end_idx + len(marker_end)
    extracted_content = content[start_pos:end_pos]

    with open(output_path, 'w', encoding='utf-8') as f_out:
        f_out.write(extracted_content)

    print(f"Successfully extracted {len(extracted_content)} characters (including marker_end) to {output_path}")
else:
    if start_idx == -1:
        print(f"Error: Could not find start marker: {marker_start}")
    if end_idx == -1:
        print(f"Error: Could not find end marker: {marker_end}")