# in this file we attempt to answer the Tools part of the pitch
import pdfplumber
import re
import logging

logger = logging.getLogger("pitch_generator")


def get_tables(file_name, article):
    logger.info(f"Extracting tables")
    pdf = pdfplumber.open(file_name)
    article["num_pages"] = len(pdf.pages)

    for idx, page in enumerate(pdf.pages):
        text = page.extract_table_text(x_tolerance=1, y_tolerance=4)

        if not text:
            continue
        text = text.replace("ﬁ", "fi")
        text = text.replace("´ ", "´")

        # we have the table text:
        lines = text.split("\n")
        lines[0] = lines[0].lstrip()

        if len(lines) < 2:
            logger.warning(f"This could be a continuation table on page {idx + 1}")
            continue

        article["tables"][lines[0]] = {}
        title = lines[1].lstrip()
        content = ""
        for line in lines[2:]:
            content = content + line
            if line[-1] == "-":
                content = content[:-1]
            else:
                content = content + " "
        article["tables"][lines[0]]["title"] = title
        article["tables"][lines[0]]["page"] = idx + 1
        article["tables"][lines[0]]["content"] = content

        logger.info(f"Found a table on page {idx + 1}")

    pdf.close()
    return


def elim_tables(article):
    keywords = ["descriptive statistics", "summary statistics"]
    for table in list(article["tables"]):
        for key in keywords:
            if key in article["tables"][table]["title"].lower():
                logger.info(f"Tools section: Eliminating table titled: {article['tables'][table]['title']}")
                del article["tables"][table]
                break


def find_first_table_mentioned(section, article):
    reg_ex = r"Table [IVXL]{1,4}\b"
    for para in section:
        if res := re.findall(reg_ex, para):
            # now maybe this is one of the tables we have removed. so let's see if we st ill have it
            if res[0] in article["tables"]:
                return res[0]
    # this means we could not find any mention of a table:
    logger.warning(f"This is weird, but no table is mentioned in section/paragraph: {section}")
    return None


def format_table_narative(table):
    # the filed is called "content"
    text = ""
    replace_action = ["presents", "investigates", "reports", "examines", "contains"] # do we need more? add here
    for key in replace_action:
        if (pos := table["content"].find(key)) > 0:
            # remove the first part
            text = table["content"][pos + len(key):]
            break
    # add the beginning:
    text = "This article investigates" + text

    # replace panels
    letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I"] # should be enough
    for let in letters:
        expr = f"In Panel {let}"
        text = text.replace(expr, "Also")
        expr = f"Panel {let}"
        text = text.replace(expr, "Also")

    # remove end sentences:
    sentences = text.split(".")
    keywords = ["*", "t-stat", "parentheses", "statistical", "significance"] # these are the keywords
    for sentence in reversed(sentences): # need to iterate backwards because we are removing from the list
        for key in keywords:
            if key in sentence.lower():
                sentences.remove(sentence)
                logger.info(f"Removing sentence: {sentence}")
                break
    return ".".join(sentences)


def get_key_table_text(article):
    # step 4 in the tools algorithm: find the main section in the paper
    keywords = ["results", "findings", "evidence"]
    for section in article["sections"]:
        for key in keywords:
            if key in section["name"].lower():
                logger.info(f"Found the main section {section}")
                # identify the first table mentioned
                table_name = find_first_table_mentioned(section["text"], article)
                if not table_name:
                    logger.warning("Tools: There is no table mentioned in the main section!!")
                    return ""
                logger.info(f"The first mentioned table is {table_name}")
                # let's format the table narative
                text = format_table_narative(article["tables"][table_name])
                logger.info(f"Formated table narative: {text}")
                return text

    # if we got here it means that there is no main section so we move to step 5 of the algorithm: find baseline
    logger.info("Tools: I could not find any main section, searching for baseline keyword")
    keywords = ["baseline"] # maybe we need more?
    for section in article["sections"]:
        for para in section["text"]:
            for key in keywords:
                if key in para.lower():
                    logger.info(f"Tools: Found the baseline paragraph")
                    table_name = find_first_table_mentioned([para], article)
                    if not table_name:
                        # we need to get the paragraph as it is
                        logger.info("Could not find any table mentioned, so we just return the paragraph")
                        return para

                    # we have a table_name so we need to format the narrative
                    logger.info(f"The first mentioned table is {table_name}")
                    text = format_table_narative(article["tables"][table_name])
                    logger.info(f"Formated table narative: {text}")
                    return text

    # if we got here it means that there is no main section and there is no baseline paragraph, so just return the first table narative that is still left!
    logger.info(f"Tools: No main section and no 'baseline' paragraph, so just get the first table narative")
    for table in article["tables"]:
        text = format_table_narative(article["tables"][table])
        logger.info(f"Formated table narative: {text}")
        return text
    return ""


def get_key_methods(article):
    keywords = [
        "identification",
        "causality",
        "reverse causality",
        "omitted variable bias",
        "omitted variables",
        "measurement error",
        "exogenous shock",
        "natural experiment",
        "difference in difference",
        "difference - in -difference",
        "PSM",
        "propensity score matching",
        "self selection",
        "regression discontinuity design",
        "RDD",
        "channel",
        "mechanism"
        ]
    found_keywords = set()
    for section in article["sections"]:
        for para in section["text"]:
            for key in keywords:
                if key in para.lower():
                    found_keywords.add(key)
    return found_keywords


def get_tools(filename, article):
    # we need the filename because the tables have a different fontsize and are treated like junk
    # so need to get them here and work with them

    article["tables"] = {}
    get_tables(filename, article)
    for table in article["tables"]:
        print(article["tables"][table])

    # we found the tables, let's eliminate the irrelevant ones as per item 3 in the Tools algorithm
    elim_tables(article)

    # find key table
    key_table_text = get_key_table_text(article)
    if not key_table_text:
        logger.warning(f"This article has no key table!")

    # find the key methods:
    key_methods = get_key_methods(article)
    if key_methods:
        logger.info(f"Tools: the methods that I found: {key_methods}")
    else:
        logger.info(f"Tools: I could not find any contemporary methods!")
    if key_methods:
        methods_text = "Contemporary methods used/ issues addressed in this article include: "
        key_methods = list(key_methods)
        for method in key_methods:
            if method != key_methods[-1]:
                methods_text += method + ", "
            else:
                methods_text = methods_text + "and " + method + "."
    else:
        methods_text = ""

    # Now we put it all together:
    tools = ""
    if article["eq_number"] > 20:
        tools += "This paper has many equations. As such, it seems that this study has a major focus on theory development and/or analytical modelling.\n"

    tools += key_table_text + "\n"
    tools += methods_text
    logger.info(f"Tools -  Final result: {tools}")
    article["answer_tools"] = tools
