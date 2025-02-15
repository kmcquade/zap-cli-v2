"""
ZAP CLI.
"""

import sys
import os
import click

from zapcli.version import __version__
from zapcli import helpers
from zapcli.commands.context import context_group
from zapcli.commands.policies import policies_group
from zapcli.commands.scanners import scanner_group
from zapcli.commands.scripts import scripts_group
from zapcli.commands.session import session_group
from zapcli.log import console
from zapcli.zap_helper import ZAPHelper


@click.group(help='ZAP CLI v{0} - A simple commandline tool for OWASP ZAP.'.format(__version__))
@click.option('--boring', is_flag=True, default=False, help='Remove color from console output.')
@click.option('--verbose', '-v', is_flag=True, default=False, type=bool,
              help='Add more verbose debugging output.')
@click.option('--zap-path', default='/zap', envvar='ZAP_PATH', type=str,
              help='Path to the ZAP daemon. Defaults to /zap or the value of the environment variable ZAP_PATH.')
@click.option('--port', '-p', default=8090, envvar='ZAP_PORT', type=int,
              help='Port of the ZAP proxy. Defaults to 8090 or the value of the environment variable ZAP_PORT.')
@click.option('--zap-url', default='http://127.0.0.1', envvar='ZAP_URL', type=str,
              help='The URL of the ZAP proxy. Defaults to http://127.0.0.1 or the value of the environment ' +
              'variable ZAP_URL.')
@click.option('--api-key', default='', envvar='ZAP_API_KEY', type=str,
              help='The API key for using the ZAP API if required. Defaults to the value of the environment ' +
              'variable ZAP_API_KEY.')
@click.option('--log-path', envvar='ZAP_LOG_PATH', type=str,
              help='Path to the directory in which to save the ZAP output log file. Defaults to the value of ' +
              'the environment variable ZAP_LOG_PATH and uses the value of --zap-path if it is not set.')
@click.option('--soft-fail', type=bool, default=False, is_flag=True, envvar="SOFT_FAIL", help="Runs scans but suppresses error code")
@click.pass_context
def cli(ctx, boring, verbose, zap_path, port, zap_url, api_key, log_path, soft_fail):
    """Main command line entry point."""
    console.colorize = not boring

    if verbose:
        console.setLevel('DEBUG')
    else:
        console.setLevel('INFO')
    if soft_fail:
        os.environ["SOFT_FAIL"] = "true"

    ctx.obj = ZAPHelper(zap_path=zap_path, port=port, url=zap_url, api_key=api_key, log_path=log_path, soft_fail=soft_fail)


@cli.command('start', short_help='Start the ZAP daemon.')
@click.option('--start-options', '-o', type=str,
              help='Extra options to pass to the ZAP start command, e.g. "-config api.key=12345"')
@click.pass_obj
def start_zap_daemon(zap_helper, start_options):
    """Helper to start the daemon using the current config."""
    console.info('Starting ZAP daemon')
    with helpers.zap_error_handler():
        zap_helper.start(options=start_options)


@cli.command('shutdown')
@click.pass_obj
def shutdown_zap_daemon(zap_helper):
    """Shutdown the ZAP daemon."""
    console.info('Shutting down ZAP daemon')
    with helpers.zap_error_handler():
        zap_helper.shutdown()


@cli.command('status', short_help='Check if ZAP is running.')
@click.option('--timeout', '-t', type=int,
              help='Wait this number of seconds for ZAP to have started')
@click.pass_obj
def check_status(zap_helper, timeout):
    """
    Check if ZAP is running and able to receive API calls.

    You can provide a timeout option which is the amount of time in seconds
    the command should wait for ZAP to start if it is not currently running.
    This is useful to run before calling other commands if ZAP was started
    outside of zap-cli. For example:

        zap-cli status -t 60 && zap-cli open-url "http://127.0.0.1/"

    Exits with code 1 if ZAP is either not running or the command timed out
    waiting for ZAP to start.
    """
    with helpers.zap_error_handler():
        if zap_helper.is_running():
            console.info('ZAP is running')
        elif timeout is not None:
            zap_helper.wait_for_zap(timeout)
            console.info('ZAP is running')
        else:
            console.error('ZAP is not running')
            sys.exit(2)


