from drongo import HttpResponseHeaders
from drongo import exceptions

from functools import partial
from datetime import datetime, timedelta

from wing_module import Module

import logging
import mimetypes
import os


__all__ = ['Static']


class Static(Module):
    """Drongo module that serves static files"""

    __default_config__ = {
        'base_url': '/static',
        'age': 300,
        'max_depth': 6
    }

    logger = logging.getLogger('wing_static')

    def init(self, config):
        self.logger.info('Initializing [static] module.')
        self.app.context.modules.static = self

        self.init_urls()

    def init_urls(self):
        parts = ['', '{a}', '{b}', '{c}', '{d}', '{e}', '{f}']
        for i in range(2, self.config.max_depth + 2):
            self.app.add_url(
                pattern=self.config.base_url + '/'.join(parts[:i]),
                call=self.serve_file)

    def chunks(self, path):
        with open(path, 'rb') as fd:
            for chunk in iter(partial(fd.read, 102400), b''):
                yield chunk

    def serve_file(self, ctx,
                   a=None, b=None, c=None, d=None, e=None, f=None):
        path = self.config.root_dir
        parts = [a, b, c, d, e, f]
        for part in parts:
            if part is not None:
                path = os.path.join(path, part)

        if os.path.exists(path) and not os.path.isdir(path):
            ctx.response.set_header(HttpResponseHeaders.CACHE_CONTROL,
                                    'max-age=%d' % self.config.age)

            expires = datetime.utcnow() + timedelta(seconds=(self.config.age))
            expires = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
            ctx.response.set_header(HttpResponseHeaders.EXPIRES, expires)

            ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'

            ctx.response.set_header(HttpResponseHeaders.CONTENT_TYPE, ctype)
            ctx.response.set_content(self.chunks(path), os.stat(path).st_size)

        else:
            self.logger.warn('Static file [{path}] not found!'.format(
                path=path))

            raise exceptions.NotFoundException()
