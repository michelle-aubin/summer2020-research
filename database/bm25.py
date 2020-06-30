import sqlite3
import math
from constants import BM25_B, BM25_K1, BM25_delta


# Returns BM25 score of a document
# doc_id: id of the document
# terms: list of query terms that are not entities
# entities: list of query terms that are entities
# total_docs: num of docs in the corpus
def get_score(doc_id, terms, entities, total_docs, avg_length, max_idf):
    conn = sqlite3.connect("cord19.db")
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    conn.commit()

    c.execute("select length from doc_lengths where doc_id = :doc_id;", {"doc_id":doc_id})
    doc_length = c.fetchone()[0]

    score = 0

    for term in terms:
        # get idf of the term
        c.execute("select idf from terms_idf where term = :term;", {"term": term})
        result = c.fetchone()
        idf = result[0] if result else 0
        # get tf of the term in the doc
        c.execute("select frequency from terms_tf where term = :term and doc_id = :doc_id;", {"term": term, "doc_id":doc_id})
        result = c.fetchone()
        tf = result[0] if result else 0
        # calculate score
        score += calc_summand(tf, idf, doc_length, avg_length)
    for ent in entities:
        # get idf of the entity
        c.execute("select idf from ents_idf where entity = :entity;", {"entity": ent})
        result = c.fetchone()
        idf = result[0] if result else 0
        # get tf of the entity in the doc
        c.execute("select frequency from ents_tf where entity = :entity and doc_id = :doc_id;", {"entity": ent, "doc_id":doc_id})
        result = c.fetchone()
        # calculate score
        score += calc_summand(tf, idf, doc_length, avg_length)
    
    return score

# Calculates and returns the summand for one query term of bm25 formula
# tf: the term frequency of the term in the doc
# idf: the inverse document frequency of the term
# doc_length: the length of the doc in words
def calc_summand(tf, idf, doc_length, avg_length):
    numerator = tf * (BM25_K1 + 1)
#    print("\t\tNumerator: %f" % numerator)
    denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * (doc_length / avg_length))
#    print("\t\tDenominator: %f" % denominator)
    return idf * ((numerator / denominator) + BM25_delta)


# Calculates and returns idf given the number of docs containing a term
# count: num of docs containing the term
# total_docs: num of docs in the corpus
def get_idf(count, total_docs):
    # idf is log(           total num of docs + 1                    )
    #           (----------------------------------------------------)
    #           (        num of docs containing the term             )
    numerator = total_docs + 1
    denominator = count
    idf = math.log10(numerator/denominator)
    return idf

# gets geometric mean of idf1 and idf2
# returns idf1 if idf2 is None
def get_geometric_mean(idf1, idf2, max_idf):
    if idf2 == None:
        return idf1
    else:
        idf2 = normalize_idf(idf2, max_idf)
        return math.sqrt(idf1 * idf2)

# gets normalized idf for idfs in en-idf.txt
# max_idf: max idf in cord-19 corpus
def normalize_idf(idf, max_idf):
    # 13.999 is max idf in en-idf.txt
    return (idf / 14) * max_idf