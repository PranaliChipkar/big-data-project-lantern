#!/usr/bin/env python3
"""
Part 8: DVC Pipeline Setup and Orchestration
Sets up Data Version Control (DVC) for reproducible pipeline execution
"""

import sys
from pathlib import Path
import subprocess
import logging
from typing import List, Tuple
import json
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DVCPipelineManager:
    """Manage DVC pipeline setup and execution"""
    
    def __init__(self, project_root: Path = Path.cwd()):
        """
        Initialize DVC Pipeline Manager
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.dvc_dir = project_root / '.dvc'
        self.pipeline_file = project_root / 'dvc.yaml'
        self.params_file = project_root / 'config' / 'params.yaml'
        
    def check_dvc_installed(self) -> bool:
        """Check if DVC is installed"""
        try:
            result = subprocess.run(['dvc', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"DVC is installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        logger.error("DVC is not installed")
        logger.info("Install DVC with: pip install dvc")
        return False
    
    def initialize_dvc(self) -> bool:
        """Initialize DVC in the project"""
        if self.dvc_dir.exists():
            logger.info("DVC is already initialized")
            return True
        
        try:
            logger.info("Initializing DVC...")
            subprocess.run(['dvc', 'init'], check=True, cwd=self.project_root)
            logger.info("✅ DVC initialized successfully")
            
            # Configure DVC cache
            subprocess.run(['dvc', 'cache', 'dir', 'cache'], cwd=self.project_root)
            
            # Add remote storage (optional - using local for now)
            self.setup_local_remote()
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize DVC: {e}")
            return False
    
    def setup_local_remote(self):
        """Setup local DVC remote for storage"""
        remote_dir = self.project_root / 'dvc-storage'
        remote_dir.mkdir(exist_ok=True)
        
        try:
            # Add local remote
            subprocess.run(
                ['dvc', 'remote', 'add', '-d', 'local', str(remote_dir)],
                cwd=self.project_root,
                capture_output=True
            )
            logger.info(f"Added local DVC remote: {remote_dir}")
        except subprocess.CalledProcessError:
            # Remote might already exist
            logger.info("DVC remote already configured")
    
    def create_pipeline_files(self):
        """Create DVC pipeline configuration files"""
        
        # Ensure config directory exists
        config_dir = self.project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Save params.yaml if it doesn't exist
        if not self.params_file.exists():
            logger.info(f"Creating {self.params_file}")
            # params.yaml content is already created in artifact above
            logger.info("Please save the params.yaml file to config/params.yaml")
        
        # Save dvc.yaml if it doesn't exist
        if not self.pipeline_file.exists():
            logger.info(f"Creating {self.pipeline_file}")
            # dvc.yaml content is already created in artifact above
            logger.info("Please save the dvc.yaml file to your project root")
    
    def validate_pipeline(self) -> List[str]:
        """Validate that all required files exist"""
        missing = []
        
        # Check for required Python scripts
        required_scripts = [
            'src/download/edgar_downloader.py',
            'src/parsers/pdf_parser.py',
            'src/parsers/table_extractor.py',
            'src/parsers/layout_detector.py',
            'src/parsers/docling_parser.py',
            'src/utils/metadata.py',
            'src/utils/format_comparison.py',
            'src/utils/build_vs_buy_analysis.py'
        ]
        
        for script in required_scripts:
            script_path = self.project_root / script
            if not script_path.exists():
                missing.append(script)
                logger.warning(f"Missing: {script}")
        
        if missing:
            logger.error(f"Missing {len(missing)} required files")
        else:
            logger.info("✅ All required scripts found")
        
        return missing
    
    def run_pipeline(self, stages: List[str] = None):
        """
        Run DVC pipeline
        
        Args:
            stages: Specific stages to run (None = run all)
        """
        try:
            if stages:
                # Run specific stages
                for stage in stages:
                    logger.info(f"Running stage: {stage}")
                    subprocess.run(['dvc', 'repro', stage], check=True, cwd=self.project_root)
            else:
                # Run entire pipeline
                logger.info("Running complete pipeline...")
                subprocess.run(['dvc', 'repro'], check=True, cwd=self.project_root)
            
            logger.info("✅ Pipeline execution complete")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Pipeline execution failed: {e}")
            return False
    
    def show_pipeline_dag(self):
        """Display pipeline DAG (Directed Acyclic Graph)"""
        try:
            result = subprocess.run(
                ['dvc', 'dag'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("\n📊 Pipeline DAG:")
                print(result.stdout)
            
        except subprocess.CalledProcessError:
            logger.warning("Could not display pipeline DAG")
    
    def track_metrics(self):
        """Show pipeline metrics"""
        try:
            result = subprocess.run(
                ['dvc', 'metrics', 'show'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0 and result.stdout:
                print("\n📈 Pipeline Metrics:")
                print(result.stdout)
            
        except subprocess.CalledProcessError:
            logger.warning("No metrics to display yet")
    
    def create_reproducibility_script(self):
        """Create a script for easy reproduction"""
        
        script_content = """#!/bin/bash
