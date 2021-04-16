# in this file we attempt to answer the So What? part of the pitch
import logging

logger = logging.getLogger("pitch_generator")


def get_so_what(article):
    # get the conclusion section
    found = False
    for sec in article["sections"]:
        if sec["name"] == "conclusion":
            data = article["intro"] + sec["text"]
            found = True
            break
    if not found:
        logger.warning("There is no conclusion section!!")
    keywords = ["collectively", "overall", "import", "signif", "economically"]

    score = {"collectively": 7, "overall": 7, "import": 3, "signif": 3, "economically": 3, "we ": 1, "our ": 1, "i ": 1, "my ": 1}
    potentials = {}
    for para in data:
        if para == article["answer_motivation"]:
            logger.info("Inside so_what: skipping the motivation part")
            continue
        # only keep collectively
        position = para.lower().find("collectively")
        if position >= 0:
            para = para[position:]
            potentials[para] = 0
        else:
            for k in keywords:
                if k in para.lower():
                    potentials[para] = 0
                    break

    if not potentials:
        logger.warning("We could not find any matches for the So What question")
        article["answer_so_what"] = ""
        return


    # we have several contribution paragraphs, need to score them
    for potential in potentials:
        # let us score it according to the score dictionary that we have defined
        for key in score:
            potentials[potential] += potential.lower().count(key) * score[key]

        # Extra rule: "one standard deviation" in the same sentence, gets 20 points
        sentences = potential.lower().split(".")
        for s in sentences:
            if "one" in s and "standard" in s and "deviation" in s:
                potentials[potential] += 20

        # lets try to normalize for paragraph length?
        if len(key):
            #potentials[potential] = 10000 * potentials[potential] // len(potential)
            pass

    for potential in potentials:
        logger.info(f"So what score {potentials[potential]} for: {potential}")

    max_score = max(potentials.values())
    for potential in potentials:
        if potentials[potential] == max_score:
            article["answer_so_what"] = potential


