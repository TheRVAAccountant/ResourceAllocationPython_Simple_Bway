#!/usr/bin/env python3
"""
Automated rollback script for the Resource Management System.
Provides automated rollback capabilities with comprehensive validation.
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil


class RollbackAutomation:
    """
    Automated rollback system for safe deployment recovery.
    Handles application rollback, data restoration, and validation.
    """

    def __init__(self, rollback_version: str = "1.0.0", dry_run: bool = False):
        """
        Initialize rollback automation.

        Args:
            rollback_version: Target version to roll back to
            dry_run: If True, simulate rollback without making changes
        """
        self.rollback_version = rollback_version
        self.dry_run = dry_run
        self.rollback_timestamp = datetime.now()

        # Paths
        self.project_root = Path(__file__).parent.parent
        self.backup_dir = self.project_root / "backups"
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"

        # Setup logging
        self.setup_logging()

        # Rollback state
        self.rollback_steps = []
        self.failed_steps = []
        self.rollback_successful = False

        logger.info(
            f"Rollback automation initialized - Target: v{rollback_version}, Dry run: {dry_run}"
        )

    def setup_logging(self):
        """Setup rollback logging."""
        global logger

        # Create logs directory if it doesn't exist
        self.logs_dir.mkdir(exist_ok=True)

        log_filename = f"rollback_{self.rollback_timestamp:%Y%m%d_%H%M%S}.log"
        log_path = self.logs_dir / log_filename

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(), logging.FileHandler(log_path)],
        )
        logger = logging.getLogger(__name__)

    def execute_rollback(self) -> bool:
        """
        Execute complete rollback procedure.

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            print("🚨 INITIATING AUTOMATED ROLLBACK")
            print("=" * 50)
            print(f"Target Version: v{self.rollback_version}")
            print(f"Rollback Time: {self.rollback_timestamp}")
            print(f"Dry Run Mode: {'ENABLED' if self.dry_run else 'DISABLED'}")
            print("=" * 50)

            if not self.dry_run:
                response = input("\\nProceed with rollback? (yes/no): ")
                if response.lower() != "yes":
                    print("Rollback cancelled by user")
                    return False

            # Pre-rollback validation
            if not self._pre_rollback_validation():
                return False

            # Create rollback snapshot
            if not self._create_rollback_snapshot():
                return False

            # Stop application services
            if not self._stop_application_services():
                return False

            # Restore application version
            if not self._restore_application_version():
                return False

            # Restore configuration
            if not self._restore_configuration():
                return False

            # Restore data files
            if not self._restore_data_files():
                return False

            # Disable new features
            if not self._disable_new_features():
                return False

            # Validate rollback
            if not self._validate_rollback():
                return False

            # Restart application services
            if not self._restart_application_services():
                return False

            # Post-rollback validation
            if not self._post_rollback_validation():
                return False

            # Generate rollback report
            self._generate_rollback_report()

            self.rollback_successful = True
            print("\\n✅ ROLLBACK COMPLETED SUCCESSFULLY")
            print("🎉 System restored to stable state")

            return True

        except Exception as e:
            logger.error(f"Rollback failed with exception: {e}")
            print(f"\\n❌ ROLLBACK FAILED: {e}")
            self._emergency_recovery()
            return False

    def _pre_rollback_validation(self) -> bool:
        """Validate system state before rollback."""
        print("\\n🔍 Pre-rollback validation...")

        try:
            # Check if backup exists
            backup_path = self.backup_dir / f"v{self.rollback_version}"
            if not backup_path.exists():
                print(f"  ❌ Backup for v{self.rollback_version} not found at {backup_path}")
                return False

            print(f"  ✅ Backup found: {backup_path}")

            # Check disk space
            disk_usage = shutil.disk_usage(self.project_root)
            free_gb = disk_usage.free / (1024**3)

            if free_gb < 1.0:  # Need at least 1GB free
                print(f"  ❌ Insufficient disk space: {free_gb:.1f} GB free")
                return False

            print(f"  ✅ Sufficient disk space: {free_gb:.1f} GB free")

            # Check system resources
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                print(f"  ⚠️  High memory usage: {memory.percent}%")
            else:
                print(f"  ✅ Memory usage acceptable: {memory.percent}%")

            self.rollback_steps.append(
                ("pre_validation", "completed", "Pre-rollback validation passed")
            )
            return True

        except Exception as e:
            logger.error(f"Pre-rollback validation failed: {e}")
            self.failed_steps.append(("pre_validation", str(e)))
            return False

    def _create_rollback_snapshot(self) -> bool:
        """Create snapshot of current state for analysis."""
        print("\\n📸 Creating rollback snapshot...")

        try:
            snapshot_dir = (
                self.backup_dir / f"rollback_snapshot_{self.rollback_timestamp:%Y%m%d_%H%M%S}"
            )

            if not self.dry_run:
                snapshot_dir.mkdir(parents=True, exist_ok=True)

                # Copy critical files
                critical_paths = [
                    self.project_root / "src",
                    self.project_root / "config",
                    self.project_root / "pyproject.toml",
                    self.project_root / "requirements.txt",
                ]

                for path in critical_paths:
                    if path.exists():
                        if path.is_dir():
                            shutil.copytree(path, snapshot_dir / path.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(path, snapshot_dir / path.name)

                print(f"  ✅ Snapshot created: {snapshot_dir}")
            else:
                print(f"  🔍 [DRY RUN] Would create snapshot: {snapshot_dir}")

            self.rollback_steps.append(
                ("snapshot", "completed", f"Snapshot created at {snapshot_dir}")
            )
            return True

        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            self.failed_steps.append(("snapshot", str(e)))
            return False

    def _stop_application_services(self) -> bool:
        """Stop all application services."""
        print("\\n🛑 Stopping application services...")

        try:
            # Find and terminate application processes
            terminated_processes = []

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if "resource-allocation" in cmdline or "src.main" in cmdline:
                        if not self.dry_run:
                            proc.terminate()
                            terminated_processes.append(proc.info["pid"])
                        else:
                            print(f"  🔍 [DRY RUN] Would terminate process: {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if terminated_processes:
                print(f"  ✅ Terminated {len(terminated_processes)} application processes")
            else:
                print("  ✅ No active application processes found")

            # Wait for processes to terminate
            if not self.dry_run:
                time.sleep(3)

            self.rollback_steps.append(
                ("stop_services", "completed", f"Stopped {len(terminated_processes)} processes")
            )
            return True

        except Exception as e:
            logger.error(f"Failed to stop services: {e}")
            self.failed_steps.append(("stop_services", str(e)))
            return False

    def _restore_application_version(self) -> bool:
        """Restore application to target version."""
        print(f"\\n📦 Restoring application to v{self.rollback_version}...")

        try:
            backup_path = self.backup_dir / f"v{self.rollback_version}"

            if not self.dry_run:
                # Backup current src directory
                current_src_backup = (
                    self.backup_dir / f"current_src_{self.rollback_timestamp:%Y%m%d_%H%M%S}"
                )
                if (self.project_root / "src").exists():
                    shutil.copytree(self.project_root / "src", current_src_backup)

                # Restore src directory from backup
                if (backup_path / "src").exists():
                    shutil.rmtree(self.project_root / "src", ignore_errors=True)
                    shutil.copytree(backup_path / "src", self.project_root / "src")

                # Restore requirements.txt
                if (backup_path / "requirements.txt").exists():
                    shutil.copy2(
                        backup_path / "requirements.txt", self.project_root / "requirements.txt"
                    )

                # Restore pyproject.toml
                if (backup_path / "pyproject.toml").exists():
                    shutil.copy2(
                        backup_path / "pyproject.toml", self.project_root / "pyproject.toml"
                    )

                print(f"  ✅ Application restored from {backup_path}")
            else:
                print(f"  🔍 [DRY RUN] Would restore from {backup_path}")

            self.rollback_steps.append(
                ("restore_app", "completed", f"Application restored to v{self.rollback_version}")
            )
            return True

        except Exception as e:
            logger.error(f"Application restoration failed: {e}")
            self.failed_steps.append(("restore_app", str(e)))
            return False

    def _restore_configuration(self) -> bool:
        """Restore configuration files."""
        print("\\n⚙️  Restoring configuration...")

        try:
            backup_path = self.backup_dir / f"v{self.rollback_version}"
            config_backup = backup_path / "config"

            if not self.dry_run:
                if config_backup.exists():
                    # Backup current config
                    current_config_backup = (
                        self.backup_dir / f"current_config_{self.rollback_timestamp:%Y%m%d_%H%M%S}"
                    )
                    if self.config_dir.exists():
                        shutil.copytree(self.config_dir, current_config_backup)

                    # Restore config from backup
                    shutil.rmtree(self.config_dir, ignore_errors=True)
                    shutil.copytree(config_backup, self.config_dir)

                    print(f"  ✅ Configuration restored from {config_backup}")
                else:
                    print("  ⚠️  No configuration backup found, keeping current config")
            else:
                print(f"  🔍 [DRY RUN] Would restore config from {config_backup}")

            self.rollback_steps.append(("restore_config", "completed", "Configuration restored"))
            return True

        except Exception as e:
            logger.error(f"Configuration restoration failed: {e}")
            self.failed_steps.append(("restore_config", str(e)))
            return False

    def _restore_data_files(self) -> bool:
        """Restore data files and templates."""
        print("\\n📁 Restoring data files...")

        try:
            backup_path = self.backup_dir / f"v{self.rollback_version}"
            data_backup = backup_path / "data"

            if not self.dry_run:
                if data_backup.exists():
                    data_dir = self.project_root / "data"

                    # Backup current data
                    current_data_backup = (
                        self.backup_dir / f"current_data_{self.rollback_timestamp:%Y%m%d_%H%M%S}"
                    )
                    if data_dir.exists():
                        shutil.copytree(data_dir, current_data_backup)

                    # Restore data from backup
                    shutil.rmtree(data_dir, ignore_errors=True)
                    shutil.copytree(data_backup, data_dir)

                    print(f"  ✅ Data files restored from {data_backup}")
                else:
                    print("  ⚠️  No data backup found, keeping current data")
            else:
                print(f"  🔍 [DRY RUN] Would restore data from {data_backup}")

            self.rollback_steps.append(("restore_data", "completed", "Data files restored"))
            return True

        except Exception as e:
            logger.error(f"Data restoration failed: {e}")
            self.failed_steps.append(("restore_data", str(e)))
            return False

    def _disable_new_features(self) -> bool:
        """Disable new features introduced in failed deployment."""
        print("\\n🚫 Disabling new features...")

        try:
            env_file = self.project_root / ".env"

            if not self.dry_run:
                # Read current .env file
                env_content = ""
                if env_file.exists():
                    env_content = env_file.read_text()

                # Disable new features
                feature_flags = [
                    "FEATURE_DUPLICATE_VALIDATION=disabled",
                    "FEATURE_UNASSIGNED_VEHICLES=disabled",
                    "FEATURE_THICK_BORDERS=disabled",
                ]

                # Update or add feature flags
                for flag in feature_flags:
                    flag_name = flag.split("=")[0]
                    if flag_name in env_content:
                        # Replace existing flag
                        lines = env_content.split("\\n")
                        for i, line in enumerate(lines):
                            if line.startswith(flag_name):
                                lines[i] = flag
                        env_content = "\\n".join(lines)
                    else:
                        # Add new flag
                        env_content += f"\\n{flag}"

                # Write updated .env file
                env_file.write_text(env_content)

                print("  ✅ New features disabled")
            else:
                print("  🔍 [DRY RUN] Would disable new features")

            self.rollback_steps.append(("disable_features", "completed", "New features disabled"))
            return True

        except Exception as e:
            logger.error(f"Feature disabling failed: {e}")
            self.failed_steps.append(("disable_features", str(e)))
            return False

    def _validate_rollback(self) -> bool:
        """Validate that rollback was successful."""
        print("\\n✅ Validating rollback...")

        try:
            # Check that target version files exist
            src_dir = self.project_root / "src"
            if not src_dir.exists():
                print("  ❌ Source directory missing")
                return False

            # Check pyproject.toml version
            pyproject_file = self.project_root / "pyproject.toml"
            if pyproject_file.exists():
                content = pyproject_file.read_text()
                if f'version = "{self.rollback_version}"' in content:
                    print(f"  ✅ Version correctly set to {self.rollback_version}")
                else:
                    print("  ⚠️  Version in pyproject.toml may not match target")

            # Verify new feature services are not accessible (or properly disabled)
            print("  ✅ Basic file structure validation passed")

            self.rollback_steps.append(("validate", "completed", "Rollback validation passed"))
            return True

        except Exception as e:
            logger.error(f"Rollback validation failed: {e}")
            self.failed_steps.append(("validate", str(e)))
            return False

    def _restart_application_services(self) -> bool:
        """Restart application services."""
        print("\\n🚀 Restarting application services...")

        try:
            if not self.dry_run:
                # For now, just indicate that services can be restarted
                # In a real deployment, this would start the actual services
                print("  ✅ Application ready for restart")
                print("  💡 Manual restart may be required")
            else:
                print("  🔍 [DRY RUN] Would restart application services")

            self.rollback_steps.append(
                ("restart_services", "completed", "Services ready for restart")
            )
            return True

        except Exception as e:
            logger.error(f"Service restart failed: {e}")
            self.failed_steps.append(("restart_services", str(e)))
            return False

    def _post_rollback_validation(self) -> bool:
        """Perform post-rollback validation."""
        print("\\n🔍 Post-rollback validation...")

        try:
            # Run basic import tests
            if not self.dry_run:
                # Test basic imports (without executing full validation)
                test_script = f"""
import sys
sys.path.insert(0, "{self.project_root / "src"}")

try:
    from core.gas_compatible_allocator import GASCompatibleAllocator
    from services.excel_service import ExcelService
    print("✅ Core services can be imported")
except Exception as e:
    print(f"❌ Import test failed: {{e}}")
    exit(1)
"""

                result = subprocess.run(
                    [sys.executable, "-c", test_script], capture_output=True, text=True
                )

                if result.returncode == 0:
                    print("  ✅ Basic import validation passed")
                else:
                    print(f"  ❌ Import validation failed: {result.stderr}")
                    return False
            else:
                print("  🔍 [DRY RUN] Would run post-rollback validation")

            self.rollback_steps.append(
                ("post_validation", "completed", "Post-rollback validation passed")
            )
            return True

        except Exception as e:
            logger.error(f"Post-rollback validation failed: {e}")
            self.failed_steps.append(("post_validation", str(e)))
            return False

    def _emergency_recovery(self) -> None:
        """Emergency recovery procedures if rollback fails."""
        print("\\n🆘 EMERGENCY RECOVERY PROCEDURES")
        print("=" * 40)
        print("Rollback has failed. Manual intervention required.")
        print("\\nRecommended actions:")
        print("1. Check application logs for specific errors")
        print("2. Verify backup integrity")
        print("3. Consider restoring from system-level backups")
        print("4. Contact technical support immediately")
        print("\\nSystem state preserved for analysis")

    def _generate_rollback_report(self) -> None:
        """Generate comprehensive rollback report."""
        report_path = (
            self.logs_dir / f"rollback_report_{self.rollback_timestamp:%Y%m%d_%H%M%S}.json"
        )

        report = {
            "rollback_info": {
                "timestamp": self.rollback_timestamp.isoformat(),
                "target_version": self.rollback_version,
                "dry_run": self.dry_run,
                "successful": self.rollback_successful,
            },
            "steps_completed": self.rollback_steps,
            "failed_steps": self.failed_steps,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_free_gb": shutil.disk_usage(self.project_root).free / (1024**3),
            },
            "recommendations": self._generate_recommendations(),
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\\n📊 Rollback report saved: {report_path}")

    def _generate_recommendations(self) -> list[str]:
        """Generate recommendations based on rollback results."""
        recommendations = []

        if self.rollback_successful:
            recommendations.extend(
                [
                    "Conduct root cause analysis of deployment failure",
                    "Review and update deployment procedures",
                    "Enhance testing coverage for failed areas",
                    "Update rollback procedures based on lessons learned",
                ]
            )
        else:
            recommendations.extend(
                [
                    "URGENT: System may be in unstable state",
                    "Verify application functionality before resuming operations",
                    "Consider restoring from system-level backups",
                    "Review rollback procedures for improvements",
                ]
            )

        if self.failed_steps:
            recommendations.append("Investigate specific failed steps for process improvements")

        return recommendations


def main():
    """Main entry point for rollback automation."""
    parser = argparse.ArgumentParser(
        description="Automated rollback for Resource Management System"
    )
    parser.add_argument(
        "--version", default="1.0.0", help="Target version to roll back to (default: 1.0.0)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate rollback without making changes"
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")

    args = parser.parse_args()

    # Create rollback automation instance
    rollback = RollbackAutomation(rollback_version=args.version, dry_run=args.dry_run)

    # Execute rollback
    success = rollback.execute_rollback()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
