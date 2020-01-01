import os
from copy import deepcopy

from unittest import TestCase

from jinja2 import FileSystemLoader, Environment

# Path to the ESMF source directory. Templates are written relative to this path.
ESMF_DIR = os.environ['ESMF_DIR']

# This dictionary is passed to the template renderer.
META = {}

# The type definitions used in the templating. Many templated routines use this
# mapping when generating interfaces.
F = 'float'
D = 'double'
I = 'int'
L = 'long int'
ST = 'std::string'
B = 'bool'
A = 'ESMCI::Info'
THETYPES = {F: {'iso_ctype': 'C_FLOAT',
                'esmf_type': 'ESMF_KIND_R4',
                'json_type': 'number_float_t',
                'esmf_suffix': 'R4',
                'ftype': 'real',
                'ctype': F,
                'full_ftype': 'real(ESMF_KIND_R4)'},
            D: {'iso_ctype': 'C_DOUBLE',
                'esmf_type': 'ESMF_KIND_R8',
                'json_type': 'number_float_t',
                'esmf_suffix': 'R8',
                'ftype': 'real',
                'ctype': D,
                'full_ftype': 'real(ESMF_KIND_R8)'},
            I: {'iso_ctype': 'C_INT',
                'esmf_type': 'ESMF_KIND_I4',
                'json_type': 'number_integer_t',
                'esmf_suffix': 'I4',
                'ftype': 'integer',
                'ctype': I,
                'full_ftype': 'integer(ESMF_KIND_I4)'},
            L: {'iso_ctype': 'C_LONG',
                'esmf_type': 'ESMF_KIND_I8',
                'json_type': 'number_integer_t',
                'esmf_suffix': 'I8',
                'ftype': 'integer',
                'ctype': L,
                'full_ftype': 'integer(ESMF_KIND_I8)'},
            ST: {'iso_ctype': 'C_CHAR',
                'esmf_type': 'ESMF_TYPEKIND_CHARACTER',
                'json_type': 'string_t',
                'esmf_suffix': 'CH',
                'ftype': 'character',
                'ctype': ST,
                'full_ftype' : 'character(len=*)'},
            B: {'iso_ctype': 'C_BOOL',
                'esmf_type': 'ESMF_TYPEKIND_LOGICAL',
                'json_type': 'bool_t',
                'esmf_suffix': 'LG',
                'ftype': 'logical',
                'ctype': B,
                'full_ftype': 'logical'},
            # A: {'iso_ctype': 'C_PTR',
            #     'esmf_type': 'ESMF_Info',
            #     'json_type': 'object_t',
            #     'esmf_suffix': 'ATTRS',
            #     'ftype': 'type(ESMF_Info)',
            #     'ctype': A},
            }
META['THETYPES'] = THETYPES

# Root directory for the template files.
TEMPLATEFOLDER = 'templates'
META['TEMPLATEFOLDER'] = TEMPLATEFOLDER

# ESMF objects that require overloading. Must inherit from Base.
ESMF_TYPES = ["Array", "ArrayBundle", "CplComp", "GridComp", "SciComp",
              "DistGrid", "Field", "FieldBundle", "Grid", "State", "LocStream"]
META['ESMF_TYPES'] = ESMF_TYPES

# Objects holding a reference to Info objects
META['INFO_PARENT_TOKEN_OBJECT'] = "Obj"
META['INFO_PARENT_TOKEN_ATTPACK'] = "AP"

# Token used to indicate an overloaded interface is for a list
META['LIST_TOKEN'] = "List"

# Token used when indicating an interface used allocated arrays
META['ALLOC_TOKEN'] = "Allocated"

# Standard ESMF Fortran file header
META['ESMF_FILEHEADER'] = \
"""! $Id$
!
! Earth System Modeling Framework
! Copyright 2002-2019, University Corporation for Atmospheric Research,
! Massachusetts Institute of Technology, Geophysical Fluid Dynamics
! Laboratory, University of Michigan, National Centers for Environmental
! Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
! NASA Goddard Space Flight Center.
! Licensed under the University of Illinois-NCSA License.
!
!=============================================================================="""

