import time
from math import floor

from flask import render_template, redirect, url_for, request, flash
import pickle

from crowdsorting import app, cookie_crypter, pairselector_options
from crowdsorting.app_resources import StringList, DBProxy, ProjectHandler, \
    JudgeHandler, PairSelector
from crowdsorting.app_resources.route_decorators import login_required, \
    admin_required, valid_current_project
from crowdsorting.database.models import Judge
from crowdsorting.settings.configurables import PICKLES_PATH

dummy_judge = Judge(id=None, firstName='', lastName='', email='', projects=[], cid='', is_admin=False)

@app.context_processor
def utility_processor():
    return {
            'judge': get_judge(),
            'StringList': StringList,
            'current_project': get_current_project()
            }

def get_judge():
    judge = DBProxy.get_judge(get_email_from_request())
    if judge is None:
        return dummy_judge
    return judge

def get_email_from_request():
    encrypted_email = request.cookies.get('email', None)
    if encrypted_email is None:
        return None
    email = cookie_crypter.decrypt({'email': encrypted_email})['email']
    return email

def get_current_project():
    project = request.cookies.get('current_project', False)
    return project

@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/instructions', methods=['GET'])
@login_required
@valid_current_project
def instructions():
    project_name = request.cookies.get('current_project')
    project = DBProxy.get_project(project_name=project_name)
    return render_template('instructions.html',
                           landing_page=project.landing_page)

@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Renders admin or user dashboards, depending on admin privileges of user
    if DBProxy.check_admin(get_email_from_request()):
        all_users = DBProxy.get_all_judges()  # All judges in the system
        all_group_projects = DBProxy.get_all_group_projects()  # All non-public projects
        public_projects = DBProxy.get_all_public_projects()  # All public projects
        return render_template('admindashboard.html', all_users=all_users,
                               all_group_projects=all_group_projects,
                               public_projects=public_projects,
                               selector_algorithms=pairselector_options,
                               )
    # Not admin, render user dashboard
    judge = DBProxy.get_judge(request.cookies.get('email'))
    all_public_projects = DBProxy.get_all_public_projects()
    filtered_public_projects = [p for p in all_public_projects if judge not in p.judges]
    return render_template('userdashboard.html',
                           filtered_public_projects=filtered_public_projects)


@app.route('/consentform', methods=['GET'])
@login_required
def consent_form():
    project_name = request.cookies.get('current_project')
    project = DBProxy.get_project(project_name=project_name)
    return render_template('consentform.html',
                           consent_form_text=project.consent_form,
                           admin=False)

@app.route('/signconsent', methods=['POST'])
@login_required
def sign_consent():
    email = get_email_from_request()
    project_name = request.form.get('project_name')
    admin = request.form.get('admin')
    DBProxy.sign_consent_form(email, project_name)
    if admin == 'True':
        return redirect(url_for('tower'))
    return redirect(url_for('sorter'))


@app.route('/sorter', methods=['GET'])
@login_required
@valid_current_project
def sorter():
    email = get_email_from_request()
    project_name = request.cookies.get('current_project')
    if not DBProxy.user_has_signed_consent(email, project_name):
        return redirect(url_for('consent_form'))
    project = DBProxy.get_project(project_name=project_name)
    pair, success_code = PairSelector.get_pair(project_name, email)
    if success_code == 1:
        flash('no pair currently available', 'warning')
        return render_template('instructions.html')
    if success_code == 2:
        ProjectHandler.start_new_round(project_name)
        return redirect(url_for('sorter'))
    if success_code == 3:
        flash('project not found', 'warning')
        return redirect(url_for('dashboard'))
    if success_code == 4:
        flash('user not found', 'warning')
        return redirect(url_for('home'))
    file_one_contents = DBProxy.get_doc_contents(pair.doc1_id)
    file_two_contents = DBProxy.get_doc_contents(pair.doc2_id)
    return render_template('sorter.html',
                           pair_id=pair.id,
                           file_one_id=pair.doc1_id,
                           file_two_id=pair.doc2_id,
                           project=project,
                           time_started=floor(time.time()),
                           timeout=120*1000,
                           file_one=file_one_contents,
                           file_two=file_two_contents,
                           admin=False
                           )

