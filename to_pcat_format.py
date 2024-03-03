import numpy as np
import open3d as o3d
test_npy=np.load("test.npy")
test_bin=np.load("test.bin")
data=test_npy[test_bin[0]==10][:,:3]
pcd=o3d.geometry.PointCloud()
pcd.points=o3d.utility.Vector3dVector(data)
o3d.visualization.draw([pcd])
