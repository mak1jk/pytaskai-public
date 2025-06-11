#!/usr/bin/env python3
"""
PyTaskAI Codebase Analysis Script
Conducts baseline analysis of current codebase structure and complexity.
"""

import os
import ast
import subprocess
from collections import defaultdict, Counter
from pathlib import Path
import json

def map_module_responsibilities():
    """Map module responsibilities across the codebase."""
    print("=== MODULE RESPONSIBILITIES MAP ===\n")
    
    modules = defaultdict(list)
    
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and cache
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py') and not file.startswith('.'):
                path = os.path.join(root, file)
                rel_path = path.replace('./', '')
                
                # Categorize by directory
                if '/' in rel_path:
                    category = rel_path.split('/')[0]
                else:
                    category = 'root'
                    
                modules[category].append(rel_path)
    
    for category, files in sorted(modules.items()):
        print(f"{category.upper()}:")
        for f in sorted(files):
            print(f"  - {f}")
        print()
    
    return modules

def analyze_dependencies():
    """Analyze import dependencies between modules."""
    print("=== DEPENDENCY GRAPH ANALYSIS ===\n")
    
    dependencies = defaultdict(set)
    external_deps = Counter()
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    module_name = filepath.replace('./', '').replace('.py', '').replace('/', '.')
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name.startswith(('.', 'mcp_server', 'shared', 'frontend', 'tests')):
                                    dependencies[module_name].add(alias.name)
                                else:
                                    external_deps[alias.name] += 1
                                    
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                if node.module.startswith(('.', 'mcp_server', 'shared', 'frontend', 'tests')):
                                    dependencies[module_name].add(node.module)
                                else:
                                    external_deps[node.module] += 1
                                    
                except Exception as e:
                    print(f"Warning: Could not parse {filepath}: {e}")
    
    print("INTERNAL DEPENDENCIES:")
    for module, deps in sorted(dependencies.items()):
        if deps:
            print(f"  {module}:")
            for dep in sorted(deps):
                print(f"    -> {dep}")
    
    print(f"\nTOP EXTERNAL DEPENDENCIES:")
    for dep, count in external_deps.most_common(10):
        print(f"  {dep}: {count} imports")
    
    return dependencies, external_deps

def measure_complexity():
    """Measure code complexity using basic metrics."""
    print("\n=== CODE COMPLEXITY METRICS ===\n")
    
    metrics = {
        'total_files': 0,
        'total_lines': 0,
        'total_functions': 0,
        'total_classes': 0,
        'file_metrics': {}
    }
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    tree = ast.parse(content)
                    
                    functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                    classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                    
                    metrics['total_files'] += 1
                    metrics['total_lines'] += len(lines)
                    metrics['total_functions'] += functions
                    metrics['total_classes'] += classes
                    
                    metrics['file_metrics'][filepath] = {
                        'lines': len(lines),
                        'functions': functions,
                        'classes': classes
                    }
                    
                except Exception as e:
                    print(f"Warning: Could not analyze {filepath}: {e}")
    
    print(f"Total Python files: {metrics['total_files']}")
    print(f"Total lines of code: {metrics['total_lines']}")
    print(f"Total functions: {metrics['total_functions']}")
    print(f"Total classes: {metrics['total_classes']}")
    print(f"Average lines per file: {metrics['total_lines'] / max(metrics['total_files'], 1):.1f}")
    
    # Show largest files
    largest_files = sorted(metrics['file_metrics'].items(), 
                          key=lambda x: x[1]['lines'], reverse=True)[:5]
    
    print(f"\nLARGEST FILES:")
    for filepath, file_metrics in largest_files:
        print(f"  {filepath}: {file_metrics['lines']} lines, "
              f"{file_metrics['functions']} functions, {file_metrics['classes']} classes")
    
    return metrics

def check_tools_available():
    """Check if complexity analysis tools are available."""
    tools = {}
    
    # Check for radon
    try:
        result = subprocess.run(['radon', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            tools['radon'] = True
        else:
            tools['radon'] = False
    except:
        tools['radon'] = False
    
    return tools

def run_radon_analysis():
    """Run radon complexity analysis if available."""
    tools = check_tools_available()
    
    if tools.get('radon'):
        print("\n=== RADON COMPLEXITY ANALYSIS ===\n")
        
        try:
            # Cyclomatic complexity
            result = subprocess.run(['radon', 'cc', '.', '--show-complexity'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("CYCLOMATIC COMPLEXITY:")
                print(result.stdout)
            
            # Maintainability index
            result = subprocess.run(['radon', 'mi', '.'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("MAINTAINABILITY INDEX:")
                print(result.stdout)
                
        except Exception as e:
            print(f"Error running radon: {e}")
    else:
        print("\n=== RADON NOT AVAILABLE ===")
        print("Install with: pip install radon")
        print("Would provide:")
        print("  - Cyclomatic complexity metrics")
        print("  - Maintainability index")
        print("  - Raw metrics (LOC, LLOC, SLOC)")

def establish_kpis():
    """Establish baseline KPIs for the project."""
    print("\n=== BASELINE KPIs ESTABLISHED ===\n")
    
    kpis = {
        'code_quality': {
            'target_test_coverage': '85%',
            'max_cyclomatic_complexity': 10,
            'min_maintainability_index': 70,
            'max_lines_per_file': 500
        },
        'architecture': {
            'max_dependencies_per_module': 15,
            'max_circular_dependencies': 0,
            'target_module_cohesion': 'high'
        },
        'performance': {
            'max_task_creation_time': '2s',
            'max_cli_response_time': '1s',
            'max_ai_call_timeout': '30s'
        },
        'maintainability': {
            'max_technical_debt_ratio': '10%',
            'min_documentation_coverage': '80%',
            'max_code_duplication': '5%'
        }
    }
    
    for category, metrics in kpis.items():
        print(f"{category.upper()}:")
        for metric, target in metrics.items():
            print(f"  {metric}: {target}")
        print()
    
    return kpis

def save_analysis_results(modules, dependencies, external_deps, metrics, kpis):
    """Save analysis results to JSON file."""
    results = {
        'timestamp': str(Path('.').absolute()),
        'module_map': dict(modules),
        'dependency_count': len(dependencies),
        'external_dependencies': dict(external_deps.most_common(20)),
        'complexity_metrics': metrics,
        'baseline_kpis': kpis
    }
    
    output_file = '.pytaskai/baseline_analysis.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis results saved to: {output_file}")

def main():
    """Run complete baseline analysis."""
    print("PyTaskAI Codebase Baseline Analysis")
    print("=" * 50)
    
    # Map module responsibilities
    modules = map_module_responsibilities()
    
    # Analyze dependencies
    dependencies, external_deps = analyze_dependencies()
    
    # Measure complexity
    metrics = measure_complexity()
    
    # Run radon if available
    run_radon_analysis()
    
    # Establish KPIs
    kpis = establish_kpis()
    
    # Save results
    save_analysis_results(modules, dependencies, external_deps, metrics, kpis)
    
    print("\n=== ANALYSIS COMPLETE ===")
    print("Baseline metrics established for PyTaskAI project.")

if __name__ == '__main__':
    main()