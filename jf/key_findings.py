# in this file we attempt to answer the Key Findings part of the pitch
import logging

logger = logging.getLogger("pitch_generator")


def get_key_findings(article):
    logger.info(f"\nTrying to get the key findings")
    # special case here: add 5 points for the first paragraph in the conclusion section
    # get the conclusion section
    found = False
    data = None
    conclusion = None
    for sec in article["sections"]:
        if sec["name"] == "conclusion":
            conclusion = sec["text"]
            found = True
            break
    if not found:
        logger.warning("There is no conclusion section!!")
        article["answer_key_findings"] = ""
        return

    data = article["intro"] + conclusion
    keywords = ["result", "find"]
    score = {
        "result": 3,
        "find": 3,
        "evidence": 3,
        "we ": 1,
        "our ": 1
        }
    potentials = {}
    for para in data:
        # eliminate the contribution paragraph
        if para == article["answer_contribution"]:
            logger.info("Key Findings: We eliminate the contribution paragraph!")
            continue

        # remove collectively
        position = para.lower().find("collectively")
        if position >= 0:
            para = para[0:position]
        for key in keywords:
            if key in para.lower():
                potentials[para] = 0
                # check if this is the first paragraph in the conclusion, so we need to add 5 points to it:
                if para == conclusion[0]:
                    logger.info("We found the first para in the conclusion, so we add 5 points")
                    potentials[para] = 5
                break

    if not potentials:
        logger.warning("This is weird, but I did not find any potential Key Findings")
        article["answer_key_findings"] = ""
        return

    # we have several contribution paragraphs, need to score them

    for potential in potentials:
        for key in score:
            potentials[potential] += potential.lower().count(key) * score[key]

        # lets try to normalize for paragraph length?
        if len(key):
            #potentials[key] = 10000 * potentials[key] // len(key)
            pass

    for potential in potentials:
        logger.info(f"Key Findings score {potentials[potential]} for: {potential}")

    max_score = max(potentials.values())
    for potential in potentials:
        if potentials[potential] == max_score:
            article["answer_key_findings"] = potential
