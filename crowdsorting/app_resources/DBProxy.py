import pickle
import uuid

from crowdsorting import db
from crowdsorting.database.models import Judge, Project, Doc, SortingProxy, \
    DocPair, DocPairReject, Consent
from crowdsorting.settings.configurables import *

def is_user_exists(email):
    judge = db.session.query(Judge).filter_by(email=email).first()
    if judge is None:
        return False
    return True

def set_user_as_admin(email, admin=True):
    judge = db.session.query(Judge).filter_by(email=email).first()
    judge.is_admin = admin
    db.session.commit()

def create_user(firstName, lastName, email):
    cid = uuid.uuid4().hex
    db.session.add(Judge(firstName=firstName, lastName=lastName,
                         email=email, cid=cid))
    db.session.commit()
    return cid

def get_user_cid(email):
    judge = db.session.query(Judge).filter_by(email=email).first()
    if judge is None:
        return ''
    return judge.cid

def get_all_projects():
    projects = db.session.query(Project).all()
    return projects

def add_user_to_project(email, project_id=None, project_name=None):
    if project_id is not None:
        project = db.session.query(Project).filter_by(id=project_id).first()
    else:
        project = db.session.query(Project).filter_by(name=project_name).first()
    if project is None:
        return
    judge = db.session.query(Judge).filter_by(email=email).first()
    if judge is None:
        return
    if judge in project.judges:
        return
    project.judges.append(judge)
    db.session.commit()

def remove_user_from_project(email, project_id=None, project_name=None):
    if project_id is not None:
        project = db.session.query(Project).filter_by(id=project_id).first()
    else:
        project = db.session.query(Project).filter_by(name=project_name).first()
    if project is None:
        return
    judge = db.session.query(Judge).filter_by(email=email).first()
    if judge is None:
        return
    if judge not in project.judges:
        return
    project.judges.remove(judge)
    db.session.commit()

def verify_login(email, cid):
    judge = db.session.query(Judge).filter_by(email=email, cid=cid).first()
    if judge is None:
        return False
    return True

def check_admin(email):
    judge = db.session.query(Judge).filter_by(email=email).first()
    if judge is None:
        return False
    return judge.is_admin

def get_judge(email):
    return db.session.query(Judge).filter_by(email=email).first()

def get_all_judges():
    return db.session.query(Judge).all()

def get_all_group_projects():
    return db.session.query(Project).filter_by(public=False).all()

def get_all_public_projects():
    """
    Retrieve all public projects from the database
    :return: list of DB Project objects
    """
    return db.session.query(Project).filter_by(public=True).all()

def get_number_of_judgments(project_id):
    pass

def add_project(name, sorting_algorithm, number_of_docs, public, join_code, description):
    project = db.session.query(Project).filter_by(name=name).first()
    if project is not None:
        return False
    db.session.add(Project(
        name=name,
        sorting_algorithm_id=sorting_algorithm,
        description=description,
        public=public,
        selection_prompt=DEFAULT_SELECTION_PROMPT,
        preferred_prompt=DEFAULT_PREFERRED_PROMPT,
        unpreferred_prompt=DEFAULT_UNPREFERRED_PROMPT,
        consent_form=DEFAULT_CONSENT_FORM,
        landing_page=DEFAULT_LANDING_PAGE,
        number_of_docs=number_of_docs,
        join_code=join_code
    ))
    db.session.commit()
    project = db.session.query(Project).filter_by(name=name).first()
    project_id = project.id
    print(f'added project {name} with id {project_id}')
    return project_id

def insert_files(files, project_id):
    for file in files:
        if file.filename.rsplit('.', 1)[
        1].lower() not in VALID_FILE_TYPES:
            return f'invalid file type: {file.filename}'
    for file in files:
        db.session.add(Doc(
            name=file.filename,
            project_id=project_id,
            contents=file.read()
        ))
    db.session.commit()
    docs = db.session.query(Doc).filter_by(project_id=project_id).all()
    return [doc.id for doc in docs]

def add_num_docs_to_project(project_id, num_docs):
    project = db.session.query(Project).filter_by(id=project_id).first()
    if project is None:
        return False
    project.number_of_docs = num_docs
    db.session.commit()
    return True

def add_sorting_algorithm_id_to_project(project_id, proxy_id):
    project = db.session.query(Project).filter_by(id=project_id).first()
    if project is None:
        return False
    project.sorting_algorithm_id = proxy_id
    db.session.commit()
    return True

