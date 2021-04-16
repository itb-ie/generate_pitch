import os, sys
from jf import pdf_conversion
from jf import references
from jf import elements
from jf import data
from jf import motivation
from jf import so_what
from jf import contribution
from jf import whats_new
from jf import key_findings
from jf import tools
from jf import research_question
from jf import idea
import logging

logger = logging.getLogger("pitch_generator")


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# this will be the main function: get article information and we will return the article structure
def get_article_information(file_name):
    article = {}
    pdf_conversion.prepare_article(file_name, article)

    fd = open("working.txt", encoding="utf-8")
    elements.get_title_and_auth(fd, article)
    logger.info(f"title is: {article['title']}")
    logger.info(f"short title is: {article['short_title']}")
    logger.info(f"authors are: {article['authors']}")
    fd.close()

    # get the intro part
    fd = open("converted.txt", encoding="utf-8")
    elements.get_intro(fd, article)
    fd.close()
    logger.info(f"The intro is: {article['intro']}")

    # get the sections
    fd = open("converted.txt", encoding="utf-8")
    elements.get_sections(fd, article)
    fd.close()

    # now get the references
    references.get_references(file_name, article)
    references.construct_reference_struct(article)
    references.count_references(article["ref_struct"])
    references.compute_reference_score(article)
    print(article["top_references"])

    article["full_reference"] = ", ".join(article["authors"]) + ", " + article[
        "title"] + ", The Journal of Finance, " + str(article["publish_year"]) + f", pages: {article['start_page']} to {article['start_page'] + article['total_pages'] -1} "

    # get the data
    data.get_data(article)
    logger.info(f"here is the data results: {article['answer_data']}")

    # get the motivation
    motivation.get_motivation(article)
    logger.info(f"here is the motivation section: {article['answer_motivation']}")

    # get the So What?
    so_what.get_so_what(article)
    logger.info(f"here is the so_what section: {article['answer_so_what']}")

    # get the contribution
    contribution.get_contribution(article)
    logger.info(f"here is the contribution section: {article['answer_contribution']}")

    # get the What's New
    whats_new.get_whats_new(article)
    logger.info(f"here is the whats_new section: {article['answer_whats_new']}")

    # Key Findings
    key_findings.get_key_findings(article)
    logger.info(f"here are the key findings: {article['answer_key_findings']}")

    # Tools
    tools.get_tools(file_name, article)
    logger.info(f"here is the tools section: {article['answer_tools']}")

    # Research Question
    research_question.get_research_question(article)
    logger.info(f"here is the research question: {article['answer_research_question']}")

    # Idea
    idea.get_idea(article)
    logger.info(f"here is the idea: {article['answer_idea']}")

    return article


if __name__ == "__main__":
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger("pitch_generator")
    logger.setLevel(logging.INFO)

    article = {}
    filename = "C:/personal projects/robert pitch/Anderson_JF_2018.pdf"
    #filename = "C:/personal projects/robert pitch/Short-Selling Risk JF (005).pdf"
    #filename = "C:/personal projects/robert pitch/Social Capital, Trust, and Firm Performance- The Value of Corporate Social Responsibility during the Financial Cris"

    # this is just to test faster
    get_article_information(filename)

    pdf_conversion.prepare_article(filename, article)

    fd = open("working.txt", encoding="utf-8")
    elements.get_title_and_auth(fd, article)
    logger.info(f"{article['title']}")
    logger.info(f"{article['short_title']}")
    logger.info(f"{article['authors']}")
    fd.close()

    # get the intro part
    fd = open("converted.txt", encoding="utf-8")
    elements.get_intro(fd, article)
    fd.close()
    logger.info("The intro is:")
    for para in article["intro"]:
        logger.info(f"{para}")

    # get the sections
    fd = open("converted.txt", encoding="utf-8")
    elements.get_sections(fd, article)
    fd.close()

    # now get the references
    references.get_references(filename, article)
    references.construct_reference_struct(article)
    references.count_references(article["ref_struct"])
    references.compute_reference_score(article)
    print(article["top_references"])

    # get the data
    data.get_data(article)
    logger.info(f"here is the data results: {article['answer_data']}")

    # get the motivation
    motivation.get_motivation(article)
    logger.info(f"here is the motivation section: {article['answer_motivation']}")

    # get the So What?
    so_what.get_so_what(article)
    logger.info(f"here is the so_what section: {article['answer_so_what']}")

    # get the contribution
    contribution.get_contribution(article)
    logger.info(f"here is the contribution section: {article['answer_contribution']}")

    # get the What's New
    whats_new.get_whats_new(article)
    logger.info(f"here is the whats_new section: {article['answer_whats_new']}")

    # Key Findings
    key_findings.get_key_findings(article)
    logger.info(f"here are the key findings: {article['answer_key_findings']}")

    # Tools
    tools.get_tools(filename, article)
    logger.info(f"here is the tools section: {article['answer_tools']}")
    
    # Research Question
    research_question.get_research_question(article)
    logger.info(f"here is the research question: {article['answer_research_question']}")
    
    # Idea
    idea.get_idea(article)
    logger.info(f"here is the idea: {article['answer_idea']}")
