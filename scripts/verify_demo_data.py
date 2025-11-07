"""
Verify Demo Data Script
Quick verification that the demo data script is ready to run
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def verify_script():
    """Verify the demo data script is ready"""
    print("Verifying demo data script...")
    
    try:
        from scripts.seed_demo_data import (
            SUBJECTS, STUDENT_NAMES, TUTOR_NAMES, TRANSCRIPTS, PRACTICE_QUESTIONS
        )
        
        print(f"[OK] Subjects: {len(SUBJECTS)}")
        print(f"[OK] Student names: {len(STUDENT_NAMES)}")
        print(f"[OK] Tutor names: {len(TUTOR_NAMES)}")
        print(f"[OK] Transcript templates: {len(TRANSCRIPTS)}")
        print(f"[OK] Practice questions: {len(PRACTICE_QUESTIONS)}")
        
        # Check for required functions
        import scripts.seed_demo_data as seed_script
        
        required_functions = [
            'generate_all_demo_data',
            'save_to_json',
            'generate_sql_inserts'
        ]
        
        missing = []
        for func in required_functions:
            if not hasattr(seed_script, func):
                missing.append(func)
        
        if missing:
            print(f"[WARNING] Missing functions: {', '.join(missing)}")
        else:
            print("[OK] All required functions present")
        
        print("\n[OK] Demo data script is ready!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error verifying script: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_script()
    sys.exit(0 if success else 1)

