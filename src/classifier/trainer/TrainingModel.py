import pathlib

import numpy as np
import open3d as o3d
import json

from src.core.PointCloud import PointCloud
from src.core.Point import Point
from src.graph_creator.core.PipelineGraph import PipelineGraph
from src.graph_creator.GraphCreator import GraphCreator
from src.pipeline_constructor.PipelineConstructor import PipelineConstructor
from src.core.PartType import EnumEncoder, as_part_type

from copy import deepcopy


class TrainingModel:

    def __init__(self, pipeline_graph: PipelineGraph = None, nb_points_per_mesh: int = 50,
                 json_file: str = None) -> None:
        resource_dir = pathlib.Path(__file__).parent.parent.parent.parent / "resources" / "3Dmodels"
        self._point_cloud_model = o3d.geometry.PointCloud()
        self._mesh = o3d.geometry.TriangleMesh()

        self._pipeline_graph = pipeline_graph

        if json_file is not None:
            with open(json_file) as file:
                json_str = file.read()
                data = json.loads(json.loads(json_str))

                points = []
                points_coordinates = []

                for point in data["points"]:
                    coordinates = point["point_coordinates"]
                    part_type = as_part_type(point["part_type"])
                    center = point["part_center"]
                    direction = point["direction"]
                    radius = point["radius"]

                    points_coordinates.append([coordinates[0], coordinates[1], coordinates[2]])

                    label_point = Point(coordinates[0], coordinates[1], coordinates[2])

                    label_point.part_type = part_type
                    label_point.center = center
                    label_point.direction = direction
                    label_point.radius = radius

                    points.append(label_point)

                self._point_cloud_unlabelled = PointCloud(points)
                self._point_cloud_labelled = PointCloud(deepcopy(points))
                self._point_cloud_model.points = o3d.utility.Vector3dVector(np.asarray(points_coordinates))

                self._point_cloud_unlabelled.clear_labels()
        else:
            pipeline_constructor = PipelineConstructor()

            all_points = []
            npy_all_points=np.empty((0, 6))
            all_labels = []
            for node in pipeline_graph.graph.nodes:
                part_type = pipeline_graph.graph.nodes[node]['type']

                if 1 <= part_type.value <= 3:
                    all_labels = np.concatenate([all_labels, np.full(nb_points_per_mesh, 0)])
                elif 4 <= part_type.value <= 5:
                    all_labels = np.concatenate([all_labels, np.full(nb_points_per_mesh, 1)])
                elif 6 <= part_type.value <= 8:
                    all_labels = np.concatenate([all_labels, np.full(nb_points_per_mesh, 2)])
                elif 9 <= part_type.value <= 12:
                    all_labels = np.concatenate([all_labels, np.full(nb_points_per_mesh, 3)])

                coordinates = pipeline_graph.graph.nodes[node]['coordinates']
                direction = pipeline_graph.graph.nodes[node]['direction']

                mesh = pipeline_constructor.create_mesh(part_type, coordinates, direction)
                point_cloud = mesh.sample_points_uniformly(nb_points_per_mesh)
                full_points=np.hstack((np.asarray(point_cloud.points), np.ones_like(np.asarray(point_cloud.points))))
                npy_all_points=np.vstack((npy_all_points, full_points))

                for point in point_cloud.points:
                    label_point = Point(point[0], point[1], point[2])

                    label_point.part_type = part_type
                    label_point.center = coordinates
                    label_point.direction = direction
                    label_point.radius = 1.

                    all_points.append(label_point)

                self._point_cloud_model += point_cloud
                self._mesh += mesh

            zeros=np.zeros(all_labels.shape[0])
            all_labels=np.stack((all_labels,zeros),axis=0)
            all_labels=all_labels.astype(int)
            self.all_labels=all_labels
            self.npy_all_points=npy_all_points

            self._point_cloud_unlabelled = PointCloud(all_points)
            self._point_cloud_labelled = PointCloud(deepcopy(all_points))

            self._point_cloud_unlabelled.clear_labels()

    @property
    def point_cloud_model(self):
        return self._point_cloud_model

    @property
    def point_cloud_labelled(self):
        return self._point_cloud_labelled

    @property
    def point_cloud_unlabelled(self):
        return self._point_cloud_unlabelled

    @property
    def model_graph(self):
        return self._pipeline_graph

    def visualize(self):
        o3d.visualization.draw_geometries([self._point_cloud_model])

    def save_mesh(self, file_path: str) -> None:
        o3d.io.write_triangle_mesh(file_path, self._mesh)

    def save_pcd(self, file_path: str) -> None:
        o3d.io.write_point_cloud(file_path, self._point_cloud_model)

    def save_file(self, npy_path: str,bin_path: str) -> None:
        np.save(npy_path,self.npy_all_points)
        with open(bin_path, 'wb') as f:
            np.save(f, self.all_labels.astype(np.uint16))

    def save_model(self, file_path: str) -> None:
        data = []

        for point in self._point_cloud_labelled.points:
            data.append({
                "point_coordinates": [point.x, point.y, point.z],
                "part_center": [point.center[0], point.center[1], point.center[2]],
                "part_type": point.part_type,
                "direction": [point.direction[0], point.direction[1], point.direction[2]],
                "radius": point.radius
            })

        json_data = {"points": data}
        json_string = json.dumps(json_data, cls=EnumEncoder)

        with open(file_path, 'w') as outfile:
            json.dump(json_string, outfile)


def create_training_model(nb_parts: int = 50, nb_points_per_mesh: int = 50) -> TrainingModel:
    graph_creator = GraphCreator()
    pipeline_graph = graph_creator.create_random_graph(nb_parts)

    training_model = TrainingModel(pipeline_graph, nb_points_per_mesh)

    return training_model
