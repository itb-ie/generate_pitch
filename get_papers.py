import re

def get_papers():
    regex = r"\b(?P<authors>(?:[^,]+, (?:[A-Z]\.?)*, )+)(?P<year>\d{4})\. (?P<title>[^\.]+)\. (?P<journal>[^,]+).*"
    regex_authors = r" ?(?P<name>[^,]+), [^,]+"
    text_references = []

    # change converted:
    fd = open("converted.txt")
    fd2 = open("converted2.txt", "w")
    for line in fd:
        if len(line) > 2:
            fd2.write("{}".format(line.replace("\n", " ")))
        else:
            fd2.write(line)
    fd.close()
    fd2.close()

    with open("converted2.txt") as fd:
        found = False
        for line in fd:

            if found:
                text_references.append(line.strip())
            if "References" in line:
                print("found the line: {}".format(line))
                found = True

    references = []
    for ref in text_references:
        info = re.finditer(regex, ref)
        for i in info:
            d = {"authors": i["authors"], "year": i["year"], "title": i["title"], "journal": i["journal"], "count": 0, "score": 0}
            # get the simple authors
            simple_auth = re.findall(regex_authors, d["authors"])
            d["simple_authors"] = simple_auth
            #print(simple_auth)
            references.append(d)

    print(references)

    # count all the reference uses:
    with open("converted2.txt") as fd:
        for line in fd:
            # for each item in references
            for ref in references:
                found = []
                # get the year
                found.append(line.count(ref["year"]))
                for auth in ref["simple_authors"]:
                    found.append(line.count(auth))
                times = min(found)
                if times > 0:
                    ref["count"] = ref["count"] + times

    # compute score:
    for ref in references:
        if int(ref["year"]) > 2010:
            ref["score"] = ref["count"]
        elif int(ref["year"]) > 2000:
            ref["score"] = ref["count"] // 2
        elif int(ref["year"]) > 1990:
            ref["score"] = ref["count"] // 3
        else:
            ref["score"] = ref["count"] // 4
    # get top 5
    count = []
    for ref in references:
        count.append(ref["score"])
    count.sort(reverse=True)
    top = count[:5]
    best_five_ref = []
    for i in range(5):
        for ref in references:
            if ref["score"] == top[i]:
                best_five_ref.append(ref)
                references.remove(ref)
                break
    print("These are the best 5 references")
    for ref in best_five_ref:
        print(ref)

    return best_five_ref[0:3]

