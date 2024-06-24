
def concordance (lang, form, recurse=True):
    form = lang.lexicon[form]
    for token in form.tokens():
        sent = token.sentence()
        i = token.sentence_index()
        lc = ' '.join(sent[:i])
        rc = ' '.join(sent[i+1:])
        rest = token + '  ' + rc
        print(f'{lc:>35}'[-35:], '', rest[:45])

