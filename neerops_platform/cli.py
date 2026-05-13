#!/usr/bin/env python3
"""
NEEROps v9.0 - CLI Interface
Command-line tool for running and managing the platform.
"""

import sys
import logging
import argparse
from typing import Optional

from config import Config, load_env_file
from main import NEEROpsV9
from tests import run_tests


def setup_logging(level: str = "INFO"):
    """Setup logging."""
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )


class NEEROpsyCLI:
    """NEEROps CLI."""
    
    def __init__(self):
        self.platform = None
        self.logger = logging.getLogger(__name__)
    
    def run(self, args=None):
        """Main CLI entry point."""
        parser = self._create_parser()
        args = parser.parse_args(args)
        
        # Setup logging
        setup_logging(Config.LOG_LEVEL)
        
        # Load .env if specified
        if args.env_file:
            load_env_file(args.env_file)
        
        # Print config if requested
        if args.show_config:
            Config.print_config()
        
        # Validate config
        if not Config.validate():
            self.logger.error("[CLI] Configuration validation failed")
            return 1
        
        # Execute command
        if hasattr(args, 'func'):
            return args.func(args) or 0
        else:
            parser.print_help()
            return 0
    
    def _create_parser(self):
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description="NEEROps v9.0 - Autonomous DevOps Platform",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Start the platform
  python cli.py start
  
  # Run tests
  python cli.py test
  
  # Process a test PR
  python cli.py pr --id test-001 --title "Feature X" --branch main
  
  # Show configuration
  python cli.py config
  
  # Run scheduled tasks
  python cli.py scheduler
            """
        )
        
        # Global options
        parser.add_argument("--env-file", default=".env", help="Environment file (default: .env)")
        parser.add_argument("--show-config", action="store_true", help="Print configuration and exit")
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        
        subparsers = parser.add_subparsers(title="Commands", dest="command")
        
        # start command
        start_parser = subparsers.add_parser("start", help="Start NEEROps platform")
        start_parser.add_argument("--supervisor", action="store_true", default=True, 
                                help="Start autonomy supervisor")
        start_parser.set_defaults(func=self.cmd_start)
        
        # test command
        test_parser = subparsers.add_parser("test", help="Run test suite")
        test_parser.add_argument("--verbosity", type=int, default=2, choices=[0, 1, 2])
        test_parser.set_defaults(func=self.cmd_test)
        
        # pr command
        pr_parser = subparsers.add_parser("pr", help="Process a PR")
        pr_parser.add_argument("--id", required=True, help="PR ID")
        pr_parser.add_argument("--title", required=True, help="PR title")
        pr_parser.add_argument("--branch", default="main", help="Target branch")
        pr_parser.add_argument("--description", default="", help="PR description")
        pr_parser.set_defaults(func=self.cmd_pr)
        
        # config command
        config_parser = subparsers.add_parser("config", help="Show configuration")
        config_parser.set_defaults(func=self.cmd_config)
        
        # health command
        health_parser = subparsers.add_parser("health", help="Check system health")
        health_parser.set_defaults(func=self.cmd_health)
        
        # scheduler command
        scheduler_parser = subparsers.add_parser("scheduler", help="Run scheduled tasks")
        scheduler_parser.add_argument("--once", action="store_true", help="Run once and exit")
        scheduler_parser.set_defaults(func=self.cmd_scheduler)
        
        # logs command
        logs_parser = subparsers.add_parser("logs", help="Show system logs")
        logs_parser.add_argument("--lines", type=int, default=50, help="Number of lines to show")
        logs_parser.set_defaults(func=self.cmd_logs)
        
        return parser
    
    def cmd_start(self, args):
        """Start platform."""
        self.logger.info("[CLI] Starting NEEROps platform...")
        
        self.platform = NEEROpsV9()
        self.platform.start()
        
        self.logger.info("[CLI] Platform started successfully")
        self.logger.info("[CLI] Waiting for PR webhooks...")
        
        # In production: would run webhook server here
        # For now: just exit cleanly
        return 0
    
    def cmd_test(self, args):
        """Run tests."""
        self.logger.info("[CLI] Running test suite...")
        
        success = run_tests(verbosity=args.verbosity)
        
        if success:
            self.logger.info("[CLI] All tests passed ✓")
            return 0
        else:
            self.logger.error("[CLI] Some tests failed ✗")
            return 1
    
    def cmd_pr(self, args):
        """Process a PR."""
        self.logger.info(f"[CLI] Processing PR {args.id}...")
        
        self.platform = NEEROpsV9()
        
        webhook_payload = {
            "pull_request": {
                "id": args.id,
                "title": args.title,
                "body": args.description,
                "base": {"ref": args.branch}
            }
        }
        
        result = self.platform.handle_pr_webhook(webhook_payload)
        
        if result:
            self.logger.info(f"[CLI] PR {args.id} processed successfully ✓")
            return 0
        else:
            self.logger.error(f"[CLI] PR {args.id} processing failed ✗")
            return 1
    
    def cmd_config(self, args):
        """Show configuration."""
        Config.print_config()
        return 0
    
    def cmd_health(self, args):
        """Check system health."""
        self.logger.info("[CLI] Checking system health...")
        
        checks = {
            "EventBus": Config.EVENT_BUS_TYPE,
            "Vault": Config.VAULT_TYPE,
            "OTEL": Config.OTEL_TYPE,
            "QLDB": Config.QLDB_TYPE,
            "K8S": "enabled" if Config.K8S_ENABLED else "disabled",
            "Supervisor": "enabled" if Config.SUPERVISOR_ENABLED else "disabled"
        }
        
        self.logger.info("[CLI] Component Status:")
        for component, status in checks.items():
            self.logger.info(f"  {component:20} : {status}")
        
        return 0
    
    def cmd_scheduler(self, args):
        """Run scheduled tasks."""
        self.logger.info("[CLI] Running scheduled tasks...")
        
        self.platform = NEEROpsV9()
        self.platform.scheduled_tasks()
        
        if args.once:
            self.logger.info("[CLI] Scheduled tasks completed (once mode)")
            return 0
        else:
            self.logger.info("[CLI] Scheduled tasks running (continuous mode)")
            # In production: would run scheduler loop
            return 0
    
    def cmd_logs(self, args):
        """Show logs."""
        self.logger.info("[CLI] Showing last {} log lines...".format(args.lines))
        
        # In production: would read from actual log file
        self.logger.info("[CLI] Mock logs - no persistent log file in mock mode")
        
        return 0


def main():
    """Main entry point."""
    cli = NEEROpsyCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
