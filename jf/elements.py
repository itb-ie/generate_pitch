import re
import logging

logger = logging.getLogger("pitch_generator")

# check if a text line is empty
def is_not_empty(line):
    non_empty = r".*[\w].*"
    return re.findall(non_empty, line)


def more_lower_cases(line):
    lc = sum(1 for c in line if c.islower())
    uc = sum(1 for c in line if c.isupper())
    return lc > uc


def get_title_and_auth(fd, article):
    title = []
    auth_regex = r"[\w .'´]+"
    authors = []

    for line in fd:
        if line[0] == "\t":
            line = line[1:]

        if is_not_empty(line):
            title.append(line.replace("\n", ""))
            break
    for line in fd:
        if line[0] == "\t":
            line = line[1:]

        if is_not_empty(line):
            # there could or could be not an empty line between the title and the authors
            if more_lower_cases(line):
                title.append(line.replace("\n", ""))
            else:
                # we should be in the authors part
                # end the title
                full_title = " ".join(title)
                article["title"] = full_title
                article["short_title"] = title[0]
                # get the authors
                authors.append(line.replace("\n", ""))
                break
        else:
            full_title = " ".join(title)
            article["title"] = full_title
            article["short_title"] = title[0]
            break
    for line in fd:
        if "ABSTRACT" not in line:
            authors.append(line.replace("\n", ""))
        else:
            article["authors"] = []
            full_auth = " ".join(authors)
            for each_auth in re.findall(auth_regex, full_auth):
                if "and" in each_auth:
                    each_auth = each_auth.replace("and", "")
                each_auth = each_auth.strip()
                article["authors"].append(each_auth)
            break
    # remove the : in the short title if it is at the end:
    if article["short_title"][-1] == ":":
        article["short_title"] = article["short_title"][0:-1]


def get_intro(fd, article):
    # we work with the converted file, in which we have collated the paragrapths into a single line

    # intro is a list of paragraphs
    intro = []
    found = False
    for line in fd:
        if found:
            # need to stop, because the first chapter is starting
            if line[0:3] == "I. ":
                # need to sanitize and remove all the quotes from the beginning
                for line in reversed(intro):
                    if len(line) < 150 or line[0] == '“':
                        intro.remove(line)
                article["intro"] = intro
                return
            intro.append(line)
        if "ABSTRACT" in line:
            # 2 options here: 1) Abstract is on a line on its own, do nothing
            # ABSTRACT is at the beginning of the first paragraph
            if "ABSTRACT\n" not in line:
                intro.append(line[len("ABSTRACT"):])
            found = True


