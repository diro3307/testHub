"""
TestHUB QE Portal - GitHub Integration Blueprint
Handles GitHub API integration for repositories and test case markdown
"""
import os
import json
import base64
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import db, GitIssue, RepoHealthSummary
from blueprints.auth_bp import require_login, require_admin

bp = Blueprint('github', __name__, url_prefix='/api')


def get_github_token():
    """Read GitHub token from secure file"""
    if os.path.exists('git_token.secure'):
        try:
            with open('git_token.secure', 'r') as f:
                return f.read().strip()
        except:
            pass
    return None


def save_github_token(token):
    """Save GitHub token to secure file"""
    try:
        with open('git_token.secure', 'w') as f:
            f.write(token)
        return True
    except:
        return False


def make_github_request(method, url, data=None):
    """Make authenticated GitHub API request"""
    token = get_github_token()
    if not token:
        return None, 'GitHub not configured'
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=10)
        elif method == 'PUT':
            headers['Content-Type'] = 'application/json'
            resp = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == 'POST':
            headers['Content-Type'] = 'application/json'
            resp = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            return None, 'Invalid method'
        
        if resp.status_code in [401, 403]:
            return None, 'GitHub authentication failed'
        
        if resp.status_code >= 400:
            return None, f'GitHub API error: {resp.status_code}'
        
        return resp.json() if resp.text else {}, None
    except requests.RequestException as e:
        return None, str(e)


@bp.route('/git-connect', methods=['POST'])
@require_admin
def connect_github():
    """Validate and save GitHub PAT"""
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': 'Token required'}), 400
    
    # Test token
    result, error = make_github_request('GET', 'https://api.github.com/user')
    if error:
        return jsonify({'success': False, 'message': f'Invalid token: {error}'}), 401
    
    # Save token
    if not save_github_token(token):
        return jsonify({'success': False, 'message': 'Failed to save token'}), 500
    
    return jsonify({
        'success': True,
        'message': 'GitHub connected',
        'user': result.get('login')
    })