@cli.command('open-url')
@click.argument('url')
@click.pass_obj
def open_url(zap_helper, url):
    """Open a URL using the ZAP proxy."""
    console.info('Accessing URL {0}'.format(url))
    zap_helper.open_url(url)


@cli.command('spider')
@click.argument('url')
@click.option('--context-name', '-c', type=str, help='Context to use if provided.')
@click.option('--user-name', '-u', type=str,
              help='Run scan as this user if provided. If this option is used, the context parameter must also ' +
              'be provided.')
@click.pass_obj
def spider_url(zap_helper, url, context_name, user_name):
    """Run the spider against a URL."""
    console.info('Running spider...')
    with helpers.zap_error_handler():
        zap_helper.run_spider(url, context_name, user_name)


@cli.command('ajax-spider')
@click.argument('url')
@click.pass_obj
def ajax_spider_url(zap_helper, url):
    """Run the AJAX Spider against a URL."""
    console.info('Running AJAX Spider...')
    zap_helper.run_ajax_spider(url)


@cli.command('active-scan', short_help='Run an Active Scan.')
@click.argument('url')
@click.option('--scanners', '-s', type=str, callback=helpers.validate_scanner_list,
              help='Comma separated list of scanner IDs and/or groups to use in the scan. Use the scanners ' +
              'subcommand to get a list of IDs. Available groups are: {0}.'.format(
                  ', '.join(['all'] + list(ZAPHelper.scanner_group_map.keys()))))
@click.option('--recursive', '-r', is_flag=True, default=False, help='Make scan recursive.')
@click.option('--context-name', '-c', type=str, help='Context to use if provided.')
@click.option('--user-name', '-u', type=str,
              help='Run scan as this user if provided. If this option is used, the context parameter must also ' +
              'be provided.')
@click.option('--soft-fail', type=bool, default=False, is_flag=True, envvar="SOFT_FAIL", help="Runs scans but suppresses error code")
@click.pass_obj
def active_scan(zap_helper, url, scanners, recursive, context_name, user_name, soft_fail):
    """
    Run an Active Scan against a URL.

    The URL to be scanned must be in ZAP's site tree, i.e. it should have already
    been opened using the open-url command or found by running the spider command.
    """
    console.info('Running an active scan...')

    with helpers.zap_error_handler():
        if scanners:
            zap_helper.set_enabled_scanners(scanners)

        zap_helper.run_active_scan(url, recursive, context_name, user_name)


@cli.command('alerts')
@click.option('--alert-level', '-l', default='High', type=click.Choice(ZAPHelper.alert_levels.keys()),
              help='Minimum alert level to include in report (default: High).')
@click.option('--output-format', '-f', default='table', type=click.Choice(['table', 'json']),
              help='Output format to print the alerts.')
@click.option('--exit-code', default=True, type=bool,
              help='Whether to set a non-zero exit code when there are any alerts of the specified ' +
              'level (default: True).')
@click.pass_obj
def show_alerts(zap_helper, alert_level, output_format, exit_code):
    """Show alerts at the given alert level."""
    alerts = zap_helper.alerts(alert_level)

    helpers.report_alerts(alerts, output_format)

    if exit_code:
        code = 1 if len(alerts) > 0 else 0
        sys.exit(code)


@cli.command('quick-scan', short_help='Run a quick scan.')
@click.argument('url')
@click.option('--self-contained', '-sc', is_flag=True, default=False,
              help='Make the scan self-contained, i.e. start the daemon, open the URL, scan it, ' +
              'and shutdown the daemon when done.')
@click.option('--scanners', '-s', type=str, callback=helpers.validate_scanner_list,
              help='Comma separated list of scanner IDs and/or groups to use in the scan. Use the scanners ' +
              'subcommand to get a list of IDs. Available groups are: {0}.'.format(
                  ', '.join(['all'] + list(ZAPHelper.scanner_group_map.keys()))))
