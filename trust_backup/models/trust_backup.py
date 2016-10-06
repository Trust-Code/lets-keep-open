# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015 Trustcode - www.trustcode.com.br                         #
#              Danimar Ribeiro <danimaribeiro@gmail.com>                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

from openerp.osv import orm, fields
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import socket
import os
import time
import logging
import openerp.tools as tools
import subprocess
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


def execute(connector, method, *args):
    res = False
    try:
        res = getattr(connector, method)(*args)
    except socket.error as e:
        raise e
    return res


class BackupExecuted(orm.Model):
    _name = 'backup.executed'
    _order = 'backup_date'

    def _generate_s3_link(self):
        return self.s3_id

    _columns = {
        'name': fields.char('Arquivo', size=100),
        'configuration_id': fields.many2one('trust.backup', string="Configuração"),
        'backup_date': fields.datetime(string="Data"),
        'local_path': fields.char(string="Caminho Local", readonly=True),
        's3_id': fields.char(string="S3 Id", readonly=True),
        's3_url': fields.char("Link S3", compute='_generate_s3_link', readonly=True),
        'state': fields.selection(
            string="Estado", default='not_started',
            selection=[('not_started', 'Não iniciado'),
                       ('executing', 'Executando'),
                       ('sending', 'Enviando'),
                       ('error', 'Erro'), ('concluded', 'Concluído')])

    }


class TrustBackup(orm.Model):
    _name = 'trust.backup'

    _columns = {
        'database_name': fields.char(string='Banco de dados', size=100),
        'interval': fields.selection(
            string=u"Período",
            selection=[('hora', '1 hora'), ('seis', '6 horas'),
                       ('doze', '12 horas'), ('diario', u'Diário')]),
        'send_to_s3': fields.boolean('Enviar Amazon S3 ?'),
        'aws_access_key': fields.char(string="Chave API S3", size=100),
        'aws_secret_key': fields.char(string="Chave Secreta API S3", size=100),
        'backup_dir': fields.char(string=u"Diretório", size=300),
        'next_backup': fields.datetime(string=u"Próximo Backup")
    }

    _defaults = {
        'backup_dir': '/opt/backups/database/',
    }

    def _set_next_backup(self, rec):
        if rec.interval == 'hora':
            rec.write({'next_backup': datetime.now() + timedelta(hours=1)})
        elif rec.interval == 'seis':
            rec.write({'next_backup': datetime.now() + timedelta(hours=6)})
        elif rec.interval == 'doze':
            rec.write({'next_backup': datetime.now() + timedelta(hours=12)})
        else:
            rec.write({'next_backup': datetime.now() + timedelta(days=1)})

    def schedule_backup(self, cr, uid, context=None):
        confs = self.search(cr, uid, [], context=context)
        for rec in self.browse(cr, uid, confs, context=context):

            if rec.next_backup:
                next_backup = datetime.strptime(
                    rec.next_backup[:19],
                    '%Y-%m-%d %H:%M:%S')
            else:
                next_backup = datetime.now()
            if next_backup < datetime.now():
                try:
                    if not os.path.isdir(rec.backup_dir):
                        os.makedirs(rec.backup_dir)
                except:
                    raise
                zip_name = '%s_%s.backup' % (rec.database_name,
                                             time.strftime('%Y%m%d_%H_%M_%S'))
                zip_file = '%s/%s' % (rec.backup_dir, zip_name)

                env = os.environ.copy()
                env['PGHOST'] = tools.config['db_host'] or 'localhost'
                env['PGPORT'] = str(tools.config['db_port'] or 5432)
                env['PGUSER'] = tools.config['db_user']
                env['PGPASSWORD'] = tools.config['db_password']

                cmds = ['pg_dump', '-Fc', rec.database_name, '-f', zip_file]
                if datetime.now().weekday() != 6:
                    cmds += ['--exclude-table-data', 'ir_attachment']
                ps = subprocess.Popen(
                     cmds, stdout=subprocess.PIPE, env=env,
                )
                output = ps.communicate()[0]
                for line in output.splitlines():
                    _logger.error(line)

                backup_env = self.pool['backup.executed']
                if rec.send_to_s3:
                    key = rec.send_for_amazon_s3(zip_file, zip_name,
                                                 rec.database_name)
                    loc = ''
                    if not key:
                        key = 'Erro ao enviar para o Amazon S3'
                        loc = zip_file
                    else:
                        loc = 'https://s3.amazonaws.com/%s_bkp_pelican/%s' % (
                            rec.database_name, key
                        )
                    backup_env.create(cr, uid, {
                        'backup_date': datetime.now(),
                        'configuration_id': rec.id,
                        's3_id': key, 'name': zip_name,
                        'state': 'concluded',
                        'local_path': loc}, context=context)
                    if key:
                        os.remove(zip_file)
                else:
                    backup_env.create(cr, uid, {
                        'backup_date': datetime.now(), 'name': zip_name,
                        'configuration_id': rec.id, 'state': 'concluded',
                        'local_path': zip_file}, context=context)
                self._set_next_backup(rec)

    def send_for_amazon_s3(self, cr, uid, ids, file_to_send,
                           name_to_store, database):
        try:
            rec = self.browse(cr, uid, ids[0])
            if rec.aws_access_key and rec.aws_secret_key:
                access_key = rec.aws_access_key
                secret_key = rec.aws_secret_key

                conexao = S3Connection(access_key, secret_key)
                bucket_name = '%s_bkp_pelican' % database
                bucket = conexao.create_bucket(bucket_name)

                k = Key(bucket)
                k.key = name_to_store
                k.set_contents_from_filename(file_to_send)
                return k.key
            else:
                _logger.error(
                    u'Configurações do Amazon S3 não setadas, \
                    pulando armazenamento de backup')
        except Exception:
            _logger.error('Erro ao enviar dados para S3', exc_info=True)
