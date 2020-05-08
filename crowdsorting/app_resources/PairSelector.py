from crowdsorting.app_resources import DBProxy
import logging

def get_pair(project_name, email):
    logging.info('in get_pair')
    pair, success_code = DBProxy.get_pair(project_name, email)
    return pair, success_code


def process_doc_pairs(proxy, proxy_id):
    logging.info('in process_doc_pairs')
    project_id = DBProxy.get_project_id(proxy.project_name)
    all_pairs = DBProxy.get_completed_doc_pairs(project_id)
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
    # DBProxy.update_proxy(proxy_id, proxy=proxy)
    DBProxy.delete_doc_pairs(project_id)


def turn_over_round(proxy, proxy_id):
    logging.info('in turn_over_round')
    proxy.new_round()
    # DBProxy.update_proxy(proxy_id, proxy=proxy)



def populate_doc_pairs(proxy):
    logging.info('in populate_doc_pairs')
    all_pairs = proxy.get_round_list()
    project_id = DBProxy.get_project_id(proxy.project_name)
    DBProxy.add_doc_pairs(project_id, all_pairs)
