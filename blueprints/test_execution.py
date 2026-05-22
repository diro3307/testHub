"""
TestHUB QE Portal - Test Execution Blueprint
Handles test execution runs and results tracking
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from models import db, TestCase, TestExecutionRun, TestStepResult, TestStep
from blueprints.auth_bp import require_login

bp = Blueprint('test_execution', __name__, url_prefix='/api')


@bp.route('/test-execution/run', methods=['POST'])
@require_login
def create_execution_run():
    """Create test execution run(s) for test case(s)"""
    data = request.get_json() or {}
    
    test_case_ids = data.get('test_case_ids', [])
    status = data.get('status', 'Pass')
    executed_by = data.get('executed_by', 'system')
    environment = data.get('environment', 'QA')
    notes = data.get('notes', '')
    bug_id = data.get('bug_id', '')
    sharepoint_link = data.get('sharepoint_link', '')
    na_comment = data.get('na_comment', '')
    
    if not test_case_ids or not isinstance(test_case_ids, list):
        return jsonify({'success': False, 'message': 'test_case_ids array required'}), 400
    
    if status not in ['Pass', 'Fail', 'Blocked', 'NA', 'In Progress', 'No Run']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    created_runs = []
    
    try:
        for tc_id in test_case_ids:
            test_case = TestCase.query.get(tc_id)
            if not test_case:
                continue
            
            # Get next run number
            last_run = TestExecutionRun.query.filter_by(test_case_id=tc_id).order_by(
                TestExecutionRun.run_number.desc()
            ).first()
            run_number = (last_run.run_number + 1) if last_run else 1
            
            # Create execution run
            run = TestExecutionRun(
                test_case_id=tc_id,
                run_number=run_number,
                executed_by=executed_by,
                executed_on=datetime.utcnow(),
                overall_status=status,
                environment=environment,
                notes=notes,
                bug_id=bug_id if status == 'Fail' else None,
                sharepoint_link=sharepoint_link if status == 'Pass' else None,
                na_comment=na_comment if status == 'NA' else None
            )
            db.session.add(run)
            db.session.flush()
            
            # Create step results if steps exist
            if test_case.steps:
                for step in test_case.steps:
                    step_result = TestStepResult(
                        run_id=run.id,
                        step_id=step.id,
                        status=status,
                        actual_result='',
                        bug_id=None,
                        notes=''
                    )
                    db.session.add(step_result)
            
            created_runs.append({
                'test_case_id': tc_id,
                'run_id': run.id,
                'run_number': run_number,
                'tc_id': test_case.tc_id
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Created {len(created_runs)} execution run(s)',
            'runs': created_runs
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/test-execution/history/<int:test_case_id>', methods=['GET'])
@require_login
def get_execution_history(test_case_id):
    """Get full execution history for a test case"""
    test_case = TestCase.query.get(test_case_id)
    if not test_case:
        return jsonify({'success': False, 'message': 'Test case not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    runs = TestExecutionRun.query.filter_by(test_case_id=test_case_id).order_by(
        TestExecutionRun.executed_on.desc()
    ).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'test_case_id': test_case_id,
        'test_case_name': test_case.name,
        'history': [
            {
                'id': run.id,
                'run_number': run.run_number,
                'executed_by': run.executed_by,
                'executed_on': run.executed_on.isoformat(),
                'overall_status': run.overall_status,
                'environment': run.environment,
                'notes': run.notes,
                'bug_id': run.bug_id,
                'sharepoint_link': run.sharepoint_link,
                'na_comment': run.na_comment,
                'step_results': [
                    {
                        'step_number': sr.step.step_number if sr.step else None,
                        'status': sr.status,
                        'actual_result': sr.actual_result,
                        'bug_id': sr.bug_id,
                        'notes': sr.notes
                    }
                    for sr in run.step_results
                ]
            }
            for run in runs.items
        ],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': runs.total,
            'pages': runs.pages
        }
    })


@bp.route('/test-execution/summary', methods=['GET'])
@require_login
def get_execution_summary():
    """Get execution summary for an application"""
    app_id = request.args.get('application_id', type=int)
    
    if not app_id:
        return jsonify({'success': False, 'message': 'application_id required'}), 400
    
    # Get all test cases for application
    from models import TestApplication
    app = TestApplication.query.get(app_id)
    if not app:
        return jsonify({'success': False, 'message': 'Application not found'}), 404
    
    test_cases = TestCase.query.filter_by(application_id=app_id).all()
    
    # Count by latest status
    statuses = {}
    for tc in test_cases:
        last_run = TestExecutionRun.query.filter_by(test_case_id=tc.id).order_by(
            TestExecutionRun.executed_on.desc()
        ).first()
        
        status = last_run.overall_status if last_run else 'No Run'
        statuses[status] = statuses.get(status, 0) + 1
    
    return jsonify({
        'success': True,
        'application_id': app_id,
        'total': len(test_cases),
        'pass': statuses.get('Pass', 0),
        'fail': statuses.get('Fail', 0),
        'blocked': statuses.get('Blocked', 0),
        'na': statuses.get('NA', 0),
        'in_progress': statuses.get('In Progress', 0),
        'no_run': statuses.get('No Run', 0),
        'by_status': statuses
    })


@bp.route('/test-execution/run/<int:run_id>', methods=['GET'])
@require_login
def get_execution_run(run_id):
    """Get specific execution run details"""
    run = TestExecutionRun.query.get(run_id)
    if not run:
        return jsonify({'success': False, 'message': 'Execution run not found'}), 404
    
    return jsonify({
        'success': True,
        'run': {
            'id': run.id,
            'test_case_id': run.test_case_id,
            'run_number': run.run_number,
            'executed_by': run.executed_by,
            'executed_on': run.executed_on.isoformat(),
            'overall_status': run.overall_status,
            'environment': run.environment,
            'notes': run.notes,
            'bug_id': run.bug_id,
            'sharepoint_link': run.sharepoint_link,
            'na_comment': run.na_comment,
            'step_results': [
                {
                    'id': sr.id,
                    'step_id': sr.step_id,
                    'step_number': sr.step.step_number if sr.step else None,
                    'status': sr.status,
                    'actual_result': sr.actual_result,
                    'bug_id': sr.bug_id,
                    'notes': sr.notes
                }
                for sr in run.step_results
            ]
        }
    })


@bp.route('/test-execution/run/<int:run_id>', methods=['PUT'])
@require_login
def update_execution_run(run_id):
    """Update execution run"""
    run = TestExecutionRun.query.get(run_id)
    if not run:
        return jsonify({'success': False, 'message': 'Execution run not found'}), 404
    
    data = request.get_json() or {}
    
    if 'overall_status' in data:
        run.overall_status = data['overall_status']
    if 'notes' in data:
        run.notes = data['notes']
    if 'bug_id' in data:
        run.bug_id = data['bug_id']
    if 'sharepoint_link' in data:
        run.sharepoint_link = data['sharepoint_link']
    if 'na_comment' in data:
        run.na_comment = data['na_comment']
    if 'environment' in data:
        run.environment = data['environment']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Execution run updated'
    })


@bp.route('/test-execution/run/<int:run_id>', methods=['DELETE'])
@require_login
def delete_execution_run(run_id):
    """Delete execution run"""
    run = TestExecutionRun.query.get(run_id)
    if not run:
        return jsonify({'success': False, 'message': 'Execution run not found'}), 404
    
    try:
        db.session.delete(run)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Execution run deleted'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/test-execution/stats', methods=['GET'])
@require_login
def get_execution_stats():
    """Get portal-wide execution statistics"""
    
    # Total runs
    total_runs = TestExecutionRun.query.count()
    
    # By status
    status_counts = db.session.query(
        TestExecutionRun.overall_status,
        db.func.count(TestExecutionRun.id)
    ).group_by(TestExecutionRun.overall_status).all()
    
    stats = {
        'total_runs': total_runs,
        'by_status': {status: count for status, count in status_counts}
    }
    
    return jsonify({
        'success': True,
        'stats': stats
    })
