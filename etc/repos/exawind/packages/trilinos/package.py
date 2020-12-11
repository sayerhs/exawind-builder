# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
from spack import *
from spack.pkg.builtin.trilinos import Trilinos as TrilinosBase

class Trilinos(TrilinosBase):
    """ExaWind Trilinos configuration"""

    generator = ('Ninja'
                 if os.environ.get('EXAWIND_MAKE_TYPE','').lower() == 'ninja'
                 else 'Unix Makefiles')

    depends_on('ninja-fortran',
               when=(os.environ.get('EXAWIND_MAKE_TYPE') == 'Ninja'))

    def cmake_args(self):
        args = super(Trilinos, self).cmake_args()

        if '%intel' in self.spec:
            args.append(self.define('Trilinos_ENABLE_STKTools', False))

        return args
