##  @package seal.nlp.dp.eval
#   Compute accuracy of the parser.

import unicodedata
from ..cld.seal.io import tabular


##  Value is True just in case
#   all characters have Unicode property "Punctuation."
#     - http://depparse.uvt.nl/SoftwarePage.html#eval07.pl
#     - CoNLL-2006 shared task: exclude punctuation tokens.
#     - CoNLL-2007 shared task: include punctuation tokens.
#
# Unicode punctuation categories: Pc Pd Ps Pe Pi Pf Po.
# No other categories begin with P.

def ispunc (s):
    for c in str(s):
        cat = unicodedata.category(c)
        if not cat.startswith('P'): return False
    return True


##  Evaluate a sentence.  Return value is a tuple: (las, uas, la, n).
#    - LAS: count of tokens with correct govr + label.
#    - UAS: count of tokens with correct govr.
#    - LA: count of tokens with correct (role) label.
#    - N: the number of words excluding Root.

def eval_sent (pred, truth, excludepunc=True):
    las = 0
    uas = 0
    la = 0
    n = 0
    for w in range(1, len(truth)):
        if excludepunc and ispunc(truth.form(w)): continue
        predrole = pred.role(w) or ''
        predgovr = pred.govr(w) or 0
        truerole = truth.role(w)
        truegovr = truth.govr(w)
        labelcorrect = (predrole == truerole)
        govrcorrect = (predgovr == truegovr)
        n += 1
        if govrcorrect: uas += 1
        if labelcorrect: la += 1
        if govrcorrect and labelcorrect: las += 1
    return (las, uas, la, n)

##  Prints two tables.  The first has one row per word, and its columns
#   are the word number, '*' if punctuation, the word form,
#   'G' if the governor is correct, 'R' if the role is correct,
#   the predicted governor, the predicted role,
#   the true governor, the true role.
#   The second contains statistics for labeled accuracy (govr + role),
#   unlabeled accuracy (govr only),
#   and label accuracy (role only).  For each, it gives numerator, denominator,
#   and proportion.

def compare (pred, truth):
    las = 0
    uas = 0
    la = 0
    n = 0
    rows = []
    for w in range(1, len(truth)):
        s = truth.form(w)
        p = ' '
        g = ' '
        r = ' '
        if ispunc(s):
            p = '*'
        else:
            predrole = pred.role(w) or ''
            predgovr = pred.govr(w) or 0
            truerole = truth.role(w)
            truegovr = truth.govr(w)
            labelcorrect = (predrole == truerole)
            govrcorrect = (predgovr == truegovr)
            n += 1
            if govrcorrect:
                g = 'G'
                uas += 1
            if labelcorrect:
                r = 'R'
                la += 1
            if govrcorrect and labelcorrect:
                las += 1
        row = [w, p, s, g, r, predgovr, predrole, truegovr, truerole]
        rows.append(row)
    print(tabular(rows))
    print()
    print(tabular([['LAS:', las, n, las/n],
                   ['UAS:', uas, n, uas/n],
                   ['LA:', la, n, la/n]]))

##  Evaluate a parser on a set of sentences.
#   Calls the parser on each sentence in turn.
#   Prints a table of statistics.

def evaluate (parser, sents, excludepunc=True, output=None):
    counts = [0, 0, 0, 0]
    nsents = 0
    for truth in sents:
        pred = parser(truth)
        inc = eval_sent(pred, truth, excludepunc)
        nsents += 1
        for i in range(4):
            counts[i] += inc[i]
    (las, uas, la, n) = counts

    print(tabular([['LAS:', las, n, las/n],
                              ['UAS:', uas, n, uas/n],
                              ['LA:', la, n, la/n],
                              ['NSents:', nsents, '', '']]), file=output)

    return (las, uas, la, n, nsents)
