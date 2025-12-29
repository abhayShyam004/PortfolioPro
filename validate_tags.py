
import re

def validate_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    stack = []
    errors = []
    
    # Simple regex for finding tags. Note: This is a basic parser and might be fooled by scripts/comments.
    # tailored for this specific debugging (looking for div/section/form structure).
    
    tag_re = re.compile(r'<\s*(/?)\s*(\w+)[^>]*>')
    
    # We want to track: div, section, form, main, header, footer, body
    target_tags = {'div', 'section', 'form', 'main', 'header', 'footer', 'body'}
    
    void_tags = {'img', 'br', 'hr', 'input', 'meta', 'link'}

    for i, line in enumerate(lines):
        line_num = i + 1
        # Skip comments (basic check)
        if '<!--' in line and '-->' in line:
            # Assumes single line comment for simplicity or simple blocks. 
            # Real HTML parsing is harder, but this suffices for structure checks.
            temp_line = re.sub(r'<!--.*?-->', '', line)
        else:
            temp_line = line
            
        tags = tag_re.findall(temp_line)
        
        for is_close, tag_name in tags:
            tag_name = tag_name.lower()
            
            if tag_name not in target_tags:
                continue
            
            if not is_close:
                # Opening tag
                # Check if self-closing via slash at end? regex doesn't capture it well in group 1
                # Check raw string
                full_tag_match = re.search(r'<\s*' + tag_name + r'[^>]*>', temp_line)
                if full_tag_match and full_tag_match.group(0).endswith('/>'):
                    continue
                
                stack.append((tag_name, line_num))
            else:
                # Closing tag
                if not stack:
                    errors.append(f"Line {line_num}: Unexpected closing </{tag_name}> (Stack empty)")
                    continue
                
                last_tag, last_line = stack[-1]
                if last_tag == tag_name:
                    stack.pop()
                else:
                    # Mismatch
                    # Check if we can find the matching tag deeper in stack (implies missing closing tags for others)
                    found = False
                    for idx in range(len(stack)-1, -1, -1):
                        if stack[idx][0] == tag_name:
                            # Found match higher up. Everything in between is unclosed.
                            unclosed = stack[idx+1:]
                            errors.append(f"Line {line_num}: Closing </{tag_name}> found, but {unclosed} expecting closure first. (Opened at lines {[x[1] for x in unclosed]})")
                            # We pop everything down to match
                            stack = stack[:idx]
                            found = True
                            break
                    
                    if not found:
                         errors.append(f"Line {line_num}: Unexpected closing </{tag_name}>. Expected closing </{last_tag}> (Opened at {last_line})")

    if stack:
        errors.append(f"End of file: Unclosed tags remaining: {stack}")
        
    return errors

errors = validate_html(r'b:\Documents\vscode\New folder\DjangoProject\portfolio\resume\app\templates\app\admin_panel.html')
for e in errors:
    print(e)
