# This example demonstrates how to regrid between a grid and a mesh.
# The grid and mesh files are required, they can be retrieved from the ESMF data repository:
#   wget http://www.earthsystemmodeling.org/download/data/ll1deg_grid.nc
#   wget http://www.earthsystemmodeling.org/download/data/mpas_uniform_10242_dual_counterclockwise.nc

import ESMF
import numpy

# Start up ESMF, this call is only necessary to enable debug logging
# esmpy = ESMF.Manager(debug=True)

from ESMF.test.test_api.mesh_utilities import mesh_create_5, mesh_create_5_parallel
from ESMF.test.test_api.locstream_utilities import create_locstream_16, create_locstream_16_parallel
if ESMF.pet_count() == 1:
    mesh, _, _, _, _ = mesh_create_5()
    locstream = create_locstream_16()
else:
    if ESMF.pet_count() is not 4:
        raise ValueError("processor count must be 4 or 1 for this example")
    else:
        mesh, _, _, _, _ = mesh_create_5_parallel()
        locstream = create_locstream_16_parallel()

# create a field
srcfield = ESMF.Field(mesh, name='srcfield')#, meshloc=ESMF.MeshLoc.ELEMENT)

# create a field on the locstream
dstfield = ESMF.Field(locstream, name='dstfield')
xctfield = ESMF.Field(locstream, name='xctfield')

# initialize the fields
[x, y] = [0, 1]
deg2rad = 3.14159/180

gridXCoord = srcfield.grid.get_coords(x)
gridYCoord = srcfield.grid.get_coords(y)
srcfield.data[...] = 10.0 + (gridXCoord * deg2rad) ** 2 + (gridYCoord * deg2rad) ** 2

gridXCoord = locstream["ESMF:X"]
gridYCoord = locstream["ESMF:Y"]
xctfield.data[...] = 10.0 + (gridXCoord * deg2rad) ** 2 + (gridYCoord * deg2rad) ** 2

dstfield.data[...] = 1e20

# create an object to regrid data from the source to the destination field
regrid = ESMF.Regrid(srcfield, dstfield,
                     regrid_method=ESMF.RegridMethod.BILINEAR,
                     unmapped_action=ESMF.UnmappedAction.ERROR)

# do the regridding from source to destination field
dstfield = regrid(srcfield, dstfield)


# compute the mean relative error
from operator import mul
num_nodes = reduce(mul, xctfield.shape)
relerr = 0
meanrelerr = 0
if num_nodes is not 0:
    ind = numpy.where((dstfield.data != 1e20) & (xctfield.data != 0))
    relerr = numpy.sum(numpy.abs(dstfield.data[ind] - xctfield.data[ind]) / numpy.abs(xctfield.data[ind]))
    meanrelerr = relerr / num_nodes

# handle the parallel case
if ESMF.pet_count() > 1:
    try:
        from mpi4py import MPI
    except:
        raise ImportError
    comm = MPI.COMM_WORLD
    relerr = comm.reduce(relerr, op=MPI.SUM)
    num_nodes = comm.reduce(num_nodes, op=MPI.SUM)

# output the results from one processor only
if ESMF.local_pet() is 0:
    meanrelerr = relerr / num_nodes
    print "ESMPy Grid Mesh Regridding Example"
    print "  interpolation mean relative error = {0}".format(meanrelerr)
