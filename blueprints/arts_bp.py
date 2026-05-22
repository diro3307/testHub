"""
TestHUB QE Portal - ART-Git Mapping Blueprint
Handles Application Release Train to Git repository mappings
"""
from flask import Blueprint, request, jsonify
from models import db, ArtGitMapping
from blueprints.auth_bp import require_login, require_admin

bp = Blueprint('arts', __name__, url_prefix='/api')


@bp.route('/art-git-mapping', methods=['GET'])
@require_login
def list_mappings():
    """List all ART-Git mappings"""
    mappings = ArtGitMapping.query.all()
    
    return jsonify({
        'success': True,
        'mappings': [
            {
                'id': m.id,
                'art_name': m.art_name,
                'git_repo': m.git_repo,
                'agile_team': m.agile_team,
                'tool': m.tool,
                'framework': m.framework,
                'languages': m.languages.split(',') if m.languages else [],
                'automation_types': m.automation_types.split(',') if m.automation_types else [],
                'smoke_job_jenkins': m.smoke_job_jenkins,
                'regression_smoke_job_jenkins': m.regression_smoke_job_jenkins,
                'last_updated': m.last_updated.isoformat() if m.last_updated else None
            }
            for m in mappings
        ]
    })


@bp.route('/art-git-mapping', methods=['POST'])
@require_admin
def create_or_update_mapping():
    """Create or update ART-Git mapping"""
    data = request.get_json() or {}
    
    git_repo = data.get('git_repo', '').strip()
    if not git_repo:
        return jsonify({'success': False, 'message': 'git_repo required'}), 400
    
    # Check if exists
    mapping = ArtGitMapping.query.filter_by(git_repo=git_repo).first()
    
    if mapping:
        # Update
        if 'art_name' in data:
            mapping.art_name = data['art_name']
        if 'agile_team' in data:
            mapping.agile_team = data['agile_team']
        if 'tool' in data:
            mapping.tool = data['tool']
        if 'framework' in data:
            mapping.framework = data['framework']
        if 'languages' in data:
            langs = data['languages']
            if isinstance(langs, list):
                mapping.languages = ','.join(langs)
            else:
                mapping.languages = langs
        if 'automation_types' in data:
            auto_types = data['automation_types']
            if isinstance(auto_types, list):
                mapping.automation_types = ','.join(auto_types)
            else:
                mapping.automation_types = auto_types
        if 'smoke_job_jenkins' in data:
            mapping.smoke_job_jenkins = data['smoke_job_jenkins']
        if 'regression_smoke_job_jenkins' in data:
            mapping.regression_smoke_job_jenkins = data['regression_smoke_job_jenkins']
    else:
        # Create
        mapping = ArtGitMapping(
            art_name=data.get('art_name', ''),
            git_repo=git_repo,
            agile_team=data.get('agile_team', ''),
            tool=data.get('tool'),
            framework=data.get('framework'),
            languages=','.join(data['languages']) if isinstance(data.get('languages'), list) else data.get('languages', ''),
            automation_types=','.join(data['automation_types']) if isinstance(data.get('automation_types'), list) else data.get('automation_types', ''),
            smoke_job_jenkins=data.get('smoke_job_jenkins'),
            regression_smoke_job_jenkins=data.get('regression_smoke_job_jenkins')
        )
        db.session.add(mapping)
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Mapping for {git_repo} saved',
            'id': mapping.id
        }), 201 if not mapping.id else 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/art-git-mapping/batch', methods=['POST'])
@require_admin
def batch_upsert_mappings():
    """Batch upsert all repository mappings"""
    data = request.get_json() or {}
    mappings_data = data.get('mappings', [])
    
    if not isinstance(mappings_data, list):
        return jsonify({'success': False, 'message': 'mappings must be a list'}), 400
    
    updated_count = 0
    created_count = 0
    
    try:
        for mapping_data in mappings_data:
            git_repo = mapping_data.get('git_repo', '').strip()
            if not git_repo:
                continue
            
            mapping = ArtGitMapping.query.filter_by(git_repo=git_repo).first()
            
            if mapping:
                # Update
                if 'art_name' in mapping_data:
                    mapping.art_name = mapping_data['art_name']
                if 'agile_team' in mapping_data:
                    mapping.agile_team = mapping_data['agile_team']
                if 'tool' in mapping_data:
                    mapping.tool = mapping_data['tool']
                if 'framework' in mapping_data:
                    mapping.framework = mapping_data['framework']
                if 'languages' in mapping_data:
                    langs = mapping_data['languages']
                    mapping.languages = ','.join(langs) if isinstance(langs, list) else langs
                if 'automation_types' in mapping_data:
                    auto_types = mapping_data['automation_types']
                    mapping.automation_types = ','.join(auto_types) if isinstance(auto_types, list) else auto_types
                if 'smoke_job_jenkins' in mapping_data:
                    mapping.smoke_job_jenkins = mapping_data['smoke_job_jenkins']
                if 'regression_smoke_job_jenkins' in mapping_data:
                    mapping.regression_smoke_job_jenkins = mapping_data['regression_smoke_job_jenkins']
                updated_count += 1
            else:
                # Create
                mapping = ArtGitMapping(
                    art_name=mapping_data.get('art_name', ''),
                    git_repo=git_repo,
                    agile_team=mapping_data.get('agile_team', ''),
                    tool=mapping_data.get('tool'),
                    framework=mapping_data.get('framework'),
                    languages=','.join(mapping_data['languages']) if isinstance(mapping_data.get('languages'), list) else mapping_data.get('languages', ''),
                    automation_types=','.join(mapping_data['automation_types']) if isinstance(mapping_data.get('automation_types'), list) else mapping_data.get('automation_types', ''),
                    smoke_job_jenkins=mapping_data.get('smoke_job_jenkins'),
                    regression_smoke_job_jenkins=mapping_data.get('regression_smoke_job_jenkins')
                )
                db.session.add(mapping)
                created_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Updated {updated_count}, created {created_count} mappings'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/art-git-mapping/<int:mapping_id>', methods=['DELETE'])
@require_admin
def delete_mapping(mapping_id):
    """Delete ART-Git mapping"""
    mapping = ArtGitMapping.query.get(mapping_id)
    if not mapping:
        return jsonify({'success': False, 'message': 'Mapping not found'}), 404
    
    repo_name = mapping.git_repo
    try:
        db.session.delete(mapping)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Mapping for {repo_name} deleted'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/agile-teams', methods=['GET'])
@require_login
def list_agile_teams():
    """List distinct agile teams"""
    teams = db.session.query(ArtGitMapping.agile_team).distinct().filter(
        ArtGitMapping.agile_team != None,
        ArtGitMapping.agile_team != ''
    ).all()
    
    return jsonify({
        'success': True,
        'teams': [t[0] for t in teams if t[0]]
    })


@bp.route('/art-names', methods=['GET'])
@require_login
def list_art_names():
    """List distinct ART names"""
    arts = db.session.query(ArtGitMapping.art_name).distinct().filter(
        ArtGitMapping.art_name != None,
        ArtGitMapping.art_name != ''
    ).all()
    
    return jsonify({
        'success': True,
        'arts': [a[0] for a in arts if a[0]]
    })
