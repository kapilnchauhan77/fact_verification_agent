#!/usr/bin/env python3
"""
Script to fix all import statements after refactoring
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Define the modules that need to be updated
        core_modules = [
            'authenticity_scorer', 'checkpoint_monitor', 'claim_extractor', 
            'config', 'document_processor', 'fact_check_agent', 'fact_checker', 
            'performance_monitor', 'report_generator', 'security_manager',
            'advanced_evidence_analyzer', 'custom_scrapers', 'enhanced_content_extractor',
            'intelligent_query_optimizer', 'performance_cache', 'predictive_caching_system',
            'ultra_optimized_fact_checker', 'optimized_fact_checker'
        ]
        
        # For files in src/fact_check_agent/, use relative imports
        if 'src/fact_check_agent' in str(file_path) and not str(file_path).endswith('__init__.py'):
            for module in core_modules:
                # Replace absolute imports with relative imports
                content = re.sub(
                    rf'\bfrom {module} import',
                    f'from .{module} import',
                    content
                )
                content = re.sub(
                    rf'\bimport {module}\b',
                    f'from . import {module}',
                    content
                )
        
        # For files outside src/, use absolute imports with package prefix
        elif 'src/fact_check_agent' not in str(file_path):
            for module in core_modules:
                # Replace local imports with package imports
                content = re.sub(
                    rf'\bfrom \.{module} import',
                    f'from src.fact_check_agent.{module} import',
                    content
                )
                content = re.sub(
                    rf'\bfrom {module} import',
                    f'from src.fact_check_agent.{module} import',
                    content
                )
                content = re.sub(
                    rf'\bimport {module}\b',
                    f'from src.fact_check_agent import {module}',
                    content
                )
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed imports in {file_path}")
            return True
        else:
            print(f"📄 No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Fix imports in all Python files"""
    project_root = Path(__file__).parent.parent
    print(f"🔧 Fixing imports in project: {project_root}")
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.py') and file != 'fix_imports.py':
                python_files.append(Path(root) / file)
    
    print(f"📊 Found {len(python_files)} Python files to process")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Import fixing completed!")
    print(f"📈 Fixed imports in {fixed_count} files")
    print(f"📄 Total files processed: {len(python_files)}")

if __name__ == "__main__":
    main()