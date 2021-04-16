# this file handles the data section and tries to answer the question: what is the data used in the article
import nltk
import logging
import summarize

logger = logging.getLogger("pitch_generator")

def get_databases(article):
    databases = [
        "American Religion Data Archive",
        "Audit Analytics"
        "BoardEx",
        "Bloomberg",
        "Capital IQ",
        "Compustat",
        "CRSP",
        "CNRDS",
        "CSMAR",
        "Datastream",
        "EDGAR",
        "ExecuComp",
        "Eventus",
        "Ken French Data Library",
        "Federal Reserve Bank Holding Company Database",
        "Fin Analysis",
        "Fitch – Bank Fundamentals Database",
        "Hou-Xue-Zhang",
        "IBES",
        "IBISWorld",
        "Institutional Shareholders Services",
        "Loan Pricing Corporation Deal Scan",
        "Morning Star Direct",
        "MSCI",
        "Option Metrics",
        "Pastor-Stambaugh liquidity factor",
        "RESSET Financial Research Database",
        "Riskmetrics",
        "RoZetta",
        "SIRCA",
        "SEC Edgar",
        "Stanford Law School Securities Class Action Clearinghouse",
        "SDC",
        "SNL Financial",
        "Thomson Reuters Institutional Holdings",
        "Trade and Quote",
        "World Bank Global Financial Development Database",
        "Wind"
    ]
    results = set()
    for key in databases:
        for sec in article["sections"]:
            for para in sec["text"]:
                if key.lower() in para.lower():
                    results.add(key)
    return results


def find_keywords_in_sections_and_return_data(sections, keywords):
    data = []
    for sec in sections:
        for key in keywords:
            if key in sec["name"].lower():
                # found the section name
                # what if there are more sections???
                if data:
                    logger.warning(f"Problem!! There are more than one sections that have {keywords} in their name!!!")
                data = sec["text"]
    # what if we did not find in the section name? Search in sub_section
    if not data:
        for key in keywords:
            for sec in sections:
                for sub_sec in sec["sub_sections"]:
                    if key in sub_sec["name"].lower():
                        # found the sub_section name
                        # what if there are more sub_sections???
                        if data:
                            logger.warning(
                                f"Problem!! There are more than one sub_sections that have {keywords} in their name!!!")
                        data = sub_sec["text"]

        # what if we did not find in the sub_section name? Searchin subsub_section
        if not data:
            for key in keywords:
                for sec in sections:
                    for sub_sec in sec["sub_sections"]:
                        for subsub_sec in sub_sec["subsub_sections"]:
                            if key in subsub_sec["name"].lower():
                                # found the subsub_section name
                                # what if there are more subsub_sections???
                                if data:
                                    logger.warning(
                                        f"Problem!! There are more than one subsub_sections that have {keywords} in their name!!!")
                                data += subsub_sec["text"]
    return data

def get_data(article):
    logger.info(f"\nTrying to get the data")
    # this is the revised algorithm

    # exclude introduction and conclusion section
    # only consider sections that end before the first half of the article
    total_letters = 0
    for sec in article["sections"]:
        section_letters = sum([len(para) for para in sec["text"]])
        total_letters += section_letters
    sections = article["sections"].copy()
    current_letters = 0
    for idx, sec in enumerate(sections):
        section_letters = sum([len(para) for para in sec["text"]])
        current_letters += section_letters
        if current_letters > total_letters // 2:
            # we are past the half point of the article
            sections = sections[:idx+1]

    # Step3: search for keyword in sections, subsections, subsubsections
    # first search in sections
    step = 3
    keywords = ["data"]
    logger.info(f"Step3: try to get the section/subsection that contain {keywords}")
    data = find_keywords_in_sections_and_return_data(sections, keywords)
    if not data:
        step = 4
        keywords = ["sample", "sampling"]
        logger.info(f"Step4: try to get the section/subsection that contain {keywords}")
        data = find_keywords_in_sections_and_return_data(sections, keywords)
    if not data:
        # Step 5
        step = 5
        keywords = ["simulation", "simulate"]
        logger.info(f"Step5: Search for keywords {keywords} in the article and extract paragraphs")
        for key in keywords:
            for sec in sections:
                for para in sec["text"]:
                    if key in para.lower() and para not in data:
                        data.append(para)
    if not data:
        step = 6
        keywords = ["data", "database"]
        logger.info(f"Step6: Search for keywords {keywords} in the article and extract paragraphs")
        for key in keywords:
            for sec in sections:
                for para in sec["text"]:
                    if key in para.lower() and para not in data:
                        data.append(para)

    # If we have data it means it was found in the section, sub_section or subsub_section
    if data:
        logger.info(f"We summarized the data found previously on step {step}")
        #   Robert: summarization and top x sentences
        #   Bogdan: Get the most significant paragraph
        text = "".join(data)
        if step == 3:
            top = 5
        elif len(text.split(".")) > 5:
            top = 3
        else:
            top = 2
        summarized = ["Robert style summarization\n"] + summarize.summarize(text, top)
        logger.info(f" Summarization Robert result: {summarized}")
        text = "ENDPARA".join(data)
        summarized2 = ["Bogdan style summarization\n"] + summarize.summarize(text, 1, para=True)
        logger.info(f" Summarization Bogdan result: {summarized2}")
        logger.info(f"Move to step 7")

    # Step 7
    result = get_databases(article)
    datasources = f"Data sources in this article include: {';'.join(result)}"
    if data:
        article["answer_data"] = summarized + summarized2 + [datasources]
    else:
        article["answer_data"] = [datasources]
    return
