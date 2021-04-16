# in this file we attempt to answer the Research Question part of the pitch
import nltk
import logging

logger = logging.getLogger("pitch_generator")


def get_research_question(article):
    logger.info(f"\nTrying to get the research question")
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

    # limit the search
    if len(article["intro"]) > 3:
        intro = article["intro"][0:3]
    else:
        intro = article["intro"]

    data = [article["abstract"]] + intro + [conclusion[0]]
    # 3 - Search for reseach question
    keywords = ["research question"]  # it is a list because maybe we need to add more
    for key in keywords:
        for para in data:
            sentences = nltk.sent_tokenize(para)
            for sentence in sentences:
                if key in sentence.lower():
                    # we found the research question. easiest case
                    article["answer_research_question"] = sentence
                    return

    # we got here, so 3 didn't work
    # try to search for another set of terms
    keywords = ["question"]  # it is a list because maybe we need to add more
    ignore_keywords = ["begs the question"]
    for key in keywords:
        for para in data:
            sentences = nltk.sent_tokenize(para)
            for idx, sentence in enumerate(sentences):
                if key in sentence.lower():
                    good = True
                    for ignore_key in ignore_keywords:
                        if ignore_key in sentence.lower():
                            # not a good one, so we skip
                            good = False
                            break
                    if good:
                        # question 4 is True, so check if a or b
                        num_words = len(sentence.split())
                        if num_words < 16:
                            # we need the previous sentence as well
                            if idx > 0:
                                logger.info(f"RQ: We found question, too short so we get the previous one")
                                article["answer_research_question"] = sentences[idx-1] + " " + sentence
                            else:
                                logger.info(f"RQ: We found question, too short but we are first in paragraph!")
                                article["answer_research_question"] = sentence
                        else:
                            logger.info(f"RQ: We found question, not too short so we get it!")
                            article["answer_research_question"] = sentence
                        return

    # 4 failed so we move to 5, search only in abstract :)
    keywords = ["we study", "in this paper", "in this study"]
    sentences = nltk.sent_tokenize(article["abstract"])
    for sentence in sentences:
        for key in keywords:
            if key in sentence.lower():
                # we found the sentence: 5 is True
                logger.info(f"RQ: Case 5 is True, we found in abstract")
                article["answer_research_question"] = sentence
                return

    # 5 failed so we move to 6 and onwards. search in entire data
    keywords = ["we study", "in this paper", "in this study"]
    ignore_keywords = ["we present", "first evidence", "we show", "we find"]
    for para in data:
        sentences = nltk.sent_tokenize(para)
        for idx, sentence in enumerate(sentences):
            for key in keywords:
                if key in sentence.lower():
                    # could be a sentence
                    good = True
                    for ignore_key in ignore_keywords:
                        if ignore_key in sentence.lower():
                            good = False
                            break
                    if not good:
                        # not a good sentence, break to get the next sentence
                        break
                    # we got here so the sentence could be good, check length
                    num_words = len(sentence.split())
                    if num_words > 15:
                        # we are good
                        logger.info(f"RQ: Case 6, I found a more than 15 words sentence that is good")
                        article["answer_research_question"] = sentence
                        return
                    # we are not 15 words, so get previous and after sentence, if possible
                    answer = sentence + "."
                    logger.info(f"RQ: Case 6, I found a less than 15 words sentence, need to look before and after")
                    if idx > 0:
                        prev_sentence = sentences[idx-1]
                        good = True
                        for ignore_key in ignore_keywords:
                            if ignore_key in prev_sentence.lower():
                                good = False
                                break
                        if good:
                            logger.info(f"RQ: Case 6, prev sentence is also good")
                            answer = prev_sentence + " " +  answer
                    if idx < len(sentences) - 1:
                        next_sentence = sentences[idx+1]
                        good = True
                        for ignore_key in ignore_keywords:
                            if ignore_key in next_sentence.lower():
                                good = False
                                break
                        if good:
                            logger.info(f"RQ: Case 6, next sentence is also good")
                            answer = answer + " " + next_sentence
                    if len(answer.split()) > 15:
                        logger.info(f"RQ: Case 6, after add prev and next we are good")
                        article["answer_research_question"] = answer
                        return

    logger.info("RQ: We got to case 7 that we need to figure out")
    article["answer_research_question"] = ""