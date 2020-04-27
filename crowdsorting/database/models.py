from datetime import datetime
from crowdsorting import db
from sqlalchemy import MetaData, ForeignKey
from flask_login import UserMixin
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper
from crowdsorting.database.database import metadata, db_session

DOC_NAME_LENGTH = 120
PROJECT_NAME_LENGTH = 120
SA_NAME_LENGTH = 120
DESCRIPTION_LENGTH = 1024
SELECTION_PROMPT_LENGTH = 64
PREFERRED_PROMPT_LENGTH = 64
UNPREFERRED_PROMPT_LENGTH = 64
CONSENT_FORM_LENGTH = 1000000
LANDING_PAGE_LENGTH = 1000000
JOIN_CODE_LENGTH = 30
FILE_CONTENTS_LENGTH = 10000
FIRST_NAME_LENGTH = 64
LAST_NAME_LENGTH = 64
EMAIL_LENGTH = 64
CID_LENGTH = 64

metadata = MetaData()
metadata.bind = db

Judges = db.Table('judges',
    db.Column('project_name', db.String(PROJECT_NAME_LENGTH), ForeignKey('project.name'), primary_key=True),
    db.Column('judge_id', db.Integer, ForeignKey('judge.id'), primary_key=True),
    info={'bind_key': 'admin_data'}
)


"""CJudges = db.Table('cjudges',
    db.Column('project_name', db.String(120), ForeignKey('project.name'), primary_key=True),
    db.Column('judge_id', db.Integer, ForeignKey('judge.id'), primary_key=True)
)
"""

"""VoteJudges = db.Table('votejudges',
    db.Column('vote_id', db.Integer, ForeignKey('vote.id'), primary_key=True),
    db.Column('judge_id', db.Integer, ForeignKey('judge.id'), primary_key=True)
)
"""

class Project(db.Model):
    __bind_key__ = 'admin_data'
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(PROJECT_NAME_LENGTH), nullable=False)
    sorting_algorithm_id = db.Column(db.Integer, nullable=True)
    # path_to_sorting_algorithm = db.Column(db.String(512), default='')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(DESCRIPTION_LENGTH), nullable=False)
    public = db.Column(db.Boolean, default=False)
    selection_prompt = db.Column(db.String(SELECTION_PROMPT_LENGTH), nullable=False)
    preferred_prompt = db.Column(db.String(PREFERRED_PROMPT_LENGTH), nullable=False)
    unpreferred_prompt = db.Column(db.String(UNPREFERRED_PROMPT_LENGTH), nullable=False)
    consent_form = db.Column(db.String(CONSENT_FORM_LENGTH), nullable=False)
    landing_page = db.Column(db.String(LANDING_PAGE_LENGTH), nullable=False)
    judges = db.relationship('Judge', secondary='judges', lazy='subquery', backref=db.backref('myprojects', lazy=True))
    number_of_docs = db.Column(db.Integer, nullable=False)
    # cjudges = db.relationship('Judge', secondary='cjudges', lazy='subquery', backref=db.backref('mycprojects', lazy=True))
    # docs = db.relationship('Doc', cascade='all')
    # judgments = db.relationship('Judgment', cascade='all')
    join_code = db.Column(db.String(JOIN_CODE_LENGTH), nullable=True)

    def __repr__(self):
        return f"{self.name}"

    def getName(self):
        return self.name


class Doc(db.Model):
    __bind_key__ = 'docs'
    __tablename__ = 'doc'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(DOC_NAME_LENGTH), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    num_compares = db.Column(db.Integer, default=0)
    checked_out = db.Column(db.Boolean, default=False)
    contents = db.Column(db.String(FILE_CONTENTS_LENGTH), default="")
    project_id = db.Column(db.Integer)
    # judgments_harder = db.relationship('Judgment', foreign_keys='Judgment.doc_harder_id', cascade='all')
    # judgments_easier = db.relationship('Judgment', foreign_keys='Judgment.doc_easier_id', cascade='all')

    def __repr__(self):
        return f"{self.name}"


