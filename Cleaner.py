import re

ID_REGEX = re.compile(r"\b\d{8,9}\b")
GRADE_REGEX = re.compile(r"\b\d+\.\d+\b")
LINE_NUMBER_REGEX = re.compile(r"^\d+")

def parse_and_filter_lines(lines):
    """Parse lines and return only items with a valid ID and line number."""
    result = []
    for N, line in enumerate(lines, start=1):
        ids = ID_REGEX.findall(line)
        grades = GRADE_REGEX.findall(line)
        line_number_match = LINE_NUMBER_REGEX.match(line)
        line_number = line_number_match.group() if line_number_match else None
        if ids:  # Only include items with a valid ID
            result.append({
                "N": N,
                "line_number": line_number,
                "id": ids[0],
                "grade": grades[0] if grades else None
            })
    return result

