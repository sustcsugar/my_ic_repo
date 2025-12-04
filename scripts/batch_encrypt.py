#!/usr/bin/env python3
# -*- coding: utf-8 -*-
################################################################################
# FILE NAME      : batch_encrypt.py
# AUTHOR         : shig
# CONTACT        : shig@fvchip.com
# CREATION DATE  : 2025-12-04
# MODIFY DATE    : 2025-12-05
# DESCRIPTION    : Batch encryption tool for Verilog/SystemVerilog files
#                  using VCS encryption commands (autoprotect/auto1protect/
#                  auto2protect/auto3protect). Features include:
#                  - Three-layer filtering (file type/exclusion/copy-only)
#                  - Directory structure preservation
#                  - Filelist generation with absolute paths
#                  - Detailed logging and reporting
################################################################################

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from datetime import datetime
import argparse


class BatchEncryptor:
    """
    Batch encryption tool class - for encrypting Verilog/SystemVerilog files
    
    Three-layer filtering mechanism:
    1. Global file type search (v, vh, sv, svh, lst)
    2. Exclusion filter - skip files/directories completely (no encryption, no copy)
    3. Copy-only filter - copy files without encryption (includes default types like .lst)
    """
    
    def __init__(self, source_dir, target_dir, log_dir=None, filelist_name=None, encrypt_method='auto3protect', exclude_files=None, exclude_dirs=None, copy_only_files=None, copy_only_dirs=None):
        """
        Initialize the encryptor
        
        Args:
            source_dir: Source project directory path
            target_dir: Encrypted file output directory path
            log_dir: Log file directory (default: current directory)
            filelist_name: Name of the filelist file to generate (optional, e.g., 'encrypted_files.lst')
            encrypt_method: VCS encryption method (default: 'auto3protect')
                           Options: 'autoprotect', 'auto1protect', 'auto2protect', 'auto3protect'
            exclude_files: List of file patterns to exclude (e.g., ['*_tb.v', 'test_*.sv'])
            exclude_dirs: List of directory patterns to exclude (e.g., ['build', 'temp', '*/test'])
            copy_only_files: List of file patterns to copy without encryption (e.g., ['*.vh', 'defines_*.svh'])
            copy_only_dirs: List of directory patterns to copy without encryption (e.g., ['include', 'defines'])
            
        Note: .lst files are automatically copied without encryption (default behavior)
        """
        self.source_dir = Path(source_dir).expanduser().resolve()
        self.target_dir = Path(target_dir).expanduser().resolve()
        self.log_dir = Path(log_dir).expanduser().resolve() if log_dir else Path.cwd()
        self.filelist_name = filelist_name
        
        # Validate and set encryption method
        valid_methods = ['autoprotect', 'auto1protect', 'auto2protect', 'auto3protect']
        if encrypt_method not in valid_methods:
            raise ValueError(f"Invalid encryption method '{encrypt_method}'. Must be one of: {valid_methods}")
        self.encrypt_method = encrypt_method
        
        # Supported file extensions
        self.supported_extensions = ['.v', '.vh', '.sv', '.svh', '.lst']
        
        # File types that should always be copied without encryption
        self.default_copy_only_extensions = ['.lst']
        
        # File and directory exclusion patterns (first level - skip completely)
        self.exclude_files = exclude_files if exclude_files else []
        self.exclude_dirs = exclude_dirs if exclude_dirs else []
        
        # File and directory copy-only patterns (second level - copy without encryption)
        self.copy_only_files = copy_only_files if copy_only_files else []
        self.copy_only_dirs = copy_only_dirs if copy_only_dirs else []
        
        # Statistics
        self.stats = {
            'total_found': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'copied_only': 0  # Files copied without encryption
        }
        
        # Lists for detailed tracking
        self.failed_files = []
        self.skipped_files = []  # Track excluded/skipped files with reasons
        self.processed_files = []  # Track successfully processed files in target directory
        self.lst_files = []  # Track .lst files (source, target) separately for filelist header
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging system - output to both file and console"""
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log filename includes timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'batch_encrypt_{timestamp}.log'
        
        # Configure log format
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Create logger
        self.logger = logging.getLogger('BatchEncryptor')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler (detailed logging)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Console handler (simplified logging)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Log file: {log_file}")
        self.logger.info(f"Encryption method: +{self.encrypt_method}")
        
    def _should_exclude_file(self, file_path):
        """
        Check if a file should be excluded based on exclusion patterns
        
        Args:
            file_path: Path object of the file to check
            
        Returns:
            tuple: (bool: should_exclude, str: reason)
        """
        from fnmatch import fnmatch
        
        # Check file name against exclusion patterns
        for pattern in self.exclude_files:
            if fnmatch(file_path.name, pattern):
                reason = f"Matched file exclusion pattern '{pattern}'"
                self.logger.debug(f"Excluding file: {file_path.name} ({reason})")
                return True, reason
        return False, None
    
    def _should_exclude_dir(self, dir_path):
        """
        Check if a directory should be excluded based on exclusion patterns
        
        Args:
            dir_path: Path object of the directory to check
            
        Returns:
            tuple: (bool: should_exclude, str: reason)
        """
        from fnmatch import fnmatch
        
        # Get relative path for pattern matching
        try:
            rel_path = dir_path.relative_to(self.source_dir)
            rel_path_str = str(rel_path)
            
            # Check directory against exclusion patterns
            for pattern in self.exclude_dirs:
                # Match against directory name or full relative path
                if fnmatch(dir_path.name, pattern) or fnmatch(rel_path_str, pattern):
                    reason = f"Matched directory exclusion pattern '{pattern}'"
                    self.logger.debug(f"Excluding directory: {rel_path_str} ({reason})")
                    return True, reason
        except ValueError:
            # Path is not relative to source_dir
            pass
            
        return False, None
        
    def _should_copy_only_file(self, file_path):
        """
        Check if a file should be copied without encryption
        
        Args:
            file_path: Path object of the file to check
            
        Returns:
            bool: True if file should be copied only (not encrypted), False otherwise
        """
        from fnmatch import fnmatch
        
        # Check if file extension is in default copy-only list (e.g., .lst files)
        if file_path.suffix in self.default_copy_only_extensions:
            self.logger.debug(f"Copy-only file (default extension '{file_path.suffix}'): {file_path.name}")
            return True
        
        # Check file name against copy-only patterns
        for pattern in self.copy_only_files:
            if fnmatch(file_path.name, pattern):
                self.logger.debug(f"Copy-only file (pattern '{pattern}'): {file_path.name}")
                return True
        return False
    
    def _should_copy_only_dir(self, dir_path):
        """
        Check if a directory should be copied without encryption
        
        Args:
            dir_path: Path object of the directory to check
            
        Returns:
            bool: True if directory should be copied only (not encrypted), False otherwise
        """
        from fnmatch import fnmatch
        
        # Get relative path for pattern matching
        try:
            rel_path = dir_path.relative_to(self.source_dir)
            rel_path_str = str(rel_path)
            
            # Check directory against copy-only patterns
            for pattern in self.copy_only_dirs:
                # Match against directory name or full relative path
                if fnmatch(dir_path.name, pattern) or fnmatch(rel_path_str, pattern):
                    self.logger.debug(f"Copy-only directory (pattern '{pattern}'): {rel_path_str}")
                    return True
        except ValueError:
            # Path is not relative to source_dir
            pass
            
        return False
        
    def validate_paths(self):
        """Validate the validity of input paths"""
        self.logger.info("=" * 80)
        self.logger.info("Starting path validation...")
        
        # Check if source directory exists
        if not self.source_dir.exists():
            self.logger.error(f"Source directory does not exist: {self.source_dir}")
            return False
            
        if not self.source_dir.is_dir():
            self.logger.error(f"Source path is not a directory: {self.source_dir}")
            return False
            
        self.logger.info(f"Source directory: {self.source_dir}")
        
        # Create target directory if it does not exist
        if self.target_dir.exists():
            self.logger.warning(f"Target directory already exists: {self.target_dir}")
            response = input("Target directory already exists. Continue? (y/n): ")
            if response.lower() != 'y':
                self.logger.info("Operation cancelled by user")
                return False
        else:
            self.logger.info(f"Creating target directory: {self.target_dir}")
            self.target_dir.mkdir(parents=True, exist_ok=True)
            
        self.logger.info("Path validation passed")
        return True
        
    def find_files(self):
        """
        Recursively find all files to be encrypted
        
        Returns:
            list: List of found file paths (Path objects)
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting search for files to encrypt...")
        
        if self.exclude_files:
            self.logger.info(f"File exclusion patterns: {self.exclude_files}")
        if self.exclude_dirs:
            self.logger.info(f"Directory exclusion patterns: {self.exclude_dirs}")
        if self.copy_only_files:
            self.logger.info(f"Copy-only file patterns: {self.copy_only_files}")
        if self.copy_only_dirs:
            self.logger.info(f"Copy-only directory patterns: {self.copy_only_dirs}")
        
        found_files = []
        excluded_count = 0
        
        for ext in self.supported_extensions:
            pattern = f"**/*{ext}"
            files = list(self.source_dir.glob(pattern))
            
            # Filter out excluded files and files in excluded directories
            for file_path in files:
                # Check if file is in an excluded directory
                should_exclude_dir = False
                exclude_reason = None
                for parent in file_path.parents:
                    if parent == self.source_dir:
                        break
                    is_excluded, reason = self._should_exclude_dir(parent)
                    if is_excluded:
                        should_exclude_dir = True
                        exclude_reason = reason
                        break
                
                if should_exclude_dir:
                    excluded_count += 1
                    rel_path = str(file_path.relative_to(self.source_dir))
                    self.skipped_files.append((rel_path, exclude_reason))
                    continue
                
                # Check if file matches exclusion pattern
                is_excluded, reason = self._should_exclude_file(file_path)
                if is_excluded:
                    excluded_count += 1
                    rel_path = str(file_path.relative_to(self.source_dir))
                    self.skipped_files.append((rel_path, reason))
                    continue
                
                found_files.append(file_path)
            
            self.logger.debug(f"Found {len([f for f in files if f in found_files])} {ext} files (excluded {len(files) - len([f for f in files if f in found_files])} files)")
            
        # Deduplicate and sort
        found_files = sorted(set(found_files))
        self.stats['total_found'] = len(found_files)
        self.stats['skipped'] = excluded_count
        
        self.logger.info(f"Total files found: {len(found_files)}")
        if excluded_count > 0:
            self.logger.info(f"Files excluded by filters: {excluded_count}")
        self.logger.info(f"File type distribution: {dict((ext, len([f for f in found_files if f.suffix == ext])) for ext in self.supported_extensions)}")
        
        return found_files
        
    def encrypt_file(self, file_path):
        """
        Encrypt a single file using VCS encryption command
        
        Args:
            file_path: File path to encrypt (Path object)
            
        Returns:
            tuple: (success: bool, encrypted_file: Path or None)
        """
        self.logger.debug(f"Encrypting file: {file_path}")
        
        # Check if file type is supported
        if file_path.suffix not in self.supported_extensions:
            self.logger.error(f"Unsupported file type: {file_path}")
            return False, None
            
        # Verilog/SystemVerilog file encryption command
        cmd = ['vcs', f'+{self.encrypt_method}', '-sverilog', str(file_path)]
            
        try:
            # Execute encryption command
            self.logger.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=file_path.parent,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Check if encryption was successful
            encrypted_file = file_path.with_suffix(file_path.suffix + 'p')
            
            if result.returncode == 0 and encrypted_file.exists():
                self.logger.debug(f"Encryption successful: {encrypted_file}")
                return True, encrypted_file
            else:
                self.logger.error(f"Encryption failed: {file_path}")
                self.logger.error(f"Return code: {result.returncode}")
                self.logger.error(f"stdout: {result.stdout}")
                self.logger.error(f"stderr: {result.stderr}")
                return False, None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Encryption timeout: {file_path}")
            return False, None
        except FileNotFoundError:
            self.logger.error("VCS command not found. Please ensure VCS is installed and in PATH")
            return False, None
        except Exception as e:
            self.logger.error(f"Encryption exception: {file_path}, error: {str(e)}")
            return False, None
            
    def copy_encrypted_file(self, source_file, encrypted_file):
        """
        Copy encrypted file to target directory, preserving original directory structure
        
        Args:
            source_file: Original file path (used to calculate relative path)
            encrypted_file: Encrypted file path
            
        Returns:
            bool: Whether copy was successful
        """
        try:
            # Calculate relative path
            rel_path = source_file.relative_to(self.source_dir)
            
            # Build target path (replace extension with .vp/.svp, etc.)
            target_file = self.target_dir / rel_path.with_suffix(encrypted_file.suffix)
            
            # Create target directory
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy encrypted file
            shutil.copy2(encrypted_file, target_file)
            
            self.logger.debug(f"Copy successful: {encrypted_file} -> {target_file}")
            
            # Track processed file (absolute path)
            self.processed_files.append(target_file.resolve())
            
            # Clean up encrypted file in source directory
            encrypted_file.unlink()
            self.logger.debug(f"Cleanup temporary file: {encrypted_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy file: {encrypted_file}, error: {str(e)}")
            return False
    
    def copy_original_file(self, source_file):
        """
        Copy original file to target directory without encryption, preserving directory structure
        
        Args:
            source_file: Original file path
            
        Returns:
            bool: Whether copy was successful
        """
        try:
            # Calculate relative path
            rel_path = source_file.relative_to(self.source_dir)
            
            # Build target path (keep original extension)
            target_file = self.target_dir / rel_path
            
            # Create target directory
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy original file
            shutil.copy2(source_file, target_file)
            
            self.logger.debug(f"Copy-only successful: {source_file} -> {target_file}")
            
            # Track .lst files separately for filelist header
            if source_file.suffix == '.lst':
                self.lst_files.append((source_file.resolve(), target_file.resolve()))
            else:
                # Track processed file (absolute path), exclude .lst files
                self.processed_files.append(target_file.resolve())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to copy original file: {source_file}, error: {str(e)}")
            return False
            
    def process_files(self, files):
        """
        Batch process file list
        
        Args:
            files: File path list
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting batch encryption processing...")
        
        total = len(files)
        
        for idx, file_path in enumerate(files, 1):
            self.logger.info(f"[{idx}/{total}] Processing: {file_path.relative_to(self.source_dir)}")
            
            # Check if file is in a copy-only directory
            should_copy_only_dir = False
            for parent in file_path.parents:
                if parent == self.source_dir:
                    break
                if self._should_copy_only_dir(parent):
                    should_copy_only_dir = True
                    break
            
            # Check if file should be copied only (without encryption)
            if should_copy_only_dir or self._should_copy_only_file(file_path):
                self.logger.info(f"  -> Copy-only (no encryption)")
                if self.copy_original_file(file_path):
                    self.stats['copied_only'] += 1
                else:
                    self.stats['failed'] += 1
                    self.failed_files.append((str(file_path), "Copy-only failed"))
                continue
            
            # Encrypt file
            success, encrypted_file = self.encrypt_file(file_path)
            
            if success and encrypted_file:
                # Copy to target directory
                if self.copy_encrypted_file(file_path, encrypted_file):
                    self.stats['success'] += 1
                else:
                    self.stats['failed'] += 1
                    self.failed_files.append((str(file_path), "Copy failed"))
            else:
                self.stats['failed'] += 1
                self.failed_files.append((str(file_path), "Encryption failed"))
    
    def generate_filelist(self):
        """
        Generate filelist file with absolute paths of all processed files in target directory
        Excludes .lst files from the list but includes them in header comments
        """
        if not self.filelist_name:
            self.logger.debug("Filelist generation skipped (no filename specified)")
            return
        
        if not self.processed_files and not self.lst_files:
            self.logger.warning("No files processed, filelist will be empty")
            return
        
        # Determine filelist path (in target directory)
        filelist_path = self.target_dir / self.filelist_name
        
        try:
            self.logger.info("=" * 80)
            self.logger.info(f"Generating filelist: {filelist_path}")
            
            # Sort files for consistent ordering
            sorted_files = sorted(self.processed_files)
            
            with open(filelist_path, 'w', encoding='utf-8') as f:
                # Write header comments
                f.write("// ###############################################################################\n")
                f.write("//  FILELIST - Batch Encryption Tool Generated File\n")
                f.write("// ###############################################################################\n")
                f.write(f"// Generation time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"// Encryption method: +{self.encrypt_method}\n")
                f.write(f"// Source directory: {self.source_dir}\n")
                f.write(f"// Target directory: {self.target_dir}\n")
                f.write(f"// Total files in list: {len(sorted_files)}\n")
                f.write("//\n")
                
                # Add .lst file information if any
                if self.lst_files:
                    f.write("// .LST FILES (excluded from this list, copied without encryption):\n")
                    for source_lst, target_lst in sorted(self.lst_files):
                        f.write(f"//   Original: {source_lst}\n")
                        f.write(f"//   Copied:   {target_lst}\n")
                    f.write("//\n")
                
                f.write("// NOTE:\n")
                f.write("//   - All paths are absolute paths\n")
                f.write("//   - Encrypted files have .vp/.svp/.vhp/.svhp extensions\n")
                f.write("//   - Copy-only files retain their original extensions\n")
                f.write("//   - .lst files are not included in this list (see above)\n")
                f.write("// ###############################################################################\n")
                f.write("\n")
                
                # Write file paths
                for file_path in sorted_files:
                    f.write(str(file_path) + '\n')
            
            self.logger.info(f"Filelist generated successfully with {len(sorted_files)} files")
            if self.lst_files:
                self.logger.info(f"Excluded {len(self.lst_files)} .lst files from filelist (listed in header)")
            self.logger.info(f"Filelist location: {filelist_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate filelist: {str(e)}")
                
    def generate_report(self):
        """Generate encryption processing report"""
        self.logger.info("=" * 80)
        self.logger.info("Encryption processing completed - Statistics Report")
        self.logger.info("=" * 80)
        self.logger.info(f"Total files discovered: {self.stats['total_found']}")
        self.logger.info(f"Successful encryption: {self.stats['success']}")
        self.logger.info(f"Copied without encryption: {self.stats['copied_only']}")
        self.logger.info(f"Failed: {self.stats['failed']}")
        self.logger.info(f"Skipped: {self.stats['skipped']}")
        self.logger.info("=" * 80)
        
        # Print skipped files list to log
        if self.skipped_files:
            self.logger.info(f"Skipped/Excluded files list ({len(self.skipped_files)} files):")
            for file_path, reason in self.skipped_files:
                self.logger.info(f"  - {file_path}: {reason}")
            self.logger.info("=" * 80)
        
        # Print failed files list to log
        if self.failed_files:
            self.logger.warning(f"Failed files list ({len(self.failed_files)} files):")
            for file_path, reason in self.failed_files:
                self.logger.warning(f"  - {file_path}: {reason}")
            self.logger.info("=" * 80)
                
        # Generate summary report file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.log_dir / f'encrypt_report_{timestamp}.log'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("Batch Encryption Processing Report\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generation time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source directory: {self.source_dir}\n")
            f.write(f"Target directory: {self.target_dir}\n")
            f.write("\n")
            f.write("Statistics:\n")
            f.write(f"  Total files discovered: {self.stats['total_found']}\n")
            f.write(f"  Successful encryption: {self.stats['success']}\n")
            f.write(f"  Copied without encryption: {self.stats['copied_only']}\n")
            f.write(f"  Failed: {self.stats['failed']}\n")
            f.write(f"  Skipped: {self.stats['skipped']}\n")
            f.write("\n")
            
            if self.skipped_files:
                f.write("Skipped/Excluded files list:\n")
                for file_path, reason in self.skipped_files:
                    f.write(f"  - {file_path}: {reason}\n")
                f.write("\n")
            
            if self.failed_files:
                f.write("Failed files list:\n")
                for file_path, reason in self.failed_files:
                    f.write(f"  - {file_path}: {reason}\n")
                    
        self.logger.info(f"Report file generated: {report_file}")
        
    def run(self):
        """Execute complete encryption workflow"""
        try:
            self.logger.info("=" * 80)
            self.logger.info("Batch encryption tool started")
            self.logger.info("=" * 80)
            
            # Validate paths
            if not self.validate_paths():
                return False
                
            # Find files
            files = self.find_files()
            if not files:
                self.logger.warning("No files to encrypt found")
                return True
                
            # Process files
            self.process_files(files)
            
            # Generate filelist if requested
            self.generate_filelist()
            
            # Generate report
            self.generate_report()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.warning("\nOperation cancelled by user")
            return False
        except Exception as e:
            self.logger.error(f"Error during execution: {str(e)}", exc_info=True)
            return False


def main():
    """Main function - parse command line arguments and execute encryption"""
    parser = argparse.ArgumentParser(
        description='Batch encryption tool for Verilog/SystemVerilog files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  # Basic usage (default: auto3protect)
  python batch_encrypt.py -s ~/work/projA -t ~/work/projA_encrypt
  
  # Specify encryption method
  python batch_encrypt.py -s ~/work/projA -t ~/work/projA_encrypt \\
      --method auto2protect
  
  # With exclusion filters
  python batch_encrypt.py -s ~/work/projA -t ~/work/projA_encrypt \\
      --exclude-files '*_tb.v' 'test_*.sv' \\
      --exclude-dirs test simv simulation
  
  # With copy-only filters
  python batch_encrypt.py -s ~/work/projA -t ~/work/projA_encrypt \\
      --copy-only-files '*.vh' '*_pkg.sv' \\
      --copy-only-dirs include defines
  
  # Complete example with all filters and filelist generation
  python batch_encrypt.py -s ~/work/projA -t ~/work/projA_encrypt \\
      --method auto3protect \\
      --exclude-files '*_tb.v' 'test_*.sv' \\
      --exclude-dirs test simulation \\
      --copy-only-files '*.vh' 'sram*.v' 'model*.v' \\
      --copy-only-dirs include defines \\
      --filelist encrypted.lst \\
      --log-dir ~/logs

Notes:
  1. VCS tool must be in PATH
  2. Target directory will be created automatically
  3. Log files are saved in the current directory by default
  4. Use quotes for patterns with wildcards (e.g., '*.vh', '*_tb.v')
  5. Filters are applied in order: exclude first, then copy-only, then encrypt
  6. Filelist contains absolute paths of all processed files in target directory
  7. Encryption methods:
     - autoprotect:  Basic encryption
     - auto1protect: Level 1 encryption
     - auto2protect: Level 2 encryption (moderate)
     - auto3protect: Level 3 encryption (highest, default)
        """
    )
    
    # Required arguments
    parser.add_argument(
        '-s', '--source',
        dest='source_dir',
        required=True,
        help='Source project directory path (e.g., ~/work/projA)'
    )
    
    parser.add_argument(
        '-t', '--target',
        dest='target_dir',
        required=True,
        help='Encrypted file output directory path (e.g., ~/work/projA_encrypt)'
    )
    
    # Optional arguments
    parser.add_argument(
        '-l', '--log-dir',
        default='.',
        help='Log file save directory (default: current directory)'
    )
    
    parser.add_argument(
        '-f', '--filelist',
        dest='filelist_name',
        default=None,
        help='Generate filelist with specified name (e.g., "encrypted_files.lst")'
    )
    
    parser.add_argument(
        '-m', '--method',
        dest='encrypt_method',
        default='auto3protect',
        choices=['autoprotect', 'auto1protect', 'auto2protect', 'auto3protect'],
        help='VCS encryption method (default: auto3protect)'
    )
    
    # Exclusion filters
    parser.add_argument(
        '--exclude-files',
        nargs='*',
        default=[],
        metavar='PATTERN',
        help='File patterns to exclude (e.g., "*_tb.v" "test_*.sv")'
    )
    
    parser.add_argument(
        '--exclude-dirs',
        nargs='*',
        default=[],
        metavar='PATTERN',
        help='Directory patterns to exclude (e.g., test simv simulation)'
    )
    
    # Copy-only filters
    parser.add_argument(
        '--copy-only-files',
        nargs='*',
        default=[],
        metavar='PATTERN',
        help='File patterns to copy without encryption (e.g., "*.vh" "*_pkg.sv")'
    )
    
    parser.add_argument(
        '--copy-only-dirs',
        nargs='*',
        default=[],
        metavar='PATTERN',
        help='Directory patterns to copy without encryption (e.g., include defines)'
    )
    
    args = parser.parse_args()
    
    # Print configuration if filters are specified
    if args.exclude_files or args.exclude_dirs or args.copy_only_files or args.copy_only_dirs:
        print("=" * 80)
        print("Filter Configuration:")
        print("=" * 80)
        if args.exclude_files:
            print(f"Exclude files:       {args.exclude_files}")
        if args.exclude_dirs:
            print(f"Exclude directories: {args.exclude_dirs}")
        if args.copy_only_files:
            print(f"Copy-only files:     {args.copy_only_files}")
        if args.copy_only_dirs:
            print(f"Copy-only dirs:      {args.copy_only_dirs}")
        print("=" * 80)
        print()
    
    # Create encryptor and execute
    encryptor = BatchEncryptor(
        args.source_dir, 
        args.target_dir, 
        args.log_dir,
        filelist_name=args.filelist_name,
        encrypt_method=args.encrypt_method,
        exclude_files=args.exclude_files if args.exclude_files else None,
        exclude_dirs=args.exclude_dirs if args.exclude_dirs else None,
        copy_only_files=args.copy_only_files if args.copy_only_files else None,
        copy_only_dirs=args.copy_only_dirs if args.copy_only_dirs else None
    )
    success = encryptor.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
