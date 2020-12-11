# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
from spack import *

class AmrWind(CMakePackage, CudaPackage):
    """ExaWind AMR-Wind block-structured, incompressible solver"""

    homepage = "https://exawind.github.io/amr-wind"
    git      = "https://github.com/exawind/amr-wind"

    maintainers = ['sayerhs', 'jrood-nrel', 'michaeljbrazell']

    version('development', branch='development', submodules=True)

    generator = ('Ninja'
                 if os.environ.get('EXAWIND_MAKE_TYPE','').lower() == 'ninja'
                 else 'Unix Makefiles')

    variant('unit', default=True,
            description="Build unit tests")
    variant('tests', default=True,
            description="Activate regression tests")
    variant('mpi', default=True,
            description='Enable MPI')
    variant('openmp', default=False,
            description='Enable OpenMP')
    variant('netcdf', default=True,
            description="Enable NetCDF support")
    variant('hypre', default=True,
            description="Enable hypre integration")
    variant('masa', default=False,
            description="Enable MASA integration")
    variant('internal-amrex', default=True,
            description="Use AMReX submodule to build")

    depends_on('ninja-fortran',
               type='build',
               when=(generator == 'Ninja'))

    depends_on('amrex', when='~internal-amrex')
    depends_on('mpi', when='+mpi')
    depends_on('netcdf-c', when='+netcdf')
    depends_on('hypre', when='+hypre')
    depends_on('masa', when='+masa')

    def process_cuda_args(self):
        """Process CUDA arch spec and convert it to AMReX format"""
        amrex_arch_map = {'20': '2.0', '21': '2.1', '30': '3.0', '32': '3.2',
                          '35': '3.5', '37': '3.7', '50': '5.0', '52': '5.2',
                          '53': '5.3', '60': '6.0', '61': '6.1', '62': '6.2',
                          '70': '7.0', '72': '7.2', '75': '7.5', '80': '8.0',
                          '86': '8.6'}

        cuda_arch = self.spec.variants['cuda_arch'].value
        try:
            amrex_arch = []
            for vv in cuda_arch:
                if vv in amrex_arch_map:
                    amrex_arch.append(amrex_arch_map[vv])
            return amrex_arch
        except:
            return []

    def cmake_args(self):
        define = CMakePackage.define

        args = [
            self.define_from_variant("AMR_WIND_ENABLE_%s"%v.upper(), v)
            for v in "mpi cuda openmp netcdf hypre masa tests".split()
        ]

        args += [
            define('CMAKE_EXPORT_COMPILE_COMMANDS', True),
            define('AMR_WIND_ENABLE_ALL_WARNINGS', True),
            define('AMR_WIND_TEST_WITH_FCOMPARE', '+tests' in self.spec),
        ]

        if '+cuda' in self.spec:
            amrex_arch = self.process_cuda_args()
            if amrex_arch:
                args.append(define('AMReX_CUDA_ARCH', ';'.join(amrex_arch)))

        if '+internal-amrex' in self.spec:
            args += [
                self.define('AMR_WIND_USE_INTERNAL_AMREX', True)
            ]
        else:
            args += [
                self.define('AMR_WIND_USE_INTERNAL_AMREX', False),
                self.define('AMReX_ROOT', self.spec['amrex'].prefix)
            ]

        return args
