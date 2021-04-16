# in this file we attempt to answer the motivation part of the pitch
import logging

logger = logging.getLogger("pitch_generator")


def get_first_paragraph(article):
    data = article["intro"]
    for para in data:
        if para[0] != '"' and para[0] != '“' and para[0] != '”' and \
                para[-1] != '"' and para[-1] != '“' and para[-1] != '”' and \
                len(para) > 200:
            return para


def get_motivation(article):
    # only look into intro
    data = article["intro"]
    keywords = ["important", "importance"]
    score = {"important": 3, "importance": 3, "objective": 3, "results": -3, "find": -3, "we": -1, "our": -1}
    potentials = {}
    for para in data:
        for keyword in keywords:
            if keyword in para.lower():
                potentials[para] = 0

    # no potential we always get the first paragraph:
    if not potentials:
        logger.info("No potential, so get the first paragraph in the intro")
        article["answer_motivation"] = get_first_paragraph(article)
        return

    # if we are here it means we have some potentials
    for potential in potentials:
        # let us score it
        for key in score:
            potentials[potential] += potential.lower().count(key) * score[key]

        # lets try to normalize for paragraph length?
        if len(key):
            # potentials[potential] /= len(potential)
            pass

    for potential in potentials:
        logger.info(f"Get Motivation: score {potentials[potential]} for {potential}")

    # the max score wins
    max_score = max(potentials.values())
    if max_score < 0:
        article["answer_motivation"] = get_first_paragraph(article)
    else:
        for potential in potentials:
            if potentials[potential] == max_score:
                article["answer_motivation"] = potential
