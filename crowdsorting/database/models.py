from datetime import datetime
from crowdsorting import db
from sqlalchemy import MetaData, ForeignKey
from flask_login import UserMixin
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper
from crowdsorting.database.database import metadata, db_session

metadata = MetaData()
metadata.bind = db

DOC_NAME_LENGTH = 120

Judges = db.Table('judges',
    db.Column('project_name', db.String(120), ForeignKey('project.name'), primary_key=True),
    db.Column('judge_id', db.Integer, ForeignKey('judge.id'), primary_key=True)
)

CJudges = db.Table('cjudges',
    db.Column('project_name', db.String(120), ForeignKey('project.name'), primary_key=True),
    db.Column('judge_id', db.Integer, ForeignKey('judge.id'), primary_key=True)
)

VoteJudges = db.Table('votejudges',
    db.Column('vote_id', db.Integer, ForeignKey('vote.id'), primary_key=True),
    db.Column('judge_id', db.Integer, ForeignKey('judge.id'), primary_key=True)
)


class Project(db.Model):
    __tablename__ = 'project'
    name = db.Column(db.String(DOC_NAME_LENGTH), nullable=False, primary_key=True)
    sorting_algorithm = db.Column(db.String(120), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(1024), nullable=False)
    public = db.Column(db.Boolean, default=False)
    selection_prompt = db.Column(db.String(120), nullable=False)
    preferred_prompt = db.Column(db.String(120), nullable=False)
    unpreferred_prompt = db.Column(db.String(120), nullable=False)
    consent_form = db.Column(db.String(9001), nullable=False)
    landing_page = db.Column(db.String(9001), nullable=False)
    judges = db.relationship('Judge', secondary='judges', lazy='subquery', backref=db.backref('myprojects', lazy=True))
    cjudges = db.relationship('Judge', secondary='cjudges', lazy='subquery', backref=db.backref('mycprojects', lazy=True))
    docs = db.relationship('Doc', cascade='all')
    judgments = db.relationship('Judgment', cascade='all')
    join_code = db.Column(db.String(32), nullable=True)

    def __repr__(self):
        return f"{self.name}"

    def getName(self):
        return self.name


class Doc(db.Model, UserMixin):
    __tablename__ = 'doc'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    num_compares = db.Column(db.Integer, default=0)
    checked_out = db.Column(db.Boolean, default=False)
    contents = db.Column(db.String(100000), default="")
    project_name = db.Column(db.String(120), ForeignKey('project.name'))
    judgments_harder = db.relationship('Judgment', foreign_keys='Judgment.doc_harder_id', cascade='all')
    judgments_easier = db.relationship('Judgment', foreign_keys='Judgment.doc_easier_id', cascade='all')

    def __repr__(self):
        return f"{self.name}"


class Judge(db.Model):
    __tablename__ = 'judge'
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    judgments = db.relationship('Judgment', backref='judger', lazy=True)
    projects = db.relationship('Project', secondary='judges', lazy='subquery', backref=db.backref('myusers', lazy=True))
    cprojects = db.relationship('Project', secondary='cjudges', lazy='subquery', backref=db.backref('mycusers', lazy=True))
    votes = db.relationship('Vote', secondary='votejudges', lazy='subquery', backref=db.backref('myjudges', lazy=True))
    cid = db.Column(db.String(64), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"\nJudge('{self.firstName} {self.lastName}', '{self.email}', '{self.email}', '{self.cid}')"


class Judgment(db.Model):
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

class JoinRequest(db.Model):
    __tablename__ = 'joinrequest'
    id = db.Column(db.Integer, primary_key=True)
    judge_id = db.Column(db.Integer, db.ForeignKey('judge.id'))
    project_name = db.Column(db.String(DOC_NAME_LENGTH), db.ForeignKey('project.name'))

    judge = db.relationship('Judge', foreign_keys=[judge_id])
    project = db.relationship('Project', foreign_keys=[project_name])


class Vote(db.Model):
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


def init_db():
    db.create_all()
