import re # provides support for regular expression

sections_list = [
    "abstract",
    "introduction",
    "methodology",
    "methods",
    "results",
    "discussion",
    "conclusion"
]

def extract_sections(text):

    sections = {}      #creates a dictionary
    current_section = "unknown"
    sections[current_section] = ""

    lines = text.split("\n")  # The paper text is broken into individual lines so we can inspect them

    for line in lines:  # Each line is checked one by one.

        line_clean = line.strip().lower() #Normalize the text

        if line_clean in sections_list:

            current_section = line_clean
            sections[current_section] = ""

        else:

            sections[current_section] += line + " " # Detect section headings

    return sections