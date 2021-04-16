# in this file we attempt to answer the Idea part of the pitch
import nltk
import logging

logger = logging.getLogger("pitch_generator")


def get_idea(article):
    logger.info(f"\nTrying to get the idea")
    # 1 search for a hypoth section
    logger.info(f"Idea: Step 1&2: searching for hypothesis section or subsection ")
    keywords = ["hypoth"] # add more keywords here if needed
    max_score = 0
    para = None
    data = None
    for section in article["sections"]:
        found_subsection = False
        for key in keywords:
            if key in section["name"].lower():
                # found it in the section name
                data = section["text"]
                break
            else:
                for subsection in section["sub_sections"]:
                    if key in subsection["name"].lower():
                        # found it in the subsection
                        found_subsection = True
                        data = subsection["text"]
                        break
                if found_subsection:
                    break

        if data:
            # We found it here
            logger.info("Idea: We found a matching section or subsection, extracting relevant paragraph")
            para_result = None
            for para in data:
                score = 0
                for key in keywords:
                    score = score + para.lower().count(key)
                if score > max_score:
                    max_score = score
                    para_result = para
    if max_score:
        logger.info(f"Idea: We found the best paragraph: {para_result}")
        article["answer_idea"] = para_result
        return

    # if we got here it means that step 1 failed
    keywords = ["hypoth", "predict %40 that"]  # this is how you define a term followed by another term!
    preceding_keywords = ["in such"]  # maybe we want to add more keywords here
    logger.info(f"Idea: Step 1&2 Failed, go to Step 3: Search generally")
    potentials = []
    for section in article["sections"]:
        for para in section["text"]:
            sentences = nltk.sent_tokenize(para)
            for idx, sentence in enumerate(sentences):
                for key in keywords:
                    if "%" in key:
                        # complicated search of one term followed by another
                        first_term = key[0:key.find("%")].rstrip()
                        #print(f"first term is: {first_term}")
                        key = key[key.find("%")+1:]
                        distance = int(key[0:key.find(" ")])
                        #print(f"Distance is {distance}")
                        second_term = key[key.find(" ")+1:]
                        #print(f"second term is: {second_term}")
                        if first_term in sentence.lower():
                            start = sentence.lower().find(first_term)
                            if start + distance + len(second_term) > len(sentence):
                                search_in = sentence[start:]
                            else:
                                search_in = sentence[start: start+distance+len(second_term)]
                            if second_term in search_in.lower():
                                if not potentials:
                                    para_result = para
                                logger.info(f"Idea: complicated search: {sentence} is a potential sentence")

                                # Final check, Step 5b:
                                for preceding in preceding_keywords:
                                    if preceding in sentence.lower():
                                        logger.info(f"Idea: found {preceding} so need to get the previous sentence from the paragraph")
                                        if idx > 0:
                                            sentence = sentences[idx-1] + sentence
                                potentials.append(sentence)
                    else:
                        # simple search
                        if key in sentence.lower():
                            if not potentials:
                                para_result = para
                            logger.info(f"Idea: {sentence} is a potential sentence")
                            # Final check, Step 5b:
                            for preceding in preceding_keywords:
                                if preceding in sentence.lower():
                                    logger.info(f"Idea: found {preceding} so need to get the previous sentence from the paragraph")
                                    if idx > 0:
                                        sentence = sentences[idx - 1] + sentence
                            potentials.append(sentence)

    if len(potentials) == 1:
        logger.info("Idea: found just one sentence, so extract entire paragraph")
        article["answer_idea"] = para_result
        return
    elif len(potentials) > 1:
        logger.info("Idea: found more than one potential sentences")
        result = "\n".join(potentials)
        article["answer_idea"] = result
        return

    # all else failed, Step 6
    result = "The central hypothesis of this paper is (likely) very closely related to the identified research question: " + article["answer_research_question"]
    article["answer_idea"] = result