@click.option('--spider', is_flag=True, default=False, help='If set, run the spider before running the scan.')
@click.option('--ajax-spider', is_flag=True, default=False, help='If set, run the AJAX Spider before running the scan.')
@click.option('--recursive', '-r', is_flag=True, default=False, help='Make scan recursive.')
@click.option('--alert-level', '-l', default='High', type=click.Choice(ZAPHelper.alert_levels.keys()),
              help='Minimum alert level to include in report.')
@click.option('--exclude', '-e', type=str, callback=helpers.validate_regex,
              help='Regex to exclude from all aspects of the scan')
@click.option('--start-options', '-o', type=str,
              help='Extra options to pass to the ZAP start command when the --self-contained option is used, ' +
              ' e.g. "-config api.key=12345"')
@click.option('--output-format', '-f', default='table', type=click.Choice(['table', 'json']),
              help='Output format to print the alerts.')
@click.option('--context-name', '-c', type=str, help='Context to use if provided.')
@click.option('--user-name', '-u', type=str,
              help='Run scan as this user if provided. If this option is used, the context parameter must also ' +
              'be provided.')
@click.option('--soft-fail', type=bool, default=False, is_flag=True, envvar="SOFT_FAIL", help="Runs scans but suppresses error code")
@click.pass_obj
def quick_scan(zap_helper, url, **options):
    """
    Run a quick scan of a site by opening a URL, optionally spidering the URL,
    running an Active Scan, and reporting any issues found.

    This command contains most scan options as parameters, so you can do
    everything in one go.

    If any alerts are found for the given alert level, this command will exit
    with a status code of 1.
    """

    if options['self_contained']:
        console.info('Starting ZAP daemon')
        with helpers.zap_error_handler():
            zap_helper.start(options['start_options'])

    console.info('Running a quick scan for {0}'.format(url))

    with helpers.zap_error_handler():
        if options['scanners']:
            zap_helper.set_enabled_scanners(options['scanners'])

        if options['exclude']:
            zap_helper.exclude_from_all(options['exclude'])

        zap_helper.open_url(url)

        if options['spider']:
            zap_helper.run_spider(url, options['context_name'], options['user_name'])

        if options['ajax_spider']:
            zap_helper.run_ajax_spider(url)

        zap_helper.run_active_scan(url, options['recursive'], options['context_name'], options['user_name'])

    alerts = zap_helper.alerts(options['alert_level'])

    helpers.report_alerts(alerts, options['output_format'])

    if options['self_contained']:
        console.info('Shutting down ZAP daemon')
        with helpers.zap_error_handler():
            zap_helper.shutdown()

    # Customization: Soft fail for error codes
    if len(alerts) > 0 and not options.get("soft_fail") and not os.getenv("SOFT_FAIL"):
        exit_code = 1
    else:
        exit_code = 0
    # exit_code = 1 if len(alerts) > 0 else 0
    sys.exit(exit_code)


@cli.command('exclude', short_help='Exclude a pattern from all scanners.')
@click.argument('pattern', callback=helpers.validate_regex)
@click.pass_obj
def exclude_from_scanners(zap_helper, pattern):
    """Exclude a pattern from proxy, spider and active scanner."""
    with helpers.zap_error_handler():
        zap_helper.exclude_from_all(pattern)


@cli.command('report')
@click.option('--output', '-o', help='Output file for report.')
@click.option('--output-format', '-f', default='xml', type=click.Choice(['xml', 'html', 'md']),
              help='Report format.')
@click.pass_obj
def report(zap_helper, output, output_format):
    """Generate XML, MD or HTML report."""
    if output_format == 'html':
        zap_helper.html_report(output)
    elif output_format == 'md':
        zap_helper.md_report(output)
    else:
        zap_helper.xml_report(output)

    console.info('Report saved to "{0}"'.format(output))


# Add subcommand groups
cli.add_command(context_group)
cli.add_command(policies_group)
cli.add_command(scanner_group)
cli.add_command(scripts_group)
cli.add_command(session_group)
