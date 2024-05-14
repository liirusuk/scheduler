import sys
import datetime
import shlex
import subprocess
import config_utils
from email_utils import send_mail
from . import log, PYTHONPATH, PYTHON_EXEC


class SimpleScheduler:
    def __init__(self, config_dict):
        self.tasks = []
        self.send_from = '<email>'
        self.send_error_to = []
        self.send_report_to = []
        self.read_config(config_dict)
        self.finished_tasks = {}

    def _matches_cron_expression(self, cron_expression, current_day, current_hour, current_minute):
        cron_minute, cron_hour, cron_day = cron_expression.split()
        return (self._matches_cron_field(cron_minute, current_minute) and
                self._matches_cron_field(cron_hour, current_hour) and
                self._matches_cron_field(cron_day, current_day))

    @staticmethod
    def _matches_cron_field(cron_field, current_value):
        if cron_field == '*':
            return True
        elif cron_field.isdigit():
            return int(cron_field) == current_value
        elif '/' in cron_field:
            step = int(cron_field.split('/')[1])
            return current_value % step == 0
        elif '-' in cron_field:
            cron_min = int(cron_field.split('-')[0]) if cron_field.split('-')[0].isdigit() else 0
            cron_max = int(cron_field.split('-')[1]) if cron_field.split('-')[1].isdigit() else 6
            return (cron_min <= current_value) and (current_value <= cron_max)
        else:
            return cron_field == current_value

    @staticmethod
    def _get_last_line(str_input, n=1):
        new_input = str_input.split('\n')[-n:]
        return '\n'.join(new_input)

    @staticmethod
    def _get_full_stack_trace():
        import traceback
        return traceback.format_exc()

    @staticmethod
    def _get_formatted_error(error_message):
        lines = error_message.strip().split('\n')
        formatted_lines = []
        for line in lines:
            if line.startswith('Error message'):
                formatted_lines.append(f'\n\n=== {line} ===\n')
            else:
                formatted_lines.append(line)
        formatted_error = '\n'.join(formatted_lines)
        return formatted_error

    @staticmethod
    def _send_email(sender, recipients, subject, body):
        try:
            send_mail(sender, recipients, subject, body)
        except Exception as e:
            log.error(f'Error while sending email {str(e)}')
            log.error(body)

    def _execute_task(self, module_name, module_config):
        command = ['export', f'PYTHONPATH={PYTHONPATH};', PYTHON_EXEC,
                   f'{PYTHONPATH}/{module_name}', '-config', module_config]
        command_str = ' '.join(command)
        command = shlex.split(command_str)
        log.info(f'Running command: {command_str}')
        try:
            result = subprocess.run(command, executable='/bin/ksh', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
            exitcode = result.returncode
            log.info(f'exitcode:\n {exitcode}')
            log.info(f'out:\n {self._get_last_line(stdout, n=2)}')
            log.info(f'error:\n {self._get_last_line(stderr)}')

            if (int(exitcode) != 0) and (len(stderr) > 0):
                raise RuntimeError(stderr)
        except Exception as e:
            error_message = f'Error while executing: {module_name} with config {module_config}\n'
            error_message += f'Command: {command_str}\n'
            error_message += f'Error message: {str(e)}\n'
            error_message += 'Full stacktrace:\n'
            error_message += self._get_full_stack_trace()
            formatted_error_message = self._get_formatted_error(error_message)
            if len(self.send_error_to) > 0:
                self._send_email(self.send_from, self.send_error_to, 'Scheduler Error',
                                 formatted_error_message)

    def read_config(self, config_dict):
        self.send_error_to = config_utils.read_list(config_dict.get('DEFAULT', 'send_error_to', fallback=None))
        self.send_report_to = config_utils.read_list(config_dict.get('DEFAULT', 'send_report_to', fallback=None))
        for section in config_dict.sections:
            module_name = config_dict.get(section, 'module')
            module_config = config_dict.get(section, 'module_config')
            cron_expression = config_dict.get(section, 'cron')
            task = {'module': module_name, 'cron': cron_expression,
                    'module_config': module_config, 'section': section}
            self.tasks.append(task)

    def execute(self):
        current_time = datetime.datetime.now()
        log.info(f'Running time {current_time}')
        current_day = int(current_time.strftime('%w'))
        current_hour = current_time.hour
        current_minute = current_time.minute

        for task in self.tasks:
            section_name = task['section']
            cron_expression = task['cron']
            module_name = task['module']
            module_config = task['module_config']

            if self._matches_cron_expression(cron_expression, current_day, current_hour, current_minute):
                finished = self._execute_task(module_name, module_config)
                self.finished_tasks[section_name] = finished
                log.info(f'Executed task {section_name}')

        self.send_report()

    def send_report(self):
        if (len(self.send_report_to) > 0) and (len(self.finished_tasks) > 0):
            finished_message = 'Scheduler finished tasks:\n'
            finished_message += f'Task Name\t\t\tExec Status\n'
            for key, value in self.finished_tasks.items():
                finished_message += f'{key}\t\t\t{value}\n'
            self._send_email(self.send_from, self.send_error_to, 'Scheduler ExecutionReport',
                             finished_message)


if __name__ == '__main__':
    config = config_utils.parse_config(sys.argv)
    scheduler = SimpleScheduler(config)
    scheduler.execute()