def get_sections(fd, article):
    # we have a list of sections, each section will have a name, list of subsections and a text
    article["sections"] = []
    roman_numbers = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"] # 9 should be enough I think
    letters = [" A. ", " B. ", " C. ", " D. ", " E. ", " F. ", " G. ", " H. ", " I. ", " J. "] # J should be enough
    numbers = ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."]
    logger.info("Starting to get the sections")
    sections = article["sections"]

    # prepare the roman numbers
    cur_section = roman_numbers.pop(0)
    reg_ex = fr"^{cur_section}\. "
    inside_section = False

    for line in fd:
        if re.findall(reg_ex, line):
            # reset the sub_section and subsub_section and prepare the new section entry
            sub_section_letters = letters.copy()
            subsub_section_numbers = numbers.copy()
            sub_section = sub_section_letters.pop(0)
            subsub_section = None

            sections.append({"name": "", "sub_sections": [], "text": []})
            section_name = line[len(cur_section)+2:].rstrip()

            if sub_section in section_name:
                poz = section_name.find(sub_section)
                sub_section_name = section_name[poz+len(sub_section):].rstrip()
                sections[-1]["sub_sections"].append({"name":sub_section_name, "subsub_sections":[], "text": []})
                section_name = section_name[0:poz]
                subsub_section = f"{sub_section.rstrip().lstrip()}{subsub_section_numbers.pop(0)}"
                sub_section = sub_section_letters.pop(0)
            sections[-1]["name"] = section_name
            inside_section = True
            cur_section = roman_numbers.pop(0)
            reg_ex = fr"^{cur_section}\. "
        elif inside_section:
            # we stop once we get to the references
            if "REFERENCES" in line:
                # the last section should be the conclusion one
                if "conclusion" in section_name.lower():
                    sections[-1]["name"] = "conclusion"
                # article["sections"][section_name.lower()] = section_text
                # article["sub_sections"][section_name.lower()] = sub_sections
                # article["subsub_sections"][section_name.lower()] = subsub_sections
                break
            if sub_section in line:
                # I need to split the line: get the end of the text and then open a new sub_section
                poz = line.find(sub_section)
                result = line[poz+len(sub_section):].rstrip()
                # make sure that we do not get some bogus results
                if len(result) < 100:
                    # if it is good, I need to add the start of the line to the section, sub_section, subsub_section
                    text = line[:poz]
                    sections[-1]["text"].append(text)
                    if sections[-1]["sub_sections"]:
                        sections[-1]["sub_sections"][-1]["text"].append(text)
                        if sections[-1]["sub_sections"][-1]["subsub_sections"]:
                            sections[-1]["sub_sections"][-1]["subsub_sections"][-1]["text"].append(text)

                    subsub_section_numbers = numbers.copy()
                    subsub_section = f"{sub_section.rstrip().lstrip()}{subsub_section_numbers.pop(0)}"
                    sub_section = sub_section_letters.pop(0)

                    # prepare a new sub_section
                    sections[-1]["sub_sections"].append({"name": result, "subsub_sections":[], "text":[]})

            elif subsub_section and subsub_section in line:
                poz = line.find(subsub_section)
                result = line[poz+len(subsub_section):].rstrip()
                # make sure that we do not get some bogus results
                if len(result) < 100:
                    # if it is good, I need to add the start of the line to the section, sub_section, subsub_section
                    text = line[:poz]
                    if text:
                        sections[-1]["text"].append(text)
                        if sections[-1]["sub_sections"]:
                            sections[-1]["sub_sections"][-1]["text"].append(text)
                            if sections[-1]["sub_sections"][-1]["subsub_sections"]:
                                sections[-1]["sub_sections"][-1]["subsub_sections"][-1]["text"].append(text)

                    subsub_section = subsub_section[0:-2] + f"{subsub_section_numbers.pop(0)}"

                    # prepare a new subsub_section
                    sections[-1]["sub_sections"][-1]["subsub_sections"].append({"name": result, "text": []})
            else:
                sections[-1]["text"].append(line)
                if sections[-1]["sub_sections"]:
                    sections[-1]["sub_sections"][-1]["text"].append(line)
                    if sections[-1]["sub_sections"][-1]["subsub_sections"]:
                        sections[-1]["sub_sections"][-1]["subsub_sections"][-1]["text"].append(line)

    # lets see the sections:
    for section in sections:
        logger.info(f"Section |{section['name']}|")
        for sub_sec in section["sub_sections"]:
            logger.info(f"  subsection: {sub_sec['name']}")
            for subsub_sec in sub_sec["subsub_sections"]:
                logger.info(f"      sub-subsection: {subsub_sec['name']}")

    logger.info("\n\n")


if __name__ == "__main__":
    article = {}
    fd = open("working.txt", encoding="utf-8")
    get_title_and_auth(fd, article)
    logger.info(f"{article['title']}")
    logger.info(f"{article['short_title']}")
    logger.info(f"{article['authors']}")
    fd.close()

    fd = open("converted.txt", encoding="utf-8")
    get_intro(fd, article)
    logger.info(f"Intro:")
    for line in article["intro"]:
        logger.info(f"{line}")
    fd.close()

    fd = open("converted.txt", encoding="utf-8")
    get_sections(fd, article)
    fd.close()

