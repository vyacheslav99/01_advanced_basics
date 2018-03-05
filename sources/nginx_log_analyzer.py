# -*- coding: utf-8 -*-
__author__: 'balychkov'

import os
import gzip
import traceback
import logging
import json
import shlex
import datetime
import statistics


class NginxLogAnalyzer:

    _rep_tmpl_file = './report.html'
    _log_file_name_tmpl = 'nginx-access-ui.log-'
    _rep_file_name_tmpl = 'report-{0}.{1:02d}.{2:02d}.html'
    _log_columns = ('remote_addr', 'remote_user', 'http_x_real_ip', 'time_local', 'request', 'status',
        'body_bytes_sent', 'http_referer', 'http_user_agent', 'http_x_forwarded_for', 'http_X_REQUEST_ID',
        'http_X_RB_USER', 'request_time')
    _default_line = ('', '', '', '', '', '', 0, 0, '', '', '', '', '', 0)

    def __init__(self, rep_dir, log_dir, rep_sz, max_parse_errors):
        self._rep_dir = rep_dir
        self._log_dir = log_dir
        self._rep_sz = rep_sz
        self._parse_errors = 0
        self._max_parse_errors = max_parse_errors
        self._history = []
        self._load_history()

    def _load_history(self):
        """ загружает историю по уже сформированным отчетам """

        try:
            for fn in os.listdir(self._rep_dir):
                self._history.append(self._log_file_name_tmpl + os.path.splitext(fn)[0].replace(
                    'report-', '').replace('.', ''))
        except:
            logging.exception('Не удалось получить историю обработки логов!')

    def _get_curren_log(self):
        """"
        Анализ папки расположения анализируемых логов - находит и возвращает самый свежий из необработанных.
        Вложенные папки не просматриваются.
        """

        files = []

        try:
            for x in os.listdir(self._log_dir):
                fn = os.path.join(self._log_dir, x)
                if os.path.isfile(fn) and x.startswith(self._log_file_name_tmpl) and \
                    os.path.splitext(x)[0] not in self._history:
                    files.append(fn)
        except:
            logging.exception('Ошибка анализа папки с логами сервера!')

        if files:
            files.sort()
            return files[-1]

        return None

    def _get_report_name(self, worked_file):
        """ Генерит и возвращает имя отчета на основе имени обрабатываемого файла лога """

        log_dt = datetime.datetime.strptime(
            os.path.splitext(os.path.split(worked_file)[1])[0].replace(self._log_file_name_tmpl, ''), '%Y%m%d')
        return os.path.join(self._rep_dir, self._rep_file_name_tmpl.format(log_dt.year, log_dt.month, log_dt.day))

    def _decode_line(self, line):
        """
        Безопасное декодирование строки line с попыткой автоматически подобрать кодировку.
        Если тип входящей строки (line) является возвращаемым типом, просто вернет ее, ничего не делая.

        python 3: Преобразует строку байт (bytes) в str, returns: str
        python 2: Преобразует строку (str) в unicode, returns: unicode
        """

        if isinstance(line, str):
            return line
        else:
            try:
                return line.decode('utf-8')
            except UnicodeDecodeError:
                return line.decode('cp1251')

    def _parse_line(self, line):
        """ парсит строку лога line, генерит по ней dict на основе колонок лога, его и возвращает """

        try:
            d = dict(zip(self._log_columns, shlex.split(line.replace('[', '"').replace(']', '"'))))

            if d['request_time'] != '-':
                d['request_time'] = float(d['request_time'])
            else:
                d['request_time'] = 0.0

            try:
                d['request'] = d['request'].split()[1]
            except:
                # оставляем строку адреса как есть - не принципиально
                pass
        except:
            logging.debug('Error in parse line:')
            logging.debug(line)
            logging.debug(traceback.format_exc())
            self._parse_errors += 1
            d = dict(zip(self._log_columns, self._default_line))

        return d

    def _open_file(self, file_name):
        """
        открывает файл file_name в зависимости от типа (определяет по расширению)
        return: file-like объект
        """

        if os.path.splitext(file_name)[1] == '.gz':
            return gzip.open(file_name, 'r')
        else:
            return open(file_name, 'r')

    def _read_log_file(self, file_name):
        """
        читает построчно файл лога file_name
        return: list generator объект, каждый эл-т - dict, ключи соответствуют колонкам лога
        """

        try:
            f = self._open_file(file_name)
            try:
                for line in f:
                    yield self._parse_line(self._decode_line(line).strip())
            finally:
                f.close()
        except:
            logging.error('Ошибка чтения файла {0}'.format(file_name))
            raise

    def _analyze(self, worked_file):
        """
        Анализирует файл отчета worked_file.
        returns: list. Таблица для рендера в шаблон отчета
        """

        sum_count = 0
        total_count = 0
        sum_time = 0.0
        stat_data = {}

        for row in self._read_log_file(worked_file):
            total_count += 1
            # пропустим строки, которые не распарсились
            if not row['request']: continue
            sum_count += 1
            sum_time += row['request_time']

            if row['request'] in stat_data:
                stat_data[row['request']]['count'] += 1
                stat_data[row['request']]['time_sum'] += row['request_time']
                stat_data[row['request']]['time_avg'] = stat_data[row['request']]['time_sum'] / stat_data[
                    row['request']]['count']
                stat_data[row['request']]['time_max'] = max(stat_data[row['request']]['time_max'], row['request_time'])
                stat_data[row['request']]['time_med'] = statistics.median((stat_data[row['request']]['time_med'],
                    row['request_time']))
            else:
                stat_data[row['request']] = {
                    'url': row['request'],
                    'count': 1,
                    'count_perc': 0.0,
                    'time_sum': row['request_time'],
                    'time_perc': 0.0,
                    'time_avg': row['request_time'],
                    'time_max': row['request_time'],
                    'time_med': row['request_time']
                }

        if sum_count > 0:
            errors_prc = self._parse_errors / sum_count
        else:
            errors_prc = 0.0

        logging.info('Чтение завершено, обработано запросов: {0} из {1}, % ошибок {2:.3f}'.format(
            sum_count, total_count, errors_prc * 100))

        # проверим, если кол-во ошибок чтения превысило заданный порог - отчет не формируем
        if sum_count > 0 and errors_prc > self._max_parse_errors:
            return None

        # теперь нужно посчитать суммарные данные и поокруглять все float-ы
        logging.info('Подготовка данных отчета...')
        for key in stat_data:
            stat_data[key]['count_perc'] = round((stat_data[key]['count'] / sum_count) * 100.0, 3)
            stat_data[key]['time_perc'] = round((stat_data[key]['time_sum'] / sum_time) * 100.0, 3)
            stat_data[key]['time_sum'] = round(stat_data[key]['time_sum'], 3)
            stat_data[key]['time_avg'] = round(stat_data[key]['time_avg'], 3)
            stat_data[key]['time_med'] = round(stat_data[key]['time_med'], 3)

        # подготовка таблицы для внесения в отчет: сортируем массив по убыванию time_sum, обрезаем до заданной длины
        table = sorted([stat_data[key] for key in stat_data], key=lambda e: e['time_sum'], reverse=True)[:self._rep_sz]
        logging.info('Анализ завершен. Обнаружено {0} уникальных адресов'.format(len(stat_data)))
        return table

    def _write_report(self, report_name, table):
        """ Рендерит шаблон отчета данными из table, сохраняет отчет в файл report_name """

        try:
            with open(self._rep_tmpl_file, 'r') as f:
                rep_template = f.read()

            # рендерим темплат
            rep_template = rep_template.replace('$table_json', json.dumps(table))

            # сохраняем отчет
            if not os.path.exists(self._rep_dir):
                os.makedirs(self._rep_dir)
            with open(report_name, 'w') as f:
                f.write(rep_template)
        except:
            logging.exception('Ошибка формирования файла отчета')

    def create_report(self):
        """ Основной метод, с выполнения которого все начинается. """

        # определим обрабатываемый файл
        logging.info('Поиск файла лога для анализа')
        worked_file = self._get_curren_log()
        if not worked_file:
            logging.info('Не найдено логов для анализа')
            return

        logging.info('Найден лог: {0}'.format(os.path.split(worked_file)[1]))

        # генерим имя отчета (дата в имени отчета соответсвует дате в анализируемом файле лога)
        report_name = self._get_report_name(worked_file)
        logging.info('Будет сформирован отчет: {0}'.format(os.path.split(report_name)[1]))

        # читаем файл лога, парсим и считаем общие показатели: общее число запросов, суммарное время всех запросов
        logging.info('Чтение и анализ лога...')
        table = self._analyze(worked_file)
        # None возвращает, когда порог ошибок разбора строк превысил допустимый уровень
        if table is None:
            logging.info('Количество ошибок разбора строк превысило допустимый порог! Анализ остановлен')
            return

        # загружаем темплат отчета
        logging.info('Запись отчета')
        self._write_report(report_name, table)
