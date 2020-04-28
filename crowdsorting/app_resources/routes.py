from flask import render_template, redirect, url_for, request, flash
import pickle

from crowdsorting import app, cookie_crypter, pairselector_options
from crowdsorting.app_resources import StringList, DBProxy, ProjectHandler, \
    JudgeHandler
from crowdsorting.app_resources.route_decorators import login_required, \
    admin_required, valid_current_project
from crowdsorting.database.models import Judge
from crowdsorting.settings.configurables import PICKLES_PATH

dummy_judge = Judge(id=None, firstName='', lastName='', email='', projects=[], cid='', is_admin=False)

@app.context_processor
def utility_processor():
    return {'judge': get_judge(),
            'StringList': StringList}

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

@app.route('/sorter', methods=['GET'])
@login_required
def sorter():
    return render_template('sorter.html')

@app.route('/sorted', methods=['GET'])
@login_required
@admin_required
def sorted():
    return render_template('sorted.html')

@app.route('/tower', methods=['GET'])
@login_required
@admin_required
def tower():
    return render_template('tower.html')

@app.route('/accountinfo', methods=['GET'])
def accountinfo():
    return render_template('accountinfo.html')

@app.route('/addproject', methods=['POST'])
@login_required
@admin_required
def add_project():
    # Get data from form
    project_name = request.form.get('project_name')
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
    res = redirect(url_for('instructions'))
    res.set_cookie('current_project', project_name)
    return res