# Standard ESMF C file header
META['ESMC_FILEHEADER'] = \
"""// $Id$
//
// Earth System Modeling Framework
// Copyright 2002-2019, University Corporation for Atmospheric Research,
// Massachusetts Institute of Technology, Geophysical Fluid Dynamics
// Laboratory, University of Michigan, National Centers for Environmental
// Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
// NASA Goddard Space Flight Center.
// Licensed under the University of Illinois-NCSA License.
//
//============================================================================="""

# ==============================================================================

class Runner(TestCase):

    def do_render(self, filename, template_folder=None, skip_types=None, **extra):
        """
        Render a standard template using `jinja2`. Method filters `THETYPES` before
        passing to the template renderer.

        `filename`  :: String template filename located in `TEMPLATEFOLDER`.
        `template_folder` :: Optional path to the root template folder directory.
        `skip_types`:: Optional string list of types to skip in the standard ESMF type definition.
        `extra`     :: Optional dictionary of additional arguments to pass to `template.render`.
        """
        if template_folder is None:
            template_folder = TEMPLATEFOLDER
        file_loader = FileSystemLoader(template_folder)
        env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
        template = env.get_template(filename)
        meta = deepcopy(META)
        if skip_types is not None:
            for s in skip_types:
                meta['THETYPES'].pop(s)
        ret = template.render(meta=meta, **extra)
        return ret

    def do_write(self, relpath, payload):
        esmf_path = os.path.expanduser(ESMF_DIR)
        full_path = os.path.join(esmf_path, 'src', relpath)
        with open(full_path, 'w') as f:
            f.write(payload)

    def test_ESMC_InfoCDefGeneric(self):
        ret = self.do_render('Info/ESMC_InfoCDefGeneric.jinja2')
        fn = 'Infrastructure/Base/src/ESMC_InfoCDefGeneric.C'
        self.do_write(fn, ret)

    def test_ESMF_InfoArrayUTest(self):
        for t in [D, F]:
            THETYPES[t]['desired'] = '(/ 1.0/3.0, 1.0/6.0, 1.0/12.0 /)'
        for ll in [I, L]:
            THETYPES[ll]['desired'] = '(/ 123, 456, 789 /)'
        skip = [ST, B]
        ret = self.do_render('Info/ESMF_InfoArrayUTest.jinja2', skip_types=skip)
        fn = 'Infrastructure/Base/tests/ESMF_InfoArrayUTest.F90'
        self.do_write(fn, ret)

    def test_ESMF_InfoCDefGeneric(self):
        ret = self.do_render('Info/ESMF_InfoCDefGeneric.jinja2')
        fn = 'Infrastructure/Base/interface/ESMF_InfoCDefGeneric.F90'
        self.do_write(fn, ret)

    def test_ESMF_Info(self):
        ret = self.do_render('Info/ESMF_Info.jinja2')
        fn = 'Infrastructure/Base/interface/ESMF_Info.F90'
        self.do_write(fn, ret)

    def test_ESMF_InfoSync(self):
        state = {"sync_types": ["CplComp", "GridComp", "SciComp", "Field",
                                "FieldBundle", "State"],
                 }

        r = self.do_render("Info/ESMF_InfoSync.jinja2", state=state)
        # print(r)
        self.do_write("Superstructure/InfoAPI/interface/ESMF_InfoSync.F90", r)

    def test_ESMF_Attribute(self):
        tf = os.path.join(TEMPLATEFOLDER, "Attribute")
        ret = self.do_render('ESMF_Attribute.jinja2', template_folder=tf)
        self.do_write("Superstructure/AttributeAPI/interface/ESMF_Attribute.F90", ret)
