def validate_sections(sections):  # define required section

    required = ["abstract", "introduction", "conclusion"]

    missing = []  # create missing list

    for r in required:

        if r not in sections:  # the system will loop for required sections
            missing.append(r)  # if not found it will be terminated

    return missing