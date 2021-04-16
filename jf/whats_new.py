# in this file we attempt to answer the What's New part of the pitch
import logging

logger = logging.getLogger("pitch_generator")


def get_whats_new(article):
    # only look in the intro
    data = article["intro"]
    keywords = ["first ", "unexplored", "novelty"]
    score = {
        "first": 5,
        "unexplored": 10,
        "novelty": 15,
        "we ": 1,
        "our ": 1,
        "my ": 1,
        "i ": 1
        }
    potentials = {}
    for para in data:
        for k in keywords:
            if k in para.lower():
                potentials[para] = 0
                break

    if not potentials:
        logger.warning("This is weird, no What's new paragraph encountered")
        article["answer_whats_new"] = ""
        return

    # we decided that this part will not be included!!
    '''
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
    '''

    for potential in potentials:
        cap_we_i = 0
        for key in score:
            # this is a special case in which we cap the score for 1 point items like i, we, our, my
            if score[key] == 1:
                cap_we_i += potential.lower().count(key)
            else:
                potentials[potential] += potential.lower().count(key) * score[key]
        if cap_we_i >= 5:
            cap_we_i = 5
        potentials[potential] += cap_we_i

        # lets try to normalize for paragraph length?
        if len(key):
            # potentials[key] = potentials[key] / len(key)
            pass

    for potential in potentials:
        logger.info(f"What's New: score {potentials[potential]} for: {potential}")

    # here the max score wins
    max_score = max(potentials.values())
    for potential in potentials:
        if potentials[potential] == max_score:
            article["answer_whats_new"] = potential

    # Now check if the paragraph we have encountered is the same as motivation or contribution
    if article["answer_motivation"] in article["answer_whats_new"] or article["answer_contribution"] in article["answer_whats_new"]:
        logger.info("What's New we got the same as motivation or contribution so we strip it down to one sentence")
        sentences = article["answer_whats_new"].split(".")
        max_sentence = ""
        max_score = 0
        for sentence in sentences:
            sentence_score = 0
            for key in score:
                sentence_score += sentence.lower().count(key) * score[key]
            if sentence_score > max_score:
                max_score = sentence_score
                max_sentence = sentence
        logger.info(f"What's New the striped sentence is: {max_sentence}")
        article["answer_whats_new"] = max_sentence