@app.route('/submitAnswer', methods=['POST'])
@login_required
def submit_answer():
    pair_id = request.form.get('pair_id')
    preferred_doc_id = request.form.get('preferred')
    pair_submitted = DBProxy.submit_doc_pair(
        pair_id=pair_id, preferred_doc_id=preferred_doc_id)
    email = get_email_from_request()
    judge_id = DBProxy.get_judge_id(email)
    unpreferred_doc_id = request.form.get('unpreferred')
    time_started = int(request.form.get('time_started'))
    proxy_id = DBProxy.get_sorting_proxy_id(get_current_project())
    preferred_doc_name = DBProxy.get_doc_name(preferred_doc_id)
    unpreferred_doc_name = DBProxy.get_doc_name(unpreferred_doc_id)
    DBProxy.make_comparison(
        judge_id=judge_id, preferred_doc_name=preferred_doc_name,
        unpreferred_doc_name=unpreferred_doc_name,
        duration=floor(time.time()) - time_started, sorting_proxy_id=proxy_id,
        used_in_sorting=pair_submitted, project_name=get_current_project())
    if request.form.get('admin') == 'True':
        return redirect(url_for('tower'))
    if isinstance(request.form.get('another_pair_checkbox'), type(None)):
        # flash('Judgment submitted', 'success')
        return redirect(url_for('instructions'))
    else:
        return redirect(url_for('sorter'))


@app.route('/safeexit', methods=['POST'])
@login_required
def safe_exit():
    pair_id = request.form.get('pair_id')
    DBProxy.return_pair(pair_id)
    return redirect(url_for('instructions'))


@app.route('/hardeasy', methods=['POST'])
@login_required
def hard_easy():
    email = get_email_from_request()
    project = get_current_project()
    doc1_id = request.form.get('file_one_id')
    doc2_id = request.form.get('file_two_id')
    pair_id = request.form.get('pair_id')
    DBProxy.add_doc_pair_reject(judge_id=DBProxy.get_judge_id(email),
                                project_name=project,
                                doc1_id=doc1_id,
                                doc2_id=doc2_id,
                                doc_pair_id=pair_id)
    DBProxy.return_pair(pair_id, too_hard=True)
    return redirect(url_for('sorter'))


@app.route('/sorted', methods=['GET'])
@login_required
@admin_required
def sorted():
    return render_template('sorted.html')

@app.route('/tower', methods=['GET'])
@login_required
@admin_required
def tower():
    project_name = get_current_project()
    proxy_id = DBProxy.get_proxy_id(project_name=project_name)
    project_proxy = DBProxy.get_proxy(proxy_id, database_model=False)

    project_model = DBProxy.get_project(project_name=project_name)

    def time_left(expiration_time):
        time_seconds = expiration_time - time.time()
        seconds = int(time_seconds % 60)
        minutes = floor(time_seconds / 60)
        return f'{minutes} minute{("" if minutes == 1 else "s")}, ' \
               f'{seconds} second{("" if seconds == 1 else "s")}'

    roundList = DBProxy.get_round_list(project_name)
    checked_out = [x for x in roundList if (x.checked_out and x.expiration_time > time.time())]
    active_judges = {x.user_checked_out_by for x in checked_out}

    return render_template('tower.html',
                           project_proxy=project_proxy,
                           time_left=time_left,
                           project_model=project_model,
                           roundList=roundList,
                           checked_out=checked_out,
                           active_judges=active_judges)

@app.route('/accountinfo', methods=['GET'])
def accountinfo():
    return render_template('accountinfo.html')

