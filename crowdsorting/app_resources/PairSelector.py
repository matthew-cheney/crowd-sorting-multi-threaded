from crowdsorting.app_resources import DBProxy


def get_pair(project_name, email):
    pair = DBProxy.get_pair(project_name, email)
    return pair


def process_doc_pairs(proxy):
    project_id = DBProxy.get_project_id(proxy.project_name)
    all_pairs = DBProxy.get_doc_pairs(project_id)
    if len(all_pairs) < len(proxy.get_round_list()):
        return 'not all pairs have been judged yet'
    # Submit all comparisons to proxy
    for pair in all_pairs:
        if pair.doc1_id == pair.preferred_id:
            proxy.make_comparison(pair.doc1_id, pair.doc2_id)
        elif pair.doc2_id == pair.preferred_id:
            proxy.make_comparison(pair.doc1_id, pair.doc2_id)
        else:
            raise KeyError('docpair marked complete without indicating preferred_id')


def turn_over_round(proxy):
    proxy.acj.nextPair()


def populate_doc_pairs(proxy):
    all_pairs = proxy.get_round_list()
    project_id = DBProxy.get_project_id(proxy.project_name)
    DBProxy.add_doc_pairs(project_id, all_pairs)
