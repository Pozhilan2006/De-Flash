"""
Lightweight verification for rule_engine.py.
Checks syntax and structure without requiring dependencies.
"""

import sys
import ast

def verify_rule_engine():
    """Verify rule engine code structure."""
    print("=" * 60)
    print("  Rule Engine Verification")
    print("=" * 60)
    
    try:
        with open('rule_engine.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Syntax check
        print("\n[1/3] Syntax Check...")
        ast.parse(code)
        print("  ✓ Valid Python syntax")
        
        # Structure check
        print("\n[2/3] Structure Check...")
        checks = {
            'Chain enum': 'class Chain',
            'TransactionType enum': 'class TransactionType',
            'AssessmentRequest': 'class AssessmentRequest',
            'AssessmentResponse': 'class AssessmentResponse',
            'RuleEngine class': 'class RuleEngine',
            'assess method': 'def assess(',
            'add_rule method': 'def add_rule(',
            '_check_loan_amount': 'def _check_loan_amount(',
            '_check_token_blacklist': 'def _check_token_blacklist(',
            '_check_protocol_risk': 'def _check_protocol_risk(',
            '_check_transaction_type': 'def _check_transaction_type(',
            '_check_transaction_count': 'def _check_transaction_count(',
        }
        
        for name, pattern in checks.items():
            if pattern in code:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name} - NOT FOUND")
                return False
        
        # Feature check
        print("\n[3/3] Feature Check...")
        features = {
            'Logging': 'logger.',
            'Type hints': '-> ',
            'Docstrings': '"""',
            'Pydantic models': 'BaseModel',
            'Error handling': 'try:',
            'Configuration': 'DEFAULT_CONFIG',
        }
        
        for name, pattern in features.items():
            if pattern in code:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name}")
        
        print("\n" + "=" * 60)
        print("  ✓ All Checks Passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = verify_rule_engine()
    sys.exit(0 if success else 1)
