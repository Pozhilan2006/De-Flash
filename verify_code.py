"""
Quick syntax and import verification test.
This test checks the code structure without requiring all dependencies.
"""

import sys
import ast

def test_syntax():
    """Test that the Python file has valid syntax."""
    print("Testing syntax...")
    try:
        with open('risk_prediction_service.py', 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print("✓ Syntax is valid")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False

def test_structure():
    """Test that key components are present."""
    print("\nTesting code structure...")
    with open('risk_prediction_service.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    checks = {
        'RiskPredictionService class': 'class RiskPredictionService',
        'LoanRequest model': 'class LoanRequest',
        'PredictionResponse model': 'class PredictionResponse',
        'predict method': 'def predict(',
        'explain_prediction method': 'def explain_prediction(',
        '_extract_features method': 'def _extract_features(',
        '_normalize method': 'def _normalize(',
        'Type hints': '-> ',
        'Docstrings': '"""',
        'Logging': 'logger.',
        'Error handling': 'try:',
        'Pydantic validation': 'BaseModel',
    }
    
    all_passed = True
    for name, pattern in checks.items():
        if pattern in code:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} - NOT FOUND")
            all_passed = False
    
    return all_passed

def test_example_structure():
    """Test example usage file structure."""
    print("\nTesting example_usage.py structure...")
    try:
        with open('example_usage.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        checks = [
            'from risk_prediction_service import',
            'def main():',
            'LoanRequest(',
            'service.predict(',
            'service.explain_prediction(',
        ]
        
        all_passed = True
        for pattern in checks:
            if pattern in code:
                print(f"  ✓ Contains: {pattern}")
            else:
                print(f"  ✗ Missing: {pattern}")
                all_passed = False
        
        return all_passed
    except FileNotFoundError:
        print("  ✗ example_usage.py not found")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("  Risk Prediction Service - Code Verification")
    print("=" * 60)
    
    results = []
    results.append(("Syntax Check", test_syntax()))
    results.append(("Structure Check", test_structure()))
    results.append(("Example Check", test_example_structure()))
    
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n✓ All verification checks passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run examples: python example_usage.py")
        print("3. Integrate into your FastAPI application")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the code.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
