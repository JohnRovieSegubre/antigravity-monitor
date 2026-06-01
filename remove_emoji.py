import re

def remove_emojis(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    # Replacing specific emojis and symbols used in the markdown
    replacements = {
        '⚡': '',
        '💳': '',
        '🧠': '',
        '📚': '',
        '🚫': '- ',
        '🔐': '- ',
        '1️⃣': '1. ',
        '2️⃣': '2. ',
        '⚠️': 'WARNING:',
        '🗄️': '',
        '⚖️': '',
        '🔴': '',
        '🟢': '',
        '🤖': '',
        '👤': '',
        '🔥': '',
        '🆔': '',
        '⛽': ''
    }

    for k, v in replacements.items():
        text = text.replace(k, v)
        
    # Standard fallback regex to catch any other emojis outside the basic multilingual plane
    emoji_pattern = re.compile(u"[\U00010000-\U0010ffff]", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)

print(f"Removing emojis from landing/skill.md and llm.txt...")
remove_emojis("landing/skill.md")
remove_emojis("llm.txt")
print("Done.")
