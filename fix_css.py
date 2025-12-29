import os

file_path = r'b:\Documents\vscode\New folder\DjangoProject\portfolio\resume\app\static\css\styles.css'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix line 4185 (index 4184)
if len(lines) > 4184:
    print(f"Original line 4185: {lines[4184]!r}")
    if "A p p e n d i n g" in lines[4184] or "}" in lines[4184]:
        lines[4184] = "}\n"
        print("Fixed line 4185.")

# Identify duplicate "Advanced Backgrounds" blocks
# The block starts with "/* ## Advanced Backgrounds"
start_indices = [i for i, line in enumerate(lines) if "## Advanced Backgrounds" in line]
print(f"Found blocks at: {start_indices}")

if len(start_indices) > 1:
    # We have duplicates.
    # The first one is likely the one following the garbage line, which we want to remove if it's identical?
    # Actually, if I just fixed line 4185, I have valid CSS, but double definitions.
    # First block starts at 4189 (index 4188) roughly.
    # Second block starts at 4246 (index 4245).
    # I'll remove the first block: from start_indices[0]-1 (to catch the comment start line if split) to start_indices[1]-1
    
    # Refined logic: Remove lines from start_indices[0]-2 (to get separator comment) up to start_indices[1]-2
    # Let's simple check:
    # Delete from 4186 to 4243.
    # index 4186 is line 4187.
    
    # Let's just remove the first block if it looks like a duplicate.
    first_block_start = start_indices[0] - 2 # "/* ----------------..." is usually 2 lines up
    second_block_start = start_indices[1] - 2
    
    if first_block_start > 4180 and second_block_start > first_block_start:
         # Delete the first instance
         # But be careful not to delete too much.
         # Let's just delete the range [first_block_start, second_block_start)
         print(f"Deleting lines {first_block_start} to {second_block_start}")
         del lines[first_block_start:second_block_start]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("File updated.")
