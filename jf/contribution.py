# in this file we attempt to answer the Contribution part of the pitch
import logging

logger = logging.getLogger("pitch_generator")


def get_contribution(article):
    logger.info(f"\nTrying to get the contribution")
    # get the conclusion section
    found = False
    data = None
    for sec in article["sections"]:
        if sec["name"] == "conclusion":
            data = article["intro"] + sec["text"]
            found = True
            break
    if not found:
        logger.warning("There is no conclusion section!!")
        article["answer_contribution"] = ""
        return

    keywords = ["contribution"]
    score = {
        "contribution": 10,
        "our study": 3,
        "our analysis": 3,
        "our paper": 3,
        "our findings": 3,
        "we find": 3,
        "we study": 3,
        "we analyze": 3,
        "this paper": 3,
        "this study": 3,
        "our ": 1,
        "we ": 1,
        "i " : 1
        }
    potentials = {}
    eliminated_so_what = False
    for para in data:
        # eliminate the paragraph if it is the same as the so what paragraph
        if para == article["answer_so_what"]:
            logger.info("Inside get_contribution: skipping so_what paragraph")
            eliminated_so_what = True
            continue
        for k in keywords:
            if k in para.lower():
                potentials[para] = 0

    if not potentials:
        logger.warning(f'Get_contribution: This is bad: we could not find any paragraph with the word {keywords}')
        if eliminated_so_what:
            logger.warning("it is because we have eliminated the so what para, we put it back in")
            article["answer_contribution"] = article["answer_so_what"]
        else:
            article["answer_contribution"] = ""
        return

    # we have several contribution paragraphs, need to score them
    for potential in potentials:
        # let us score it according to the score dictionary that we have defined
        for key in score:
            potentials[potential] += potential.lower().count(key) * score[key]

    for potential in potentials:
        logger.info(f"Contribution: score {potentials[potential]} for: {potential}")

    max_score = max(potentials.values())
    for potential in potentials:
        if potentials[potential] == max_score:
            article["answer_contribution"] = potential
