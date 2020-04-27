import uuid

from crowdsorting import db
from crowdsorting.database.models import Judge, Project, Doc
from crowdsorting.settings.configurables import *

def is_user_exists(email):
    judge = db.session.query(Judge).filter_by(email=email).first()
    if judge is None:
        return False
    return True

def set_user_as_admin(email):
    judge = db.session.query(Judge).filter_by(email=email).first()
    judge.is_admin = True
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

def add_user_to_project(email, project_id):
    project = db.session.query(Project).filter_by(id=project_id).first()
    if project is None:
        return
    judge = db.session.query(Judge).filter_by(email=email).first()
    if judge is None:
        return
    if judge in project.judges:
        return
    project.judges.append(judge)
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
    return db.session.query(Project).filter_by(public=True).all()

def get_number_of_judgments(project_id):
    pass

def add_project(name, sorting_algorithm, number_of_docs, public, join_code, description):
    project = db.session.query(Project).filter_by(name=name).first()
    if project is not None:
        return False
    db.session.add(Project(
        name=name,
        sorting_algorithm=sorting_algorithm,
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
            project_id=project_id
        ))
    db.session.commit()
    return [file.filename for file in files]

def add_num_docs_to_project(project_id, num_docs):
    project = db.session.query(Project).filter_by(id=project_id).first()
    if project is None:
        return False
    project.number_of_docs = num_docs
    db.session.commit()
    return True

def add_sorting_algorithm_filepath_to_project(project_id, filepath):
    project = db.sesson.query(Project).filter_by(id=project_id).first()
    if project is None:
        return False
    project.path_to_sorting_algorithm = filepath
    db.session.commit()
    return True