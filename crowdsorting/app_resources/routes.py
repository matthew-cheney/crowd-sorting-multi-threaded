from flask import render_template, redirect, url_for, request, flash
import pickle

from crowdsorting import app, cookie_crypter, pairselector_options
from crowdsorting.app_resources import StringList, DBProxy
from crowdsorting.app_resources.route_decorators import login_required, admin_required
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


@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

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
    return render_template('userdashboard.html')

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

    # Create project entry in database
    project_id = DBProxy.add_project(
        name=project_name,
        sorting_algorithm=sorting_algorithm_name,
        number_of_docs=0,
        public=public,
        join_code=join_code,
        description=description
    )

    if not project_id:
        flash('project name already used')
        return redirect(url_for('admin'))

    # Identify selected sorting algorithm
    target_algorithm = None
    for algorithm in pairselector_options:
        if sorting_algorithm_name == algorithm.get_algorithm_name():
            target_algorithm = algorithm
            break
    if target_algorithm is None:
        flash('sorting algorithm not found')
        return redirect(url_for('dashboard'))

    # Insert files into database
    filenames = DBProxy.insert_files(request.files.getlist("file"),
                           project_id)

    # Create algorithm proxy for project and pickle it
    project_proxy = target_algorithm(project_name)
    project_proxy.initialize_selector(filenames)
    pickle_proxy(project_proxy)

    # Update project in databse with new info
    DBProxy.add_num_docs_to_project(project_id, len(filenames))
    DBProxy.add_sorting_algorithm_filepath_to_project(project_id, f'{PICKLES_PATH}/{project_name}.pkl')

    flash(f'added project {project_name} with {len(filenames)} docs')
    return redirect(url_for('dashboard'))

def pickle_proxy(proxy):
    with open(f'{PICKLES_PATH}/{proxy.project_name}.pkl', 'wb') as f:
        pickle.dump(proxy, f)

def unpickle_proxy(project_name):
    try:
        with open(f'{PICKLES_PATH}/{project_name}.pkl', 'rb') as f:
            proxy = pickle.load(f)
        return proxy
    except FileNotFoundError:
        return None