def add_proxy(proxy, project_name):
    proxy_btyes = pickle.dumps(proxy)
    db.session.add(SortingProxy(project_name=project_name, proxy=proxy_btyes))
    db.session.commit()

    proxy_found = db.session.query(SortingProxy).filter_by(project_name=project_name).first()
    return proxy_found.id

def get_proxy(proxy_id):
    proxy = db.session.query(SortingProxy).filter_by(id=proxy_id).first()
    if proxy is None:
        return False
    return proxy

def get_project_id(name):
    project = db.session.query(Project).filter_by(name=name).first()
    if project is None:
        return None
    return project.id

def delete_sorting_proxy(sorting_proxy_id=None, project_name=None):
    if sorting_proxy_id is not None:
        proxy = db.session.query(SortingProxy).filter_by(id=sorting_proxy_id).first()
    elif project_name is not None:
        proxy = db.session.query(SortingProxy).filter_by(project_name=project_name).first()
    else:
        return
    if proxy is None:
        return
    del(proxy)
    db.session.commit()

def delete_doc_pairs(project_id):
    db.session.query(DocPair).filter_by(project_id=project_id).delete()
    db.session.commit()

def delete_project(project_id):
    project = db.session.query(Project).filter_by(id=project_id).first()
    delete_all_consents_from_project(project.name)
    db.session.query(Project).filter_by(id=project_id).delete()
    db.session.commit()

def get_project(project_name=None, project_id=None):
    if project_name is not None:
        return db.session.query(Project).filter_by(name=project_name).first()
    else:
        return db.session.query(Project).filter_by(id=project_id).first()

def update_project(name, description, selection_prompt, preferred_prompt,
                        unpreferred_prompt, consent_form, landing_page):
    project = db.session.query(Project).filter_by(name=name).first()
    if project is None:
        return False
    project.description = description
    project.selection_prompt = selection_prompt
    project.preferred_prompt = preferred_prompt
    project.unpreferred_prompt = unpreferred_prompt
    project.consent_form = consent_form
    project.landing_page = landing_page

    db.session.commit()

    return True


def delete_judge(judge_id):
    db.session.query(Judge).filter_by(id=judge_id).delete()
    db.session.commit()


def verify_join_code(project_name, join_code):
    project = db.session.query(Project).filter_by(name=project_name, join_code=join_code).first()
    return project is not None


def verify_user_in_project(email, project_name):
    project = db.session.query(Project).filter_by(name=project_name).first()
    if project is None:
        return False
    judge = get_judge(email)
    return judge in project.judges


def get_pair(project_name, email):
    project = db.session.query(Project).filter_by(name=project_name).first()
    if project is None:
        return 'project not found'
    project_id = project.id
    pairs = db.session.query(DocPair).filter_by(project_id=project_id, complete=False, checked_out=False).all()
    if len(pairs) == 0:
        return 'no pairs available'
    judge = db.session.query(Judge).filter_by(email=email).first()
    if judge is None:
        return 'judge not found'
    pair_rejects = db.session.query(DocPairReject).filter_by(judge_id=judge.id).all()
    pair_rejects = [x.doc_pair_id for x in pair_rejects]
    for pair in pairs:
        if pair.id not in pair_rejects:
            return pair
    return 'no pair available for user'


def add_doc_pairs(project_id, id_pairs):
    for pair in id_pairs:
        doc1_id = int(pair[0])
        doc2_id = int(pair[1])
        db.session.add(DocPair(project_id=project_id,
                               doc1_id=doc1_id,
                               doc2_id=doc2_id))
    db.session.commit()


def get_doc_pairs(project_id):
    pairs = db.session.query(DocPair).filter_by(project_id=project_id).all()
    return pairs


def get_doc_contents(doc_id):
    doc = db.session.query(Doc).filter_by(id=doc_id).first()
    if doc is None:
        return ''
    return doc.contents


def sign_consent_form(email, project_name):
    db.session.add(Consent(email=email, project_name=project_name))
    db.session.commit()


def user_has_signed_consent(email, project_name):
    consent = db.session.query(Consent).filter_by(email=email, project_name=project_name, active=True).first()
    return (consent is not None)


def delete_all_consents_from_project(project_name):
    db.session.query(Consent).filter_by(project_name=project_name).delete()
    db.session.commit()
