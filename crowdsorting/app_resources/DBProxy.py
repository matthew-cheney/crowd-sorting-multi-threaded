import uuid

from crowdsorting import db
from crowdsorting.database.models import Judge, Project, Doc


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