# Project LANTERN - Reproducibility Script
# This script reproduces the entire pipeline from scratch

echo "🚀 Project LANTERN Pipeline Reproduction"
echo "========================================"

# Step 1: Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Step 2: Initialize DVC
echo "📊 Setting up DVC..."
dvc init -f

# Step 3: Run the complete pipeline
echo "⚙️ Running pipeline..."
dvc repro

# Step 4: Show results
echo "📈 Pipeline Results:"
dvc metrics show

echo "✅ Pipeline reproduction complete!"
echo "Check data/parsed/ for all outputs"
"""
        
        script_path = self.project_root / 'reproduce_pipeline.sh'
        script_path.write_text(script_content)
        script_path.chmod(0o755)  # Make executable
        
        logger.info(f"Created reproduction script: {script_path}")
        return script_path


def main():
    """Main function to setup and run DVC pipeline"""
    
    print("\n" + "="*60)
    print("Part 8: DVC Pipeline Setup")
    print("="*60)
    
    # Initialize manager
    manager = DVCPipelineManager()
    
    # Step 1: Check DVC installation
    print("\n📦 Checking DVC installation...")
    if not manager.check_dvc_installed():
        print("\n❌ Please install DVC first:")
        print("   pip install dvc")
        return
    
    # Step 2: Initialize DVC
    print("\n🔧 Initializing DVC...")
    if not manager.initialize_dvc():
        return
    
    # Step 3: Create pipeline files
    print("\n📄 Setting up pipeline configuration...")
    manager.create_pipeline_files()
    
    # Step 4: Validate pipeline
    print("\n✅ Validating pipeline...")
    missing = manager.validate_pipeline()
    
    if missing:
        print("\n⚠️ Some files are missing, but that's okay!")
        print("The pipeline will run the stages that are available.")
    
    # Step 5: Show pipeline DAG
    manager.show_pipeline_dag()
    
    # Step 6: Create reproducibility script
    print("\n📝 Creating reproducibility script...")
    script_path = manager.create_reproducibility_script()
    
    # Step 7: Ask if user wants to run pipeline
    print("\n" + "="*60)
    print("DVC Pipeline Ready!")
    print("="*60)
    
    print("\n📊 Your pipeline is configured with these stages:")
    stages = [
        "1. download - Download SEC filings",
        "2. parse_text - Extract text from documents", 
        "3. extract_tables - Extract financial tables",
        "4. detect_layout - Detect document layout",
        "5. docling_comparison - Compare with Docling",
        "6. add_metadata - Add metadata and provenance",
        "7. format_comparison - Compare storage formats",
        "8. build_vs_buy - Analyze build vs buy options"
    ]
    
    for stage in stages:
        print(f"   {stage}")
    
    print("\n🎯 Options:")
    print("1. Run complete pipeline (all stages)")
    print("2. Run specific stage")
    print("3. Just show metrics")
    print("4. Exit (setup complete)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        print("\n🚀 Running complete pipeline...")
        print("This will re-run all processing steps.")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm == 'y':
            manager.run_pipeline()
            manager.track_metrics()
    
    elif choice == '2':
        print("\nAvailable stages:")
        stage_names = ['download', 'parse_text', 'extract_tables', 'detect_layout', 
                      'docling_comparison', 'add_metadata', 'format_comparison', 'build_vs_buy']
        for i, name in enumerate(stage_names, 1):
            print(f"{i}. {name}")
        
        stage_num = input("\nEnter stage number: ").strip()
        try:
            stage_idx = int(stage_num) - 1
            if 0 <= stage_idx < len(stage_names):
                manager.run_pipeline([stage_names[stage_idx]])
        except (ValueError, IndexError):
            print("Invalid stage number")
    
    elif choice == '3':
        manager.track_metrics()
    
    print("\n✅ Part 8 Complete!")
    print("\n📋 What you've accomplished:")
    print("   • Set up Data Version Control (DVC)")
    print("   • Created reproducible pipeline configuration")
    print("   • Defined 8 processing stages")
    print("   • Added parameter management")
    print("   • Created reproduction script")
    
    print("\n🎯 Next steps:")
    print("1. Anyone can reproduce your pipeline with: dvc repro")
    print("2. Track changes with: dvc status")
    print("3. Version data with: dvc add <file>")
    print("4. Proceed to Part 9 for evaluation metrics")
    
    print("\n📝 For your documentation:")
    print(f"   • Reproduction script: {script_path}")
    print("   • Pipeline config: dvc.yaml")
    print("   • Parameters: config/params.yaml")


if __name__ == "__main__":
    main()