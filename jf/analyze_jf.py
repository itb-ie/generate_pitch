import re
import summarize
import nltk
from itertools import chain

start_marker = "Pitch Start of Page\n"
end_marker = "\nPitch End Of Page\n"


# check if a text line is empty
def is_not_empty(line):
    non_empty = r".*[\w].*"
    return re.findall(non_empty, line)


# prepare the regexes to determine the header part
def define_regex(article):
    regex_list = [r"[\d]+ The Journal of Finance.", r"{}(?: [\d]*)?".format(article["short_title"])]
    return regex_list


# is this a junk line (starts with number as an explanation or starts woth *)
def is_junk_line(line, foot_note):
    if len(line) < 5:
        return False
    if line[0] == "*":
        return True
    if line[0] == str(foot_note):
        return True
    if foot_note > 9:
        if line[0:2] == str(foot_note) or (line[0] == str(foot_note // 10) and (
                line[2] == " " or line[1] == " ")):  # good enough to just match the first number??
            # print("Got it for {} |{}|".format(foot_note, line))
            return True
        if int(foot_note // 10) == 2 and line[0] == "?":
            # print("2 Got it for {} |{}|".format(foot_note, line))
            return True
        if int(foot_note // 10) == 3 and (line[0] == "°" or line[0] == "®"):
            # print("3 Got it for {} |{}|".format(foot_note, line))
            return True
        # 3 can also be omitted so instead of 32 we get only 2.
        if int(foot_note // 10) == 3 and (len(line) > 1) and (line[0] == str(foot_note % 10) and (line[1] == " ")):
            # print("4 Got it for {} |{}|".format(foot_note, line))
            return True

    # 2 can be mistaken for ?
    if int(foot_note) == 2 and line[0] == "?":
        return True
    # 3, 9 can be mistaken for ° or ®
    if (int(foot_note) == 3 or int(foot_note) == 9) and (line[0] == "°" or line[0] == "®"):
        return True

    # 4 can be mistaken for "
    if int(foot_note) == 4 and (line[0] == '"' or line[0] == '“'):
        return True
    # 5 can be mistaken for > or ®
    if int(foot_note) == 5 and (line[0] == ">" or line[0] == "®"):
        return True


# this function check to see if we have a comment that continues from one page to the other
def check_behind_comment(lines):
    for i in range(len(lines) - 2, 0, -1):
        if not is_not_empty(lines[i]) and lines[i + 1][0].islower():
            print("found a potential comment {}".format(lines[i:]))
            lines = lines[0:i]
            return lines
        elif not is_not_empty(lines[i]):
            return lines


def remove_junk(fd, fd2, article):
    regex_list = define_regex(article)
    lines = []
    foot_note = 0
    end_foot_note = False
    skip_header_line = False

    for line in fd:
        # add some debug here:
        if "2011, we find that long-short portfolios based on short-selling" in line:
            print("aici")

        # we skip the blank line after a foot note
        if end_foot_note or skip_header_line:
            end_foot_note = False
            skip_header_line = False
            if not is_not_empty(line):
                continue

        # skip the start of the page (for now that is all):
        if start_marker in line:
            continue

        # check if it is header line
        for reg in regex_list:
            matched = re.findall(reg, line)
            if matched:
                if line.find(matched[0]):
                    # it is in the middle of the line, so we can just remove it:
                    line = line.replace(matched[0], "")
                else:
                    # it is on the same line, so we need to remove the entire line
                    # remove the previous empty line to link them
                    if not is_not_empty(lines[-1]):
                        lines = lines[0:-1]
                    # mark to remove the next empty line if any
                    skip_header_line = True
                    break
        if skip_header_line:
            continue
        if end_marker[1:] in line:
            lines = check_behind_comment(lines)
            continue

        # if is_junk_line(line, foot_note) or (len(lines) and not is_not_empty(lines[-1]) and line[0].islower()):
        if is_junk_line(line, foot_note):
            if is_junk_line(line, foot_note):
                foot_note += 1
            # check behind to see if there were not other lines that continued a comment from previous page
            lines = check_behind_comment(lines)
            # we have the acknowledgment or foot_note line
            for other_line in fd:
                if end_marker[1:] in other_line:
                    break
                # increase the foot_nore while making sure to avoid very short lines
                if is_junk_line(other_line, foot_note) and len(other_line) > 5:
                    foot_note += 1
            # after a foot_note we need to ignore the blank line if any
            end_foot_note = True

            # remove the previous empty line to link them
            if not is_not_empty(lines[-1]):
                lines = lines[0:-1]

            continue

        lines.append(line)

    for line in lines:
        fd2.write(line)
    fd.close()
    fd2.close()


def get_year(fd, article):
    nr_lines = 0
    year_regex = r".*([\d]{4})"
    for line in fd:
        if nr_lines == 3 and is_not_empty(line):
            print(line)
            year = re.findall(year_regex, line)
            article["year"] = int(year[0])
            return
        if is_not_empty(line):
            nr_lines += 1


def more_lower_cases(line):
    lc = sum(1 for c in line if c.islower())
    uc = sum(1 for c in line if c.isupper())
    return lc > uc


def get_title_and_auth(fd, article):
    title = []
    auth_regex = r"[\w .]+"
    authors = []

    for line in fd:
        if is_not_empty(line):
            title.append(line.replace("\n", ""))
            break
    for line in fd:
        if is_not_empty(line):
            # there could or could be not an empty line between the title and the authors
            if more_lower_cases(line):
                title.append(line.replace("\n", ""))
            else:
                # we can be in the authors part
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
        if is_not_empty(line):
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


def get_abstract(fd, article):
    abstract = []
    for line in fd:
        if "ABSTRACT" in line:
            break
    # make sure there are no empty lines
    found_dash = False
    for line in fd:
        if is_not_empty(line):
            line = line.replace("\n", "")
            if "-" == line[-1]:
                line = line[:-1]
                found_dash = True
            abstract.append(line)

            break
    for line in fd:
        if is_not_empty(line):
            if found_dash:
                found_dash = False
            else:
                line = " " + line
            line = line.replace("\n", "")
            if "-" == line[-1]:
                line = line[:-1]
                found_dash = True
            abstract.append(line)
        else:
            # we are done with the abstract part
            full_abstract = "".join(abstract)
            article["abstract"] = full_abstract
            break


def get_intro(fd, article):
    # same as with abstract. we stop once we get to "I. "
    intro = []

    # make sure there are no empty lines
    found_dash = False
    for line in fd:
        if is_not_empty(line):
            line = line.replace("\n", "")
            if "-" == line[-1]:
                line = line[:-1]
                found_dash = True
            intro.append(line)
            break
    for line in fd:
        if "I. " not in line:
            if found_dash:
                found_dash = False
            else:
                line = " " + line
            if is_not_empty(line):
                line = line.replace("\n", "")
                if "-" == line[-1]:
                    line = line[:-1]
                    found_dash = True
            intro.append(line)
        else:
            # we are done with the intro part
            full_intro = "".join(intro)
            article["intro"] = full_intro
            break


def get_data(fd, article):
    roman_numbers = {1: ["I", ], 2: ["II", "lI", "Il"], 3: ["III", "lII", "llI", "Ill", "IIl", "IlI", "lIl", "lll"],
                     4: ["IV", "lV"], 5: ["V", ], 6: ["VI", ]}
    data_keywords = ["data", "sample", "evidence"]
    found_data = False
    found_chapter = False
    data = []
    # make sure there are no empty lines
    found_dash = False

    for key in roman_numbers:
        for line in fd:
            # we are in the data section
            if found_data:
                for r in roman_numbers[key]:
                    regex = r"^{}\.".format(r)
                    # print(regex)

                    if re.findall(regex, line):
                        # we are done with the data
                        full_data = "".join(data)
                        article["data_section"] = full_data
                        return
                if found_dash:
                    found_dash = False
                else:
                    line = " " + line
                if is_not_empty(line):
                    line = line.replace("\n", "")
                    if "-" == line[-1]:
                        line = line[:-1]
                        found_dash = True
                data.append(line)
                # print("We are in the data chapter and we keep searching")
                continue

            # keep looking for the data section
            for r in roman_numbers[key]:
                regex = r"^{}\.".format(r)
                # print(regex)
                if re.findall(regex, line):
                    print("Chapter: {}".format(line))
                    for kw in data_keywords:
                        if kw in line.lower():
                            print("We found the data chapter!")
                            found_data = True
                            data.append(line)
                            break
                    # we found the chapter so move to find the next chapter
                    found_chapter = True
                    break
            if found_chapter:
                found_chapter = False
                break


def get_conclusion_section(fd, article):
    roman_numbers = {1: ["I", ], 2: ["II", "lI", "Il"], 3: ["III", "lII", "llI", "Ill", "IIl", "IlI", "lIl", "lll"],
                     4: ["IV", "lV"], 5: ["V", ], 6: ["VI", ], 7: ["VII", ]}
    conclusion_keywords = ["conclusion"]
    found_cl = False
    found_chapter = False
    data = []
    # make sure there are no empty lines
    found_dash = False

    for key in roman_numbers:
        for line in fd:
            # we are in the conclusion section
            if found_cl:
                if "Initial submission" in line:
                    # we are done with the conclusion
                    full_data = "".join(data)
                    article["conclusion_section"] = full_data
                    return
                if found_dash:
                    found_dash = False
                else:
                    line = " " + line
                if is_not_empty(line):
                    line = line.replace("\n", "")
                    if "-" == line[-1]:
                        line = line[:-1]
                        found_dash = True
                data.append(line)
                # continue to exhaust the conclusion section
                continue

            # keep looking for the conclusion section
            for r in roman_numbers[key]:
                regex = r"^{}\.".format(r)
                # print(regex)
                if re.findall(regex, line):
                    print("Chapter: {}".format(line))
                    for kw in conclusion_keywords:
                        if kw in line.lower():
                            print("We found the conclusion chapter!")
                            found_cl = True
                            data.append(line)
                            break
                    # we found the chapter so move to find the next chapter
                    found_chapter = True
                    break
            if found_chapter:
                found_chapter = False
                break


def parse_data_section(article, data):
    sentence_list = []
    paragraphs = data.split("\n")
    good_sentences = []
    for p in paragraphs:
        sentence_list.extend(nltk.sent_tokenize(p))
    for sen in sentence_list:
        if "data " in sen.lower() and "database" in sen.lower():
            good_sentences.append(sen)
    article["data_source"] = good_sentences


def get_references(fd, article):
    references = []
    for line in fd:
        if line == "REFERENCES\n":
            print("Found the references line!")
            break
    # start getting the references until we get to the
    ref = []
    for line in fd:
        if "Supporting Information" in line:
            # we end

            break
        if is_not_empty(line):
            if len(ref) and ref[-1] == "-":
                ref = ref[0:-1] + line.replace("\n", "")
            elif len(ref):
                ref = ref + " " + line.replace("\n", "")
            else:
                ref = line.replace("\n", "")
        else:
            if ref:
                references.append(ref)
                ref = []

    article["references"] = references


def construct_reference_struct(article, ref_list):
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


def count_references(ref_struct, fd):
    reg_ex = r"((?P<auth1>[A-Z][\w]+) and )?(?P<auth2>[A-Z][\w]+)( et al\.)? \((?P<year>\d{4}[a-z]?)\)"
    # split into paragraphs
    # print("Here are the paragraphs\n\n\n\n")
    para = ""
    matches = []
    found_dash = False
    for line in fd:
        if not is_not_empty(line):
            # we have a paragraph a we match the regex
            para_matches = re.finditer(reg_ex, para)
            matches.extend(list(para_matches))
            para = ""
            found_dash = False
        else:
            # remove the \n
            line = line[:-1]
            if found_dash:
                para = para + line
            else:
                para = para + " " + line
            if line[-1] == "-":
                found_dash = True
            else:
                found_dash = False

    print("we found {} matches".format(len(list(matches))))
    for m in matches:
        auth1 = m["auth1"]
        auth2 = m["auth2"]
        year = m["year"]
        # print(auth1, auth2, year)
        found = False
        for reference in ref_struct:
            if (auth1 and auth1 in reference["auth"]) or not auth1:
                if (auth2 and auth2 in reference["auth"]) or not auth2:
                    if year in reference["year"]:
                        # print("we matched {} with {}".format(reference, m))
                        reference["count"] += 1
                        found = True
        if not found:
            print("This is odd, but I could not find {} auth1={}, auth2={}, year={}".format(m, auth1, auth2, year))


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
    article["top_references"] = top_references


def get_contributions(article):
    data = article["intro"] + article["conclusion_section"]
    keywords1 = ["our study", "our analysis", "our paper", "our findings", "we find", "we study", "we analyze", "this paper", "this study"]
    keywords2 = [" our", " we"]
    potentials = {}
    paragraphs = data.split("\n")
    eliminated_so_what = False
    for para in paragraphs:
        # eliminate the paragraph if it is the same as the so what paragraph
        if para == article["so_what"]:
            print("get_contribution: skipping so_what paragraph")
            eliminated_so_what = True
            continue
        if para.lower().count("contribution"):
            potentials[para] = 0
    '''
    print("We have found these potential paragraphs!")
    for pot in potentials:
        print(pot)
    '''
    if len(potentials) > 1:
        # we have several contribution paragraphs, need to score them

        for key in potentials:
            potentials[key] = potentials[key] + key.lower().count("contribution") * 10
            for k1 in keywords1:
                potentials[key] = potentials[key] + key.lower().count(k1) * 3
            for k1 in keywords2:
                potentials[key] = potentials[key] + key.lower().count(k1) * 1

        for key in potentials:
            print("Contribution: score {} for {}".format(potentials[key], key))

        max_score = max(potentials.values())
        for key in potentials:
            if potentials[key] == max_score:
                article["contribution"] = key
    elif len(potentials) == 1:
        article["contribution"] = list(potentials.keys())[0]
    else:
        print('Get_contribution: This is bad: we could not find any paragraph with the word "contribution"')
        if (eliminated_so_what):
            print("it is because we have eliminated the so what para, we put it back in")
            article["contribution"] = article["so_what"]
        else:
            article["contribution"] = ""


def get_so_what(article):
    data = article["intro"] + article["conclusion_section"]
    keywords1 = ["collectively", "overall", "import", "signif", "economically"]
    keywords2 = ["we ", "our ", "i ", "my "]
    potentials = {}
    paragraphs = data.split("\n")
    for para in paragraphs:
        if para == article["motivation"]:
            print("we are skipping the motivation part")
            continue
        # only keep collectively
        position = para.lower().find("collectively")
        if position >= 0:
            para = para[position:]
            potentials[para] = 0
        else:
            for k in keywords1:
                if k in para.lower():
                    potentials[para] = 0
                    break

    if len(potentials) > 1:
        # we have several contribution paragraphs, need to score them

        for key in potentials:
            for k1 in keywords1:
                if k1 == keywords1[0] or k1 == keywords1[1]:
                    potentials[key] = potentials[key] + key.lower().count(k1) * 7
                else:
                    potentials[key] = potentials[key] + key.lower().count(k1) * 3
            for k1 in keywords2:
                potentials[key] = potentials[key] + key.lower().count(k1) * 1
            # one standard deviation in the same sentence, gets 20 points
            sentences = key.lower().split(".")
            for s in sentences:
                if "one" in s and "standard" in s and "deviation" in s:
                    potentials[key] = potentials[key] + 20

            # lets try to normalize for paragraph length?
            if len(key):
                #potentials[key] = 10000 * potentials[key] // len(key)
                pass

        for key in potentials:
            print("So what score {} for {}".format(potentials[key], key))

        max_score = max(potentials.values())
        for key in potentials:
            if potentials[key] == max_score:
                article["so_what"] = key
    elif len(potentials) == 1:
        article["so_what"] = list(potentials.keys())[0]


def get_key_findings(article):
    data = article["intro"] + article["conclusion_section"]
    keywords1 = ["result", "find", "evidence"]
    keywords2 = ["we ", "our "]
    potentials = {}
    paragraphs = data.split("\n")
    for para in paragraphs:
        # eliminate the contribution paragraph
        if para == article["contribution"]:
            print("Key Findings: We eliminate the contribution paragraph!")
            continue

        # remove collectively
        position = para.lower().find("collectively")
        if position >= 0:
            para = para[0:position]
        if "find" in para.lower() or "result" in para.lower():
            potentials[para] = 0
            # check if this is the first paragraph in the conclusion, so we need to add 5 points to it:
            cl_paragraphs = article["conclusion_section"].split("\n")
            for cl_para in cl_paragraphs:
                if len(cl_para) > 100:
                    if para[0:50] in cl_para:
                        print("WE found the first para in the conclusion, so we add 5 points")
                        potentials[para] = 5
                    break

    if len(potentials) > 1:
        # we have several contribution paragraphs, need to score them

        for key in potentials:
            for k1 in keywords1:
                potentials[key] = potentials[key] + key.lower().count(k1) * 3
            for k1 in keywords2:
                potentials[key] = potentials[key] + key.lower().count(k1) * 1

            # lets try to normalize for paragraph length?
            if len(key):
                potentials[key] = 10000 * potentials[key] // len(key)
                #pass

        for key in potentials:
            print("Key Findings normalized: score {} for {}".format(potentials[key], key))

        max_score = max(potentials.values())
        for key in potentials:
            if potentials[key] == max_score:
                article["key_findings"] = key
    elif len(potentials) == 1:
        article["key_findings"] = list(potentials.keys())[0]


def get_first_paragraph(article):
    data = article["intro"]
    paragraphs = data.split("\n")
    for para in paragraphs:
        if para[0] != '"' and para[0] != '“' and para[0] != '”' and \
                para[-1] != '"' and para[-1] != '“' and para[-1] != '”' and \
                len(para) > 200:
            return para


def get_motivation(article):
    data = article["intro"]
    keywords1 = ["results", "find"]
    keywords2 = ["we", "our"]
    keywords = ["important", "importance", "objective"]
    potentials = {}
    paragraphs = data.split("\n")
    for para in paragraphs:
        if keywords[0] in para.lower() or keywords[1] in para.lower():
            potentials[para] = 0
    '''
    print("We have found these potential paragraphs!")
    for pot in potentials:
        print(pot)
    '''
    if len(potentials) > 1:
        # we have several contribution paragraphs, need to score them

        for key in potentials:
            for k1 in keywords:
                potentials[key] = potentials[key] + key.lower().count(k1) * 3
            for k1 in keywords1:
                potentials[key] = potentials[key] - key.lower().count(k1) * 3
            for k1 in keywords2:
                potentials[key] = potentials[key] - key.lower().count(k1) * 1

            # lets try to normalize for paragraph length?
            if len(key):
                # potentials[key] = potentials[key] / len(key)
                pass

        for key in potentials:
            print("Get Motivation: score {} for {}".format(potentials[key], key))

        # here the max score wins
        max_score = max(potentials.values())
        if max_score < 0:
            article["motivation"] = get_first_paragraph(article)
        else:
            for key in potentials:
                if potentials[key] == max_score:
                    article["motivation"] = key
    elif len(potentials) == 1:
        # the motivation can easily give false positives, so in the case of one candidate, let's examine the score.
        for key in potentials:
            for k1 in keywords:
                potentials[key] = potentials[key] + key.lower().count(k1) * 3
            for k1 in keywords1:
                potentials[key] = potentials[key] - key.lower().count(k1) * 3
            for k1 in keywords2:
                potentials[key] = potentials[key] - key.lower().count(k1) * 1
        print("only have one potential with score of {}".format(potentials[key]))
        if potentials[key] < 0:
            print("The potential seems wrong, so get the first paragraph in the intro")
            article["motivation"] = get_first_paragraph(article)
        else:
            article["motivation"] = list(potentials.keys())[0]
    else:
        print("No potential, so get the first paragraph in the intro")
        article["motivation"] = get_first_paragraph(article)


def get_whats_new(article):
    data = article["intro"]
    keywords1 = [" we ", " our ", " my", " i "]
    keywords = ["first ", "unexplored", "novelty"]
    potentials = {}
    paragraphs = data.split("\n")
    for para in paragraphs:
        for k in keywords:
            if k in para.lower():
                potentials[para] = 0
                break

    if len(potentials) > 1:
        # we have several contribution paragraphs, need to score them

        for key in list(potentials):
            found_new = key.lower().find("new")
            found_not_new = key.lower().find("not new")
            # we remove the paragraph if the word new appears more than 2 times
            if found_new - found_not_new > 2:
                pass
                #print("Whats New: we remove the paragraph because if has <new> too many times: {}".format(key))
                #del potentials[key]

        for key in potentials:
            # remove paragraphs that have less than 2 occurrences of we our my
            we_our_my = key.lower().find(" we ") + key.lower().find(" our ") + key.lower().find(" my ")
            if we_our_my < 2:
                pass
                #print("Whats New: we remove the paragraph because if has less than 2 we our my: {}".format(key))
                #del potentials[key]

        for key in potentials:
            cap_we_i = 0
            for idx, k1 in enumerate(keywords):
                potentials[key] = potentials[key] + key.lower().count(k1) * ((idx+1) * 5)
            for k1 in keywords1:
                if cap_we_i >= 5:
                    break
                cap_we_i += key.lower().count(k1)
            if cap_we_i >= 5:
                cap_we_i = 5
            potentials[key] = potentials[key] + cap_we_i

            # lets try to normalize for paragraph length?
            if len(key):
                # potentials[key] = potentials[key] / len(key)
                pass

        for key in potentials:
            print("What's New: score {} for {}".format(potentials[key], key))

        # here the max score wins
        max_score = max(potentials.values())
        for key in potentials:
            if potentials[key] == max_score:
                article["whats_new"] = key
    elif len(potentials) == 1:
        article["whats_new"] = list(potentials.keys())[0]
    else:
        print("This is weird, no What's new paragraph encountered")
        article["whats_new"] = ""
        return

    # Now check if the paragraph we have encountered is the same as motivation or contribution
    if article["motivation"] in article["whats_new"] or article["contribution"] in article["whats_new"]:
        print("What's New we got the same as motrivation or contribution so we strip it down to one sentece")
        sentences = article["whats_new"].split(".")
        max_sentence = ""
        max_score = 0
        for sentence in sentences:
            score = 0
            for k1 in keywords:
                score = score + sentence.lower().count(k1) * 10
            for k1 in keywords1:
                score = score + sentence.lower().count(k1) * 1
            if score > max_score:
                max_score = score
                max_sentence = sentence
        print("What's New the striped sentence is: {}".format(max_sentence))
        article["whats_new"] = max_sentence

# this will be the main function: get article information and we will return the article structure
def get_article_information(file_name):
    fd = open(file_name)
    # we need another file to work with
    fd2 = open("working.txt", "w")

    # the article will be a dictionary of different chapters and things
    article = {}

    # let me get the year
    # it should be on the third line
    get_year(fd, article)

    # let us get the title:
    # it should follow the year, but it could be on multiple lines:
    # same thing with the authors
    get_title_and_auth(fd, article)

    # remove the foot_notes
    remove_junk(fd, fd2, article)
    fd = open("working.txt")

    # next is the abstract part
    get_abstract(fd, article)

    # next comes the intro. for this it could be useful to first remove all the junk
    get_intro(fd, article)
    print("The intro is:")
    print(article["intro"])

    # We can summarize, but right now we do not focus on that
    # summarize.summarize(article["intro"])

    print("Article is:", article)
    print("Abstract is ", article["abstract"])

    full_reference = ""
    for auth in article["authors"]:
        full_reference += auth
        full_reference += ", "
    full_reference += article["title"]
    full_reference += ", "
    full_reference += "The Journal of Finance, "
    full_reference += str(article["year"])

    print("Full reference is: ", full_reference)
    article["full_reference"] = full_reference

    fd.close()
    fd = open("working.txt")
    get_data(fd, article)
    # print(article["data"])
    parse_data_section(article, article["data_section"])

    print("Here are the data sources")
    for sources in article["data_source"]:
        print(sources)
    fd.close()

    # for the references I use the filename in which we have not removed the junk
    fd = open(file_name)
    get_references(fd, article)
    '''
    for ref in article["references"]:
        print(ref)
    '''
    fd.close()

    construct_reference_struct(article, article["references"])

    fd = open(file_name)
    count_references(article["ref_struct"], fd)
    compute_reference_score(article)
    print(article["top_references"])
    fd.close()

    # get the conclusion section:
    fd = open("working.txt")
    get_conclusion_section(fd, article)
    print("Here is the conclusion:")
    print(article["conclusion_section"], "\n\n")
    fd.close()

    # Start to get the sections
    # order: motivation, what's new, so what?, contribution, key findings

    # Motivation
    get_motivation(article)
    print("motivation is")
    print(article["motivation"], "\n\n")
    # we might need to strip away some sentences from this based on the other findings

    # So What?
    get_so_what(article)
    print("so what is")
    print(article["so_what"], "\n\n")

    # Contribution
    get_contributions(article)
    print("contribution is:")
    print(article["contribution"], "\n\n")

    # Whats New
    get_whats_new(article)
    print("So what's new is:")
    print(article["whats_new"], "\n\n")

    # Key Findings
    get_key_findings(article)
    print("key findings are")
    print(article["key_findings"], "\n\n")


    return article


if __name__ == "__main__":
    # the files is presumed to be located in the same dir under the name: converted.txt
    article = get_article_information("converted-2.txt")
    '''
    for ref in article["references"]:
        print(ref)
    '''
