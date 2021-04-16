import pdfplumber
import logging

logger = logging.getLogger("pitch_generator")


def count_equations(line, eq):
    comment = f"({eq})"
    if line.endswith(comment):
        eq += 1
    return eq


def merge_lines(raw_text, get_eq=False, eq_number=0):
    # we need to link the lines and reform words split into syllables
    text = ""
    lines = raw_text.split("\n")
    for line in lines:
        # print(line)
        if not line:
            continue

        # also count the equations here
        if get_eq:
            eq_number = count_equations(line, eq_number)
        if line[0] == "\t":
            line = line[1:]
            if text:
                text = text + "\n"
        # now remove the end \n and -
        line = line.replace("\n", "")
        if line[-1] == "-":
            line = line[0:-1]
        else:
            line = line + " "
        text = text + line

    if get_eq:
        eq_number -= 1
        logger.info(f"we found {eq_number} equations")
        return text, eq_number
    else:
        return text


def extract_abstract(page, article):
    # first find the letter 'ABSTRACT' and the next ones are the abstract
    expected = 'ABSTRACT'
    poz = None

    # first get the publication year

    for idx, let in enumerate(page.chars):
        # get the last 4 chars that have the same y as the first char
        if abs(page.chars[idx]['y0'] - page.chars[0]['y0']) > 10:
            break
    year = int(page.chars[idx - 4]["text"] +
               page.chars[idx - 3]["text"] +
               page.chars[idx - 2]["text"] +
               page.chars[idx - 1]["text"]
               )
    article["publish_year"] = year
    logger.info(f"Article publication year: {article['publish_year']}")

    for idx, let in enumerate(page.chars):
        # get the next 8 and compare with expected
        sliced = page.chars[idx: idx + len(expected)]
        match = [c['text'] for c in sliced]
        match = "".join(match)
        if match == expected:
            # found it, so we need to extract the abstract
            poz = idx + len(expected)
            # logger.info(f"the position is {poz}")
            break
    if not poz:
        logger.warning("This is awkward but I did not find the ABSTRACT")
        article['abstract'] = ""
        return
    raw_abstract = page.extract_abstract(poz, x_tolerance=1.5, y_tolerance=4)
    logger.info(f"this is the raw abstract that I found\n {raw_abstract}")

    # now we just need to remove the lines and the -
    article['abstract'], article["eq_number"] = merge_lines(raw_abstract, True, 1)
    logger.info(f"this is the abstract that I found\n {article['abstract']}")


def process_first_page(page, article, fp):
    # the first page has the abstract that we need to extract:
    extract_abstract(page, article)

    text = page.extract_custom_text(x_tolerance=1, y_tolerance=4)
    # need to remove the last line because it is a page number
    lines = text.split("\n")
    article["start_page"] = int(lines[-1])
    logger.info(f"Article's first page is: {article['start_page']}")
    lines = lines[0:-1]

    text = "\n".join(lines)
    return text


def find_first_sentence(page):
    # the first sentence has more than the first letter capitalized
    logger.info(f"Trying to find first sentence on page {page}")
    idx = 0
    while idx < len(page.chars) - 1:
        end = idx + 1
        # logger.info(f"page.chars = {len(page.chars)}, idx={idx}, end={end}")
        while abs(page.chars[idx]['y0'] - page.chars[end]['y0']) < 4:
            if end == len(page.chars) - 1:
                break
            end += 1
        #logger.info(f"line between {idx} and {end}")
        sliced = page.chars[idx: end]
        line_value = [c['text'] for c in sliced]
        line_value = "".join(line_value)
        logger.info(f"line value {line_value}")
        if len(line_value) > 30:
            # set a limit to 20 uppercase characters
            if line_value[0:20].upper() == line_value[0:20] and sliced[0]['size'] > sliced[1]['size']:
                logger.info(f"found the first article line {line_value}!!")
                # now we need to make it uniform so it will not get deleted :)
                size = sliced[0]['size']
                for c in sliced:
                    c['size'] = size
                return True

        idx = end


def prepare_article(file_name, article):
    logger.info(f"Starting to convert from PDF to text")
    pdf = pdfplumber.open(file_name)

    fp = open("working.txt", "w", encoding="utf-8")
    found_first_sentence = False
    article["total_pages"] = len(pdf.pages)
    logger.info(f"Article has: {article['total_pages']} pages")
    for idx, page in enumerate(pdf.pages):
        logger.info(f" page {idx}")

        # there is this annoying thing that the first main sentence of the article can have more than the first
        # letter capitalized
        if not found_first_sentence and idx < 3:
            # try to find the first sentence
            if find_first_sentence(page):
                found_first_sentence = True
        if not idx:
            # first page is different because of abstract and intro
            text = process_first_page(page, article, fp)
        else:
            text = page.extract_custom_text(x_tolerance=1, y_tolerance=4)
            # need to remove the first line
            lines = text.split("\n")
            lines = lines[1:]
            text = "\n".join(lines)
        text = text.replace("ﬁ", "fi")
        text = text.replace("´ ", "´")
        fp.write(text)
        fp.write("\n")
        # a debug break to just do one page
        # break
    # print(f"There were {foot_notes-1} comments")
    pdf.close()
    fp.close()

    # now we need to convert it into continuous paragraphs rather than lines.
    fp = open("working.txt", "r", encoding="utf-8")
    fp2 = open("converted.txt", "w", encoding="utf-8")
    raw_text = fp.read()
    converted_text, article["eq_number"] = merge_lines(raw_text, True,
                                                       article["eq_number"] if article["eq_number"] else 1)
    fp2.write(converted_text)
    fp.close()
    fp2.close()


if __name__ == "__main__":
    # article will be a dictionary data structure with all the info that we need
    article = {}
    # prepare_article("C:/personal projects/robert pitch/Anderson_JF_2018.pdf", article)
    # prepare_article("C:/personal projects/robert pitch/Short-Selling Risk JF (005).pdf", article)
    prepare_article(
        "C:/personal projects/robert pitch/Social Capital, Trust, and Firm Performance- The Value of Corporate Social Responsibility during the Financial Cris",
        article)
    exit()


def count_comments(fp):
    idx = 1
    for line in fp:
        comment = f"{idx} "
        if line.startswith(comment):
            idx += 1
    print(f"There are {idx - 1} comments")
