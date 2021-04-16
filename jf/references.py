import pdfplumber
import jf.pdf_conversion
import logging
import re

logger = logging.getLogger("pitch_generator")


def find_year(page):
    # we need to look for the word Initial submission:
    text = page.extract_text(x_tolerance=1, y_tolerance=4)
    if "Initial submission:" in text:
        poz = text.find("Initial submission:")
        text = text[poz:]
        text = text.split('\n')[0]
        date = int(text[-4:])
        return True, date
    else:
        return False, ""


def find_reference_start(page):
    # we need to look for the word reference
    text = page.extract_text(x_tolerance=1, y_tolerance=4)
    if "REFERENCES" in text:
        #print(f"found it")
        poz = text.find("REFERENCES") + len("REFERENCES")
        text = text[poz:]
        #logger.info(f"this is the first part of the references {text}")
        return True, text+"\n"
    else:
        return False, ""


def get_reference_page(page):
    # check if this is the last page or not
    text = page.extract_text(x_tolerance=1, y_tolerance=4)
    # remove the first line
    #logger.info(f"before the split {text}")
    text = "\n".join(text.split("\n")[1:])
    #logger.info(f"after the split {text}")
    stop = False
    if "Supporting Information" in text:
        # it is the last page
        poz = text.find("Supporting Information")
        text = text[0:poz]
        stop = True
    return stop, text+"\n"


def get_references(file_name, article):
    # this gets the references from the References section and stores them as text

    pdf = pdfplumber.open(file_name)

    final_text = ""
    found = False
    found_year = False
    # this is different, because the references are not captured at first since they are a smaller font
    for page in pdf.pages:
        if not found_year:
            found_year, year = find_year(page)
            if found_year:
                article["year"] = year
                logger.info(f"The article year is {article['year']}")
        if not found:
            found, text = find_reference_start(page)
            if found:
                final_text = text
                continue
        else:
            # we are in the middle of the references
            stop, text = get_reference_page(page)
            final_text += text
            if stop:
                break

    # we have all the references
    #logger.info(f"here are all the references {final_text}")
    # convert them to a list
    reference_list = final_text.split(".\n")
    merged_references = []
    for ref in reference_list:
        #logger.info(f"{ref}")
        merged_references.append(jf.pdf_conversion.merge_lines(ref))
        logger.info(f"{merged_references[-1]}")

    article['references'] = merged_references


def construct_reference_struct(article):
    # we break down the reference into authors and year and the rest
    ref_list = article["references"]
    ref_struct = []
    reg_ex = r"\b(?P<authors>(?:[^,\n]*, )+)(?P<year>\d{4}[a-z]?), (?P<rest>.*)"
    for ref in ref_list:
        matched = re.findall(reg_ex, ref)
        if matched:
            auth = matched[0][0]
            year = matched[0][1]
            rest = matched[0][2]
            d = {"auth": auth, "year": year, "rest": rest, "count": 0, "score": 0}
            ref_struct.append(d)
    article["ref_struct"] = ref_struct


def count_references(ref_struct):
    # this is a bit ugly since I assume that converted will be used here
    fd = open("converted.txt", encoding="utf-8")
    reg_ex = r"((?P<auth0>[A-Z][\w]+),)?((?P<auth1>[A-Z][\w]+),? and)?(?P<auth2>[A-Z][\w]+)( et al\.)? \((?P<year>\d{4}[a-z]?)\)"
    matches = []
    for line in fd:
        # we have a paragraph a we match the regex
        para_matches = re.finditer(reg_ex, line)
        matches.extend(list(para_matches))

    logger.info(f"we found {len(list(matches))} matches")
    for m in matches:
        auth0 = m["auth0"]
        auth1 = m["auth1"]
        auth2 = m["auth2"]
        year = m["year"]
        # print(auth1, auth2, year)
        found = False
        for reference in ref_struct:
            if (auth0 and auth0 in reference["auth"]) or not auth0:
                if (auth1 and auth1 in reference["auth"]) or not auth1:
                    if (auth2 and auth2 in reference["auth"]) or not auth2:
                        if year in reference["year"]:
                            # print("we matched {} with {}".format(reference, m))
                            reference["count"] += 1
                            found = True
        if not found:
            logger.warning("This is odd, but I could not find {} auth0={}, auth1={}, auth2={}, year={}".format(m, auth0, auth1, auth2, year))


def compute_reference_score(article):
    year = article["year"]
    for ref in article["ref_struct"]:
        if len(ref["year"]) == 5:
            ref_year = int(ref["year"][:-1])
        else:
            ref_year = int(ref["year"])
        ref["score"] = ref["count"] * (20 - year + ref_year)

    scores = []
    for ref in article["ref_struct"]:
        scores.append(ref["score"])
    scores.sort(reverse=True)
    scores = scores[0:3]
    top_references = []
    for score in scores:
        for ref in article["ref_struct"]:
            if ref["score"] == score:
                top_references.append(ref)
                article["ref_struct"].remove(ref)
    # if we have more than 3, we remove the excess ones
    if len(top_references) > 3:
        # bubble sort
        changed = True
        while changed:
            changed = False
            for i in range(0, len(top_references)-1):
                if top_references[i]["score"] == top_references[i+1]["score"]:
                    if top_references[i]["year"] < top_references[i+1]["year"]:
                        changed = True
                        top_references[i], top_references[i+1] = top_references[i+1], top_references[i]

    article["top_references"] = top_references[0:3]


if __name__ == "__main__":
    article = {}

    filename = "C:/personal projects/robert pitch/Anderson_JF_2018.pdf"
    #filename = "C:/personal projects/robert pitch/Short-Selling Risk JF (005).pdf"
    #filename = "C:/personal projects/robert pitch/Social Capital, Trust, and Firm Performance- The Value of Corporate Social Responsibility during the Financial Cris"

    get_references(filename, article)
    construct_reference_struct(article)
    count_references(article["ref_struct"])
    compute_reference_score(article)
    print(article["top_references"])




