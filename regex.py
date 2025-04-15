import re

phrase = "trump"
text = "trump assasination attempt"
# Also test cases:
# text = "the trump assasination"
# text = "attempted trump assasination."
# text = "trumpassasination" # Should not match

# Use word boundaries (\b) to match the whole phrase
pattern = r'\b' + re.escape(phrase.lower()) + r'\b'

print(f"Phrase: '{phrase}'")
print(f"Text: '{text}'")
print(f"Pattern: {pattern}")

if re.search(pattern, text.lower()):
    print("Match found")
else:
    print("No match")

# --- Simpler alternative (less precise) ---
# If you only need to know if the substring exists anywhere,
# even inside other words, you could use 'in':
#
# print("\nUsing 'in' operator:")
# if phrase.lower() in text.lower():
#     print("Substring found using 'in'")
# else:
#     print("Substring not found using 'in'")
# Note: This would incorrectly match 'sin' in 'assasination', for example.
# The regex approach with \b is generally better for matching specific keywords/phrases.
