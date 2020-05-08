import pickle

from crowdsorting import pairselector_options
from crowdsorting.app_resources import DBProxy, PairSelector
from crowdsorting.settings.configurables import PICKLES_PATH

def create_project(name, sorting_algorithm_name, public, join_code, description, files):

    # Identify selected sorting algorithm
    target_algorithm = None
    for algorithm in pairselector_options:
        if sorting_algorithm_name == algorithm.get_algorithm_name():
            target_algorithm = algorithm
            break
    if target_algorithm is None:
        return f'sorting algorithm \'{sorting_algorithm_name}\' not found', 'warning'

    # Create project entry in database
    project_id = DBProxy.add_project(
        name=name,
        sorting_algorithm=sorting_algorithm_name,
        number_of_docs=0,
        public=public,
        join_code=join_code,
        description=description
    )

    if not project_id:
        return 'project name already used', 'warning'

    # Insert files into database
    file_ids = DBProxy.insert_files(files, project_id)

    # Create algorithm proxy for project
    project_proxy = target_algorithm(name)
    project_proxy.initialize_selector(file_ids)

    # Fill docpairs table in database
    PairSelector.turn_over_round(project_proxy)
    print(f'populating docpairs with: {project_proxy.roundList}')
    PairSelector.populate_doc_pairs(project_proxy)

    # Insert proxy into database
    proxy_id = DBProxy.add_proxy(project_proxy, name)
    print(f'new proxy roundList: {project_proxy.roundList}')

    # Update project in database with new info
    DBProxy.add_num_docs_to_project(project_id, len(file_ids))
    DBProxy.add_sorting_algorithm_id_to_project(project_id, proxy_id)

    f'added project {name} with {len(file_ids)} docs'

    test_proxy = DBProxy.get_proxy(proxy_id, database_model=False)
    print(f'new proxy from db: {test_proxy.roundList}')

    return '', ''

def delete_project(project_name):
    # Get the project id
    project_id = DBProxy.get_project_id(project_name)
    if project_id is None:
        return 'project not found', 'warning'

    # Delete sorting proxy and logs
    DBProxy.delete_sorting_proxy(project_name=project_name)

    # Delete doc pairs
    DBProxy.delete_doc_pairs(project_id)

    # Delete project itself
    DBProxy.delete_project(project_id)

    return f'project {project_name} deleted', 'success'

def update_project_info(name, description, selection_prompt, preferred_prompt,
                        unpreferred_prompt, consent_form, landing_page):
    project = DBProxy.get_project(project_name=name)
    if project is None:
        return False
    DBProxy.delete_all_consents_from_project(project_name=name)
    return DBProxy.update_project(name, description, selection_prompt, preferred_prompt,
                           unpreferred_prompt, consent_form, landing_page)


def start_new_round(project_name):
    proxy_id = DBProxy.get_sorting_proxy_id(project_name)
    proxy = DBProxy.get_proxy(proxy_id)
    print(f'old round: {proxy.roundList}')
    PairSelector.process_doc_pairs(proxy, proxy_id)
    PairSelector.turn_over_round(proxy)
    PairSelector.populate_doc_pairs(proxy)
    DBProxy.update_proxy(proxy_id, proxy=proxy)
    print(f'new round: {proxy.roundList}')
