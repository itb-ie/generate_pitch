import heapq
import re
import nltk

nltk.download('punkt')
nltk.download('stopwords')

def summarize(text, top=7, para=False):
    # Removing Square Brackets and Extra Spaces
    article_text = re.sub(r'\[[0-9]*\]', ' ', text)
    article_text = re.sub(r'\s+', ' ', article_text)

    # Removing special characters and digits
    formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text )
    formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)

    max_sentence_len = 30
    if para:
        sentence_list = text.split("ENDPARA")
        max_sentence_len = 10000
    else:
        sentence_list = nltk.sent_tokenize(article_text)

    stopwords = nltk.corpus.stopwords.words('english')
    #print(stopwords)

    word_frequencies = {}
    for word in nltk.word_tokenize(formatted_article_text):
        if word not in stopwords:
            if word not in word_frequencies.keys():
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1

    maximum_frequency = max(word_frequencies.values())

    for word in word_frequencies.keys():
        word_frequencies[word] = (word_frequencies[word]/maximum_frequency)

    sentence_scores = {}
    for sent in sentence_list:
        for word in nltk.word_tokenize(sent.lower()):
            if word in word_frequencies.keys():
                if len(sent.split(' ')) < max_sentence_len:
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word]
                    else:
                        sentence_scores[sent] += word_frequencies[word]

    summary_sentences = heapq.nlargest(top, sentence_scores, key=sentence_scores.get)

    summary = ' '.join(summary_sentences)
    #print(summary)
    # for sent in summary_sentences:
    #     print(sent)
    return summary_sentences

if __name__ == "__main__":
    summary = summarize("So, keep working. Keep striving. Never give up. Fall down seven times, get up eight. Ease is a greater threat to progress than hardship. So, keep moving, keep growing, keep learning. See you at work.", 3)
    print(summary)