@app.route('/addproject', methods=['POST'])
@login_required
@admin_required
def add_project():
    # Get data from form
    project_name = request.form.get('project_name')
    if ' ' in project_name:
        flash('project name may not contain spaces', 'warning')
        return redirect(url_for('dashboard'))
    sorting_algorithm_name = request.form.get('selector_algorithm')
    public = (True if request.form.get('public') == 'on' else False)
    join_code = request.form.get('join_code')
    description = request.form.get('description')
    message, status = ProjectHandler.create_project(
        name=project_name,
        sorting_algorithm_name=sorting_algorithm_name,
        public=public,
        join_code=join_code,
        description=description,
        files=request.files.getlist("file"),
    )
    flash(message, status)
    return redirect(url_for('dashboard'))

@app.route('/deleteProject', methods=['POST'])
@login_required
@admin_required
def delete_project():
    project_name = request.form.get('project_name_delete', None)
    if project_name is None:
        return redirect(url_for('dashboard'))
    message, status = ProjectHandler.delete_project(project_name)
    flash(message, status)
    return redirect(url_for('dashboard'))

@app.route('/editproject', methods=['POST'])
@login_required
@admin_required
def edit_project():
    project_name = request.form.get('project_name_edit', None)
    if project_name is None:
        flash('project not found', 'warning')
        return redirect(url_for('dashboard'))
    project = DBProxy.get_project(project_name=project_name)
    if project is None:
        flash('project not found', 'warning')
        return redirect(url_for('dashboard'))
    return render_template('editproject.html', project=project)

@app.route('/updateprojectinfo', methods=['POST'])
@login_required
@admin_required
def update_project_info():
    name = request.form.get('name')
    description = request.form.get('description')
    selection_prompt = request.form.get('selection_prompt')
    preferred_prompt = request.form.get('preferred_prompt')
    unpreferred_prompt = request.form.get('unpreferred_prompt')
    consent_form = request.form.get('consent_page')
    instruction_page = request.form.get('instruction_page')
    success = ProjectHandler.update_project_info(
        name, description, selection_prompt, preferred_prompt,
    unpreferred_prompt, consent_form, instruction_page)
    if not success:
        flash(f'unable to update project {name}', 'danger')
        return redirect(url_for('dashboard'))

    flash(f'updated project {name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/deleteuser', methods=['POST'])
@login_required
@admin_required
def delete_user():
    judge_id = request.form.get('user_id')
    JudgeHandler.delete_judge(judge_id)
    return redirect(url_for('dashboard'))

@app.route('/addpublicproject', methods=['POST'])
@login_required
def add_public_project():
    project_name = request.form.get('project_name')
    email = get_email_from_request()
    DBProxy.add_user_to_project(email, project_name=project_name)
    return redirect(url_for('dashboard'))

@app.route('/joincode', methods=['POST'])
@login_required
def join_code():
    project_name = request.form.get('project_name')
    join_code = request.form.get('join_code')
    if not DBProxy.verify_join_code(project_name, join_code):
        flash('invalid project name or join code', 'warning')
        return redirect(url_for('dashboard'))
    email = get_email_from_request()
    DBProxy.add_user_to_project(email, project_name=project_name)
    flash(f'added project {project_name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/selectproject', methods=['POST'])
@login_required
def select_project():
    project_name = request.form.get('project_name')
    email = get_email_from_request()
    if not DBProxy.verify_user_in_project(email, project_name=project_name):
        flash(f'unable to select project {project_name}', 'warning')
        return redirect(url_for('dashboard'))
    return_page = request.form.get('return_page', False)
    if return_page:
        res = redirect(return_page)
    else:
        res = redirect(url_for('instructions'))
    res.set_cookie('current_project', project_name)
    return res

@app.route('/removeself', methods=['POST'])
@login_required
def remove_self():
    email = get_email_from_request()
    project_name = request.form.get('project_name')
    print(f'remove {email} from {project_name}')
    DBProxy.remove_user_from_project(email, project_name=project_name)
    current_project = get_current_project()
    res = redirect(url_for('dashboard'))
    if project_name == current_project:
        res.set_cookie('current_project', '', max_age=0)
    return res


@app.route('/forcereturn', methods=['POST'])
@login_required
@admin_required
def force_return():
    pair_id = request.form.get('pair_id')
    DBProxy.return_pair(pair_id)
    return redirect(url_for('tower'))