from src.pipeline_constructor.PipelineConstructor import PipelineConstructor
import open3d as o3d
import numpy as np

mesh = o3d.io.read_triangle_mesh("resources/3Dmodels/te.ply")

rotation = o3d.geometry.get_rotation_matrix_from_xyz([0,0,np.pi/2])

mesh.translate([0., 0., 0.], relative=True)
mesh.rotate(rotation, center=[0., 0., 0.])
axis=o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0)
o3d.visualization.draw_geometries([mesh,axis])
o3d.io.write_triangle_mesh("resources/3Dmodels/te3.ply", mesh)
