import os
import logging
import sys
import datetime
import shlex
import subprocess
import config_utils
from email_utils import send_mail
from . import log, PYTHONPATH, PYTHON_EXEC

class SimpleScheduler:
    def __init__(self, config):
        self.tasks = []
        self.send_from = '<email>'
        self.send_error_to = []
        self.send_report_to = []
        self.read_config(config)
        self.finished_tasks={}

    @staticmethod
    def _matches_cron_expression(cron_expression, current_day, current_hour, current_minute):
        pass

    def _execute_task(self,module_name, module_config):
        pass

    def read_config(self, config):
        self.send_error_to = config_utils.read_list(config.get('DEFAULT', 'send_error_to', fallback=None))
        self.send_report_to = config_utils.read_list(config.get('DEFAULT', 'send_report_to', fallback=None))
        for section in config.sections:
            module_name = config.get(section, 'module')
            module_config = config.get(section, 'module_config')
            cron_expression = config.get(section, 'cron')
            task = {'module': module_name, 'cron': cron_expression,
                    'module_config': module_config, 'section': section}
            self.tasks.append(task)

    def execute(self):
        current_time=datetime.datetime.now()
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
        pass





