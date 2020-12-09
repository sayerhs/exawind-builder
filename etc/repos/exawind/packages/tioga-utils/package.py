# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import sys
from spack import *

class TiogaUtils(CMakePackage, CudaPackage):
    """ExaWind TIOGA utilities"""

    homepage = "https://github.com/sayerhs/tioga_utils"
    git      = "https://github.com/sayerhs/tioga_utils.git"

    maintainers = ['sayerhs']

    version('exawind', branch='exawind', submodules=True)

    variant('shared', default=(sys.platform != 'darwin'),
            description='Build shared libraries')
    variant('pic', default=True,
            description="Position independent code")
    variant('nalu', default=False,
            description="Link to Nalu-Wind")

    depends_on('cuda', when='+cuda')
    depends_on('kokkos-nvcc-wrapper', when='+cuda')
    depends_on('trilinos')
    depends_on('tioga')
    depends_on('yaml-cpp')
    depends_on('nalu-wind', when='+nalu')

    def cmake_args(self):
        spec = self.spec
        define = CMakePackage.define

        args = [
            define('BUILD_SHARED_LIBS', '+shared' in spec),
            define('CMAKE_POSITION_INDEPENDENT_CODE', '+pic' in spec),
            define('Trilinos_DIR', spec['trilinos'].prefix),
            define('TIOGA_DIR', spec['tioga'].prefix),
            define('YAML_DIR', spec['yaml-cpp'].prefix),
            define('ENABLE_NALU', '+nalu' in spec),
        ]

        if '+nalu' in spec:
            args.append(define('NALU_DIR', spec['nalu-wind'].prefix))

        if 'darwin' in spec.architecture:
            args.append(define('CMAKE_MACOSX_RPATH', True))
        return args
