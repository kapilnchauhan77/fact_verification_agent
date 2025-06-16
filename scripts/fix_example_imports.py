#!/usr/bin/env python3
"""
Script to fix imports in examples and scripts for the new structure
"""

import os
import re
from pathlib import Path

def fix_example_import(file_path):
    """Fix imports in example/script files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already has the path setup
        if 'sys.path.insert' in content:
            return False
            
        # Find the first import from src.fact_check_agent
        import_match = re.search(r'(from src\.fact_check_agent\.[^\s]+ import [^\n]+)', content)
        if not import_match:
            return False
        
        # Create the path setup code
        path_setup = '''import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

'''
        
        # Find where to insert the path setup (before first src import)
        first_src_import = import_match.start()
        
        # Find the last import before the src import
        lines_before = content[:first_src_import].split('\n')
        
        # Find where imports start
        import_start = 0
        for i, line in enumerate(lines_before):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_start = sum(len(l) + 1 for l in lines_before[:i])
                break
        
        # Insert path setup before src imports
        content = content[:import_start] + path_setup + content[import_start:]
        
        # Replace src.fact_check_agent imports with fact_check_agent
        content = re.sub(r'from src\.fact_check_agent\.', 'from fact_check_agent.', content)
        content = re.sub(r'import src\.fact_check_agent\.', 'import fact_check_agent.', content)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Fixed {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Fix imports in examples and scripts"""
    project_root = Path(__file__).parent.parent
    
    # Process examples and scripts
    dirs_to_fix = ['examples', 'scripts']
    
    for dir_name in dirs_to_fix:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue
            
        print(f"🔧 Processing {dir_name}/")
        
        for py_file in dir_path.glob('*.py'):
            if py_file.name in ['__init__.py', 'fix_imports.py', 'fix_example_imports.py']:
                continue
                
            fix_example_import(py_file)

if __name__ == "__main__":
    main()