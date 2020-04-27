import pickle

from crowdsorting import pairselector_options
from crowdsorting.app_resources import DBProxy
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
    filenames = DBProxy.insert_files(files, project_id)

    # Create algorithm proxy for project
    project_proxy = target_algorithm(name)
    project_proxy.initialize_selector(filenames)

    # Insert proxy into database
    proxy_id = DBProxy.add_proxy(project_proxy, name)

    # Update project in databse with new info
    DBProxy.add_num_docs_to_project(project_id, len(filenames))
    DBProxy.add_sorting_algorithm_id_to_project(project_id, proxy_id)
    f'added project {name} with {len(filenames)} docs'
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
    return DBProxy.update_project(name, description, selection_prompt, preferred_prompt,
                           unpreferred_prompt, consent_form, landing_page)