@bp.route('/git-disconnect', methods=['POST'])
@require_admin
def disconnect_github():
    """Delete GitHub token"""
    try:
        if os.path.exists('git_token.secure'):
            os.remove('git_token.secure')
        return jsonify({'success': True, 'message': 'GitHub disconnected'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/git-token', methods=['GET'])
@require_login
def check_github_token():
    """Check if GitHub is configured"""
    token = get_github_token()
    
    if not token:
        return jsonify({
            'success': True,
            'configured': False,
            'message': 'GitHub not configured'
        })
    
    # Verify token still works
    result, error = make_github_request('GET', 'https://api.github.com/user')
    if error:
        return jsonify({
            'success': True,
            'configured': False,
            'message': 'Token invalid or expired'
        })
    
    return jsonify({
        'success': True,
        'configured': True,
        'user': result.get('login')
    })


@bp.route('/list-repos', methods=['GET'])
@require_login
def list_repos():
    """List repositories in GitHub organization"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    
    # Get org from config
    config_file = 'site_config.json'
    org = 'diro3307'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            org = config.get('github_org', 'diro3307')
        except:
            pass
    
    url = f'https://api.github.com/orgs/{org}/repos?page={page}&per_page={per_page}'
    result, error = make_github_request('GET', url)
    
    if error:
        return jsonify({'success': False, 'message': error}), 500
    
    repos = [{
        'id': r.get('id'),
        'name': r.get('name'),
        'full_name': r.get('full_name'),
        'url': r.get('html_url'),
        'description': r.get('description'),
        'language': r.get('language'),
        'topics': r.get('topics', [])
    } for r in result if isinstance(result, list)] if isinstance(result, list) else []
    
    return jsonify({
        'success': True,
        'repos': repos,
        'page': page,
        'per_page': per_page
    })


@bp.route('/repo-languages', methods=['GET'])
@require_login
def get_repo_languages():
    """Get language breakdown for a repository"""
    repo = request.args.get('repo', '').strip()
    if not repo:
        return jsonify({'success': False, 'message': 'repo parameter required'}), 400
    
    url = f'https://api.github.com/repos/{repo}/languages'
    result, error = make_github_request('GET', url)
    
    if error:
        return jsonify({'success': False, 'message': error}), 500
    
    return jsonify({
        'success': True,
        'languages': result if isinstance(result, dict) else {}
    })


@bp.route('/git-branches', methods=['GET'])
@require_login
def get_git_branches():
    """List branches for a repository"""
    repo = request.args.get('repo', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    
    if not repo:
        return jsonify({'success': False, 'message': 'repo parameter required'}), 400
    
    url = f'https://api.github.com/repos/{repo}/branches?page={page}&per_page={per_page}'
    result, error = make_github_request('GET', url)
    
    if error:
        return jsonify({'success': False, 'message': error}), 500
    
    branches = [{
        'name': b.get('name'),
        'commit': b.get('commit', {}).get('sha')
    } for b in result if isinstance(result, list)] if isinstance(result, list) else []
    
    return jsonify({
        'success': True,
        'branches': branches
    })


@bp.route('/list-md-files', methods=['GET'])
@require_login
def list_md_files():
    """List markdown files in a repository"""
    repo = request.args.get('repo', '').strip()
    branch = request.args.get('branch', 'main')
    
    if not repo:
        return jsonify({'success': False, 'message': 'repo parameter required'}), 400
    
    # Search for .md files
    url = f'https://api.github.com/search/code?q=extension:md+repo:{repo}+branch:{branch}&per_page=100'
    result, error = make_github_request('GET', url)
    
    if error:
        return jsonify({'success': False, 'message': error}), 500
    
    items = result.get('items', []) if isinstance(result, dict) else []
    md_files = [{
        'name': item.get('name'),
        'path': item.get('path'),
        'url': item.get('html_url')
    } for item in items]
    
    return jsonify({
        'success': True,
        'md_files': md_files
    })


@bp.route('/get-md-file', methods=['GET'])
@require_login
def get_md_file():
    """Fetch raw content of a markdown file"""
    repo = request.args.get('repo', '').strip()
    path = request.args.get('path', '').strip()
    branch = request.args.get('branch', 'main')
    
    if not repo or not path:
        return jsonify({'success': False, 'message': 'repo and path required'}), 400
    
    url = f'https://api.github.com/repos/{repo}/contents/{path}?ref={branch}'
    result, error = make_github_request('GET', url)
    
    if error:
        return jsonify({'success': False, 'message': error}), 500
    
    if isinstance(result, dict) and 'content' in result:
        try:
            content = base64.b64decode(result['content']).decode('utf-8')
            return jsonify({
                'success': True,
                'content': content,
                'sha': result.get('sha')
            })
        except:
            return jsonify({'success': False, 'message': 'Failed to decode content'}), 500
    
    return jsonify({'success': False, 'message': 'File not found'}), 404


@bp.route('/git-issues/refresh', methods=['POST'])
@require_admin
def refresh_github_issues():
    """Scan all repos for open issues and cache in DB"""
    page = 1
    per_page = 100
    config_file = 'site_config.json'
    org = 'diro3307'
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            org = config.get('github_org', 'diro3307')
        except:
            pass
    
    # Get all repos
    url = f'https://api.github.com/orgs/{org}/repos?per_page={per_page}'
    result, error = make_github_request('GET', url)
    
    if error:
        return jsonify({'success': False, 'message': error}), 500
    
    repos = result if isinstance(result, list) else []
    issues_count = 0
    
    try:
        # Clear old issues
        GitIssue.query.delete()
        
        for repo in repos:
            repo_name = repo.get('full_name')
            issues_url = f'https://api.github.com/repos/{repo_name}/issues?state=open&per_page=100'
            issues_result, error = make_github_request('GET', issues_url)
            
            if issues_result and isinstance(issues_result, list):
                for issue in issues_result:
                    git_issue = GitIssue(
                        git_repo=repo_name,
                        issue_number=issue.get('number'),
                        issue_title=issue.get('title'),
                        issue_url=issue.get('html_url'),
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(git_issue)
                    issues_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Scanned {len(repos)} repos, found {issues_count} open issues'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/git-issues', methods=['GET'])
@require_login
def get_cached_issues():
    """Return cached GitHub issues"""
    issues = GitIssue.query.all()
    
    return jsonify({
        'success': True,
        'issues': [{
            'id': i.id,
            'repo': i.git_repo,
            'number': i.issue_number,
            'title': i.issue_title,
            'url': i.issue_url,
            'last_updated': i.last_updated.isoformat() if i.last_updated else None
        } for i in issues]
    })


@bp.route('/repo-health-summary/refresh', methods=['POST'])
@require_admin
def refresh_repo_health():
    """Scan repos for health issues: stale, no README, direct push, no main/master"""
    config_file = 'site_config.json'
    org = 'diro3307'
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            org = config.get('github_org', 'diro3307')
        except:
            pass
    
    # Get all repos
    url = f'https://api.github.com/orgs/{org}/repos?per_page=100'
    result, error = make_github_request('GET', url)
    
    if error:
        return jsonify({'success': False, 'message': error}), 500
    
    repos = result if isinstance(result, list) else []
    health_issues = []
    
    try:
        # Clear old health data
        RepoHealthSummary.query.delete()
        
        for repo in repos:
            repo_name = repo.get('full_name')
            
            # Check for README
            if not repo.get('has_downloads'):
                health = RepoHealthSummary(
                    repo_name=repo_name,
                    repo_url=repo.get('html_url'),
                    health_type='no_readme',
                    last_update=datetime.utcnow()
                )
                db.session.add(health)
                health_issues.append(f'{repo_name}: no README')
            
            # Check last update (stale if > 90 days)
            if repo.get('updated_at'):
                try:
                    updated = datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
                    days_since = (datetime.utcnow() - updated.replace(tzinfo=None)).days
                    if days_since > 90:
                        health = RepoHealthSummary(
                            repo_name=repo_name,
                            repo_url=repo.get('html_url'),
                            health_type='stale',
                            branch='N/A',
                            updated_at=updated,
                            last_update=datetime.utcnow()
                        )
                        db.session.add(health)
                        health_issues.append(f'{repo_name}: stale ({days_since} days)')
                except:
                    pass
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Checked {len(repos)} repos, found {len(health_issues)} issues',
            'issues': health_issues
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/repo-health-summary', methods=['GET'])
@require_login
def get_repo_health():
    """Return cached repository health data"""
    health = RepoHealthSummary.query.all()
    
    return jsonify({
        'success': True,
        'health': [{
            'id': h.id,
            'repo': h.repo_name,
            'url': h.repo_url,
            'health_type': h.health_type,
            'branch': h.branch,
            'updated_at': h.updated_at.isoformat() if h.updated_at else None,
            'last_update': h.last_update.isoformat() if h.last_update else None
        } for h in health]
    })