class Judge(db.Model):
    __bind_key__ = 'admin_data'
    __tablename__ = 'judge'
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(FIRST_NAME_LENGTH), nullable=False)
    lastName = db.Column(db.String(LAST_NAME_LENGTH), nullable=False)
    email = db.Column(db.String(EMAIL_LENGTH), unique=True, nullable=False)
    # judgments = db.relationship('Judgment', backref='judger', lazy=True)
    projects = db.relationship('Project', secondary='judges', lazy='subquery', backref=db.backref('myusers', lazy=True))
    # cprojects = db.relationship('Project', secondary='cjudges', lazy='subquery', backref=db.backref('mycusers', lazy=True))
    # votes = db.relationship('Vote', secondary='votejudges', lazy='subquery', backref=db.backref('myjudges', lazy=True))
    cid = db.Column(db.String(CID_LENGTH), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"\nJudge('{self.firstName} {self.lastName}', '{self.email}', '{self.email}', '{self.cid}')"


"""class Judgment(db.Model):
    __tablename__ = 'judgment'
    id = db.Column(db.Integer, primary_key=True)
    doc_harder_id = db.Column(db.Integer, db.ForeignKey('doc.id'))
    doc_easier_id = db.Column(db.Integer, db.ForeignKey('doc.id'))


    doc_harder = db.relationship('Doc', foreign_keys=[doc_harder_id])
    doc_easier = db.relationship('Doc', foreign_keys=[doc_easier_id])

    # doc_one = db.Column(db.Integer, db.ForeignKey('doc.id'), nullable=False)
    # doc_two = db.Column(db.Integer, db.ForeignKey('doc.id'), nullable=False)
    # winner = db.Column(db.Integer, db.ForeignKey(Judge.id), nullable=False) # ID of the harder doc
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'), nullable=True, default=0)

    judge = db.relationship('Judge', foreign_keys=[judge_id])
    project_name = db.Column(db.String(120), ForeignKey('project.name'))

    def __repr__(self):
        if self.judge is not None:
            return f"\nJudgment(Judge='{self.judge.email}', doc_harder='{self.doc_harder.name}', doc_easier='{self.doc_easier.name}')"
        return f"\nJudgment(Judge='DELETED', doc_harder='{self.doc_harder.name}', doc_easier='{self.doc_easier.name}')"
"""

"""class JoinRequest(db.Model):
    __bind_key__ = 'admin_data'
    __tablename__ = 'joinrequest'
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer)

    judge = db.relationship('Judge', foreign_keys=[judge_id])
    project = db.relationship('Project', foreign_keys=[project_id])
"""

class DocPair(db.Model):
    __bind_key__ = 'doc_pairs'
    __tablename__ = 'doc_pair'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer)
    doc1_id = db.Column(db.Integer, nullable=False)
    doc2_id = db.Column(db.Integer, nullable=False)
    checked_out = db.Column(db.Boolean, default=False)
    complete = db.Column(db.Boolean, default=False)
    times_rejected = db.Column(db.Integer, default=0)

class DocPairReject(db.Model):
    __bind_key__ = 'doc_pairs'
    __tablename__ = 'doc_pair_rejects'
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, nullable=False)
    doc_pair_id = db.Column(db.Integer, nullable=False)
    date_rejected = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Comparison(db.Model):
    __bind_key__ = 'sorting_algorithms'
    __tablename__ = 'comparison'
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, nullable=False)
    preferred_doc_name = db.Column(db.String(DOC_NAME_LENGTH))
    unpreferred_doc_name = db.Column(db.String(DOC_NAME_LENGTH))
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    duration_seconds = db.Column(db.Integer)
    sorting_proxy_id = db.Column(db.Integer, ForeignKey('sorting_proxy.id'))
    sorting_proxy = db.relationship('SortingProxy', back_populates='comparisons')

class SortingProxy(db.Model):
    __bind_key__ = 'sorting_algorithms'
    __tablename__ = 'sorting_proxy'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(PROJECT_NAME_LENGTH), nullable=False)
    proxy = db.Column(db.LargeBinary, nullable=True)
    comparisons = db.relationship('Comparison', back_populates='sorting_proxy')


"""class Vote(db.Model):
    __tablename__ = 'vote'
    id = db.Column(db.Integer, primary_key=True)
    doc_one_id = db.Column(db.Integer, db.ForeignKey('doc.id'))
    doc_two_id = db.Column(db.Integer, db.ForeignKey('doc.id'))

    doc_one = db.relationship('Doc', foreign_keys=[doc_one_id])
    doc_two = db.relationship('Doc', foreign_keys=[doc_two_id])

    doc_one_votes = db.Column(db.Integer, default=0)
    doc_two_votes = db.Column(db.Integer, default=0)

    project_name = db.Column(db.String(120), ForeignKey('project.name'))
    resolved = db.Column(db.Boolean, default=False)

    judges = db.relationship('Judge', secondary='votejudges', lazy='subquery', backref=db.backref('myjudges', lazy=True))
"""

def init_db():
    db.create_all()
