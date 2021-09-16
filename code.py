import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
import itertools
from random import randint
import maya.cmds as cmds
import maya.mel as mel
import time


class OpenMayaUtils:
    @staticmethod
    def get_mesh_creation_data(mesh_dag_path):

        """
        Returns all mesh data, which needed to recreate surface.
        :param mesh_dag_path: string with node dag_path
        :returns result: dict with all mesh creation data.
        """

        result = dict()

        selection_list = OpenMaya.MSelectionList()
        selection_list.add(mesh_dag_path)
        dag_path = OpenMaya.MDagPath()
        selection_list.getDagPath(0, dag_path)
        mfn_mesh = OpenMaya.MFnMesh(dag_path)

        vertex_positions = OpenMayaUtils.get_vertex_pos_of_mesh(mfn_mesh)
        polygon_vertex_ids = OpenMayaUtils.get_polygon_vertex_ids(mfn_mesh)
        number_of_vertices_per_polygon = [len(x) for x in polygon_vertex_ids]

        flatten = itertools.chain.from_iterable
        vertex_indexes_per_polygon = list(flatten(polygon_vertex_ids))

        result["vertex_positions"] = vertex_positions
        result["number_of_vertices_per_polygon"] = number_of_vertices_per_polygon
        result["vertex_indexes_per_polygon"] = vertex_indexes_per_polygon
        result["numPolygons"] = mfn_mesh.numPolygons()

        return result

    @staticmethod
    def get_vertex_pos_of_mesh(mfn_mesh, as_mpoint_array=False):

        """
        Returns vertex positions of given mesh.
        :param mesh: string dag path to mesh
        :param as_mpoint_array: if True, function will return vertex positions as array of OpenMaya.MPoint objects, 
                                by defaul False mean it will return vertex positions as as floats array
        :returns list: by default returns list of integers with point coordinates, with as_mpoint_array=True will returns list of MPoint objects.
        """

        if mfn_mesh:
            mpoint_array = OpenMaya.MPointArray()
            mfn_mesh.getPoints(mpoint_array)

            if as_mpoint_array:
                return mpoint_array
            else:
                point_list = OpenMayaUtils.convert_mpoint_array_to_float_list_array(mpoint_array)
                return point_list

    @staticmethod
    def convert_mpoint_array_to_float_list_array(mpoints_array):
        floats_list = []
        if mpoints_array:
            for i in range(mpoints_array.length()):
                mpoint = mpoints_array[i]
                temp_list = []
                for j in range(4):
                    temp_list.append(mpoint(j))
                floats_list.append(temp_list)

        return floats_list

    @staticmethod
    def get_polygon_vertex_ids(mfn_mesh):

        """
        Returns polygon vertex ids for given mesh. 
        (what vertex each polygon have, vertex defined by vertex id)
        :param mesh: string dag path to mesh
        :returns list: list of vertex id's per polygon
        """

        if mfn_mesh:
            nums_of_polygons = mfn_mesh.numPolygons()

            result = []
            if nums_of_polygons:
                for poly_id in range(nums_of_polygons):
                    vertCountForPoly = OpenMaya.MIntArray()
                    mfn_mesh.getPolygonVertices(poly_id, vertCountForPoly)
                    result.append(list(vertCountForPoly))

            return result

    @staticmethod
    def convert_float_lists_array_to_mpoints_array(float_list_array):

        """
        Converts given list of lists with float coordinates to list of MPoint objects

        :param float_list_array: list of integer lists
        :returns vertex_positions_mpoints: list of MPoint objects.
        """

        mfloat_point_array = OpenMaya.MFloatPointArray()
        if float_list_array:
            for vertex_coords_list in float_list_array:
                mpoint_object = OpenMaya.MFloatPoint(*vertex_coords_list)
                mfloat_point_array.append(mpoint_object)

        return mfloat_point_array

    @staticmethod
    def convert_floats_to_MIntArray(floats_array):
        m_int_array_obj = OpenMaya.MIntArray()
        if floats_array:
            for v in floats_array:
                m_int_array_obj.append(v)

        return m_int_array_obj

    @staticmethod
    def create_mesh(polygon_count, vertex_positions_raw_data, number_of_vertices_per_polygon,
                    vertex_indexes_per_polygon, parent_mobj = None):

        vertex_positions_mfloatpoints = OpenMayaUtils.convert_float_lists_array_to_mpoints_array(
            vertex_positions_raw_data)
        meshFn = OpenMaya.MFnMesh()

        try:
            vertex_count = vertex_positions_mfloatpoints.length()
            polygon_count = polygon_count
            polygon_counts = OpenMayaUtils.convert_floats_to_MIntArray(number_of_vertices_per_polygon)
            polygon_connects = OpenMayaUtils.convert_floats_to_MIntArray(vertex_indexes_per_polygon)
            if parent_mobj:
                createdMobject = meshFn.create(vertex_count, polygon_count, vertex_positions_mfloatpoints, polygon_counts,
                                               polygon_connects, parent_mobj)
            else:
                createdMobject = meshFn.create(vertex_count, polygon_count, vertex_positions_mfloatpoints, polygon_counts,
                                               polygon_connects)
            return createdMobject
        except Exception as e:
            print(e)

    @staticmethod
    def make_depend_node(name):
        node = None
        if name:
            selList = OpenMaya.MSelectionList()
            selList.add(name)
            node = OpenMaya.MObject()
            selList.getDependNode(0, node)

        return node

    @staticmethod
    def get_plug_by_name(inObj, inPlugName):
        """
        Gets a node's plug as an MPlug.
        
        @inObj: MObject. Node to get plug from.
        @inPlugName: String. Name of plug to get from node.
        @return: MPlug.
        @return: None.
        """
        depFn = OpenMaya.MFnDependencyNode(inObj)
        try:
            plug = depFn.findPlug(inPlugName)
            return plug
        except:
            print("errror")
            return None

    @staticmethod
    def connect_nodes(source_obj, source_plug_name, destination_obj, destination_plug_name):
        '''
        @param source_obj: MObject. Source object.
        @param source_plug_name: String. Name of plug on parent node.
        @param destination_obj: MObject. Destination object.
        @param destination_plug_name: String. Name of plug on child node.
        '''
        source_plug = OpenMayaUtils.get_plug_by_name(source_obj, source_plug_name)
        destination_plug = OpenMayaUtils.get_plug_by_name(destination_obj, destination_plug_name)
        MDGMod = OpenMaya.MDGModifier()
        MDGMod.connect(source_plug, destination_plug)
        MDGMod.doIt()

    @staticmethod
    def convert_floats_matrix_to_MMatrix(floats_matrix):
        if floats_matrix:
            mmatrix = OpenMaya.MMatrix()
            for i in range(4):
                for j in range(4):
                    OpenMaya.MScriptUtil.setDoubleArray(mmatrix[i], j, floats_matrix[i][j])

            return mmatrix

    @staticmethod
    def get_obj_floats_transform_matrix(mobject):
        if mobject:
            mfn_transform = OpenMaya.MFnTransform(mobject)
            mtranform_matrix = mfn_transform.transformation()
            mmatrix = mtranform_matrix.asMatrix()

            new_matrix = []
            for i in range(4):
                temp_array = []
                for j in range(4):
                    temp_array.append(mmatrix(i, j))
                new_matrix.append(temp_array)

            return new_matrix


class Field:
    number_of_vertices_per_polygon = \
        [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
         4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
         4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
         4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
         4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
         4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
         4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]

    vertex_indexes_per_polygon = \
        [0, 1, 12, 11, 1, 2, 13, 12, 2, 3, 14, 13, 3, 4, 15, 14, 4, 5, 16, 15, 5, 6, 17, 16, 6, 7, 18, 17, 7, 8, 19, 18,
         8, 9, 20, 19, 9, 10, 21, 20, 11, 12, 23, 22, 12, 13, 24, 23, 13, 14, 25, 24, 14, 15, 26, 25, 15, 16, 27, 26,
         16, 17, 28, 27, 17, 18, 29, 28, 18, 19, 30, 29, 19, 20, 31, 30, 20, 21, 32, 31, 22, 23, 34, 33, 23, 24, 35, 34,
         24, 25, 36, 35, 25, 26, 37, 36, 26, 27, 38, 37, 27, 28, 39, 38, 28, 29, 40, 39, 29, 30, 41, 40, 30, 31, 42, 41,
         31, 32, 43, 42, 33, 34, 45, 44, 34, 35, 46, 45, 35, 36, 47, 46, 36, 37, 48, 47, 37, 38, 49, 48, 38, 39, 50, 49,
         39, 40, 51, 50, 40, 41, 52, 51, 41, 42, 53, 52, 42, 43, 54, 53, 44, 45, 56, 55, 45, 46, 57, 56, 46, 47, 58, 57,
         47, 48, 59, 58, 48, 49, 60, 59, 49, 50, 61, 60, 50, 51, 62, 61, 51, 52, 63, 62, 52, 53, 64, 63, 53, 54, 65, 64,
         55, 56, 67, 66, 56, 57, 68, 67, 57, 58, 69, 68, 58, 59, 70, 69, 59, 60, 71, 70, 60, 61, 72, 71, 61, 62, 73, 72,
         62, 63, 74, 73, 63, 64, 75, 74, 64, 65, 76, 75, 66, 67, 78, 77, 67, 68, 79, 78, 68, 69, 80, 79, 69, 70, 81, 80,
         70, 71, 82, 81, 71, 72, 83, 82, 72, 73, 84, 83, 73, 74, 85, 84, 74, 75, 86, 85, 75, 76, 87, 86, 77, 78, 89, 88,
         78, 79, 90, 89, 79, 80, 91, 90, 80, 81, 92, 91, 81, 82, 93, 92, 82, 83, 94, 93, 83, 84, 95, 94, 84, 85, 96, 95,
         85, 86, 97, 96, 86, 87, 98, 97, 88, 89, 100, 99, 89, 90, 101, 100, 90, 91, 102, 101, 91, 92, 103, 102, 92, 93,
         104, 103, 93, 94, 105, 104, 94, 95, 106, 105, 95, 96, 107, 106, 96, 97, 108, 107, 97, 98, 109, 108, 99, 100,
         111, 110, 100, 101, 112, 111, 101, 102, 113, 112, 102, 103, 114, 113, 103, 104, 115, 114, 104, 105, 116, 115,
         105, 106, 117, 116, 106, 107, 118, 117, 107, 108, 119, 118, 108, 109, 120, 119, 110, 111, 122, 121, 111, 112,
         123, 122, 112, 113, 124, 123, 113, 114, 125, 124, 114, 115, 126, 125, 115, 116, 127, 126, 116, 117, 128, 127,
         117, 118, 129, 128, 118, 119, 130, 129, 119, 120, 131, 130, 121, 122, 133, 132, 122, 123, 134, 133, 123, 124,
         135, 134, 124, 125, 136, 135, 125, 126, 137, 136, 126, 127, 138, 137, 127, 128, 139, 138, 128, 129, 140, 139,
         129, 130, 141, 140, 130, 131, 142, 141, 132, 133, 144, 143, 133, 134, 145, 144, 134, 135, 146, 145, 135, 136,
         147, 146, 136, 137, 148, 147, 137, 138, 149, 148, 138, 139, 150, 149, 139, 140, 151, 150, 140, 141, 152, 151,
         141, 142, 153, 152, 143, 144, 155, 154, 144, 145, 156, 155, 145, 146, 157, 156, 146, 147, 158, 157, 147, 148,
         159, 158, 148, 149, 160, 159, 149, 150, 161, 160, 150, 151, 162, 161, 151, 152, 163, 162, 152, 153, 164, 163,
         154, 155, 166, 165, 155, 156, 167, 166, 156, 157, 168, 167, 157, 158, 169, 168, 158, 159, 170, 169, 159, 160,
         171, 170, 160, 161, 172, 171, 161, 162, 173, 172, 162, 163, 174, 173, 163, 164, 175, 174, 165, 166, 177, 176,
         166, 167, 178, 177, 167, 168, 179, 178, 168, 169, 180, 179, 169, 170, 181, 180, 170, 171, 182, 181, 171, 172,
         183, 182, 172, 173, 184, 183, 173, 174, 185, 184, 174, 175, 186, 185, 176, 177, 188, 187, 177, 178, 189, 188,
         178, 179, 190, 189, 179, 180, 191, 190, 180, 181, 192, 191, 181, 182, 193, 192, 182, 183, 194, 193, 183, 184,
         195, 194, 184, 185, 196, 195, 185, 186, 197, 196, 187, 188, 199, 198, 188, 189, 200, 199, 189, 190, 201, 200,
         190, 191, 202, 201, 191, 192, 203, 202, 192, 193, 204, 203, 193, 194, 205, 204, 194, 195, 206, 205, 195, 196,
         207, 206, 196, 197, 208, 207, 198, 199, 210, 209, 199, 200, 211, 210, 200, 201, 212, 211, 201, 202, 213, 212,
         202, 203, 214, 213, 203, 204, 215, 214, 204, 205, 216, 215, 205, 206, 217, 216, 206, 207, 218, 217, 207, 208,
         219, 218, 209, 210, 221, 220, 210, 211, 222, 221, 211, 212, 223, 222, 212, 213, 224, 223, 213, 214, 225, 224,
         214, 215, 226, 225, 215, 216, 227, 226, 216, 217, 228, 227, 217, 218, 229, 228, 218, 219, 230, 229, 1, 0, 231,
         232, 0, 11, 233, 231, 2, 1, 232, 234, 3, 2, 234, 235, 4, 3, 235, 236, 5, 4, 236, 237, 6, 5, 237, 238, 7, 6,
         238, 239, 8, 7, 239, 240, 9, 8, 240, 241, 10, 9, 241, 242, 21, 10, 242, 243, 11, 22, 244, 233, 32, 21, 243,
         245, 22, 33, 246, 244, 43, 32, 245, 247, 33, 44, 248, 246, 54, 43, 247, 249, 44, 55, 250, 248, 65, 54, 249,
         251, 55, 66, 252, 250, 76, 65, 251, 253, 66, 77, 254, 252, 87, 76, 253, 255, 77, 88, 256, 254, 98, 87, 255,
         257, 88, 99, 258, 256, 109, 98, 257, 259, 99, 110, 260, 258, 120, 109, 259, 261, 110, 121, 262, 260, 131, 120,
         261, 263, 121, 132, 264, 262, 142, 131, 263, 265, 132, 143, 266, 264, 153, 142, 265, 267, 143, 154, 268, 266,
         164, 153, 267, 269, 154, 165, 270, 268, 175, 164, 269, 271, 165, 176, 272, 270, 186, 175, 271, 273, 176, 187,
         274, 272, 197, 186, 273, 275, 187, 198, 276, 274, 208, 197, 275, 277, 198, 209, 278, 276, 219, 208, 277, 279,
         209, 220, 280, 278, 230, 219, 279, 281]

    vertex_positions_raw_data = \
        [[-8.860343933105469, 0.0, 10.977370262145996, 1.0], [-7.860344886779785, 0.0, 10.977370262145996, 1.0],
         [-6.860344409942627, 0.0, 10.977370262145996, 1.0], [-5.860343933105469, 0.0, 10.977370262145996, 1.0],
         [-4.860344409942627, 0.0, 10.977370262145996, 1.0], [-3.860344409942627, 0.0, 10.977370262145996, 1.0],
         [-2.8603439331054688, 0.0, 10.977370262145996, 1.0], [-1.860344409942627, 0.0, 10.977370262145996, 1.0],
         [-0.8603441715240479, 0.0, 10.977370262145996, 1.0], [0.13965606689453125, 0.0, 10.977370262145996, 1.0],
         [1.1396558284759521, 0.0, 10.977370262145996, 1.0], [-8.860343933105469, 0.0, 9.977370262145996, 1.0],
         [-7.860344886779785, 0.0, 9.977370262145996, 1.0], [-6.860344409942627, 0.0, 9.977370262145996, 1.0],
         [-5.860343933105469, 0.0, 9.977370262145996, 1.0], [-4.860344409942627, 0.0, 9.977370262145996, 1.0],
         [-3.860344409942627, 0.0, 9.977370262145996, 1.0], [-2.8603439331054688, 0.0, 9.977370262145996, 1.0],
         [-1.860344409942627, 0.0, 9.977370262145996, 1.0], [-0.8603441715240479, 0.0, 9.977370262145996, 1.0],
         [0.13965606689453125, 0.0, 9.977370262145996, 1.0], [1.1396558284759521, 0.0, 9.977370262145996, 1.0],
         [-8.860343933105469, 0.0, 8.977370262145996, 1.0], [-7.860344886779785, 0.0, 8.977370262145996, 1.0],
         [-6.860344409942627, 0.0, 8.977370262145996, 1.0], [-5.860343933105469, 0.0, 8.977370262145996, 1.0],
         [-4.860344409942627, 0.0, 8.977370262145996, 1.0], [-3.860344409942627, 0.0, 8.977370262145996, 1.0],
         [-2.8603439331054688, 0.0, 8.977370262145996, 1.0], [-1.860344409942627, 0.0, 8.977370262145996, 1.0],
         [-0.8603441715240479, 0.0, 8.977370262145996, 1.0], [0.13965606689453125, 0.0, 8.977370262145996, 1.0],
         [1.1396558284759521, 0.0, 8.977370262145996, 1.0], [-8.860343933105469, 0.0, 7.977370262145996, 1.0],
         [-7.860344886779785, 0.0, 7.977370262145996, 1.0], [-6.860344409942627, 0.0, 7.977370262145996, 1.0],
         [-5.860343933105469, 0.0, 7.977370262145996, 1.0], [-4.860344409942627, 0.0, 7.977370262145996, 1.0],
         [-3.860344409942627, 0.0, 7.977370262145996, 1.0], [-2.8603439331054688, 0.0, 7.977370262145996, 1.0],
         [-1.860344409942627, 0.0, 7.977370262145996, 1.0], [-0.8603441715240479, 0.0, 7.977370262145996, 1.0],
         [0.13965606689453125, 0.0, 7.977370262145996, 1.0], [1.1396558284759521, 0.0, 7.977370262145996, 1.0],
         [-8.860343933105469, 0.0, 6.977370262145996, 1.0], [-7.860344886779785, 0.0, 6.977370262145996, 1.0],
         [-6.860344409942627, 0.0, 6.977370262145996, 1.0], [-5.860343933105469, 0.0, 6.977370262145996, 1.0],
         [-4.860344409942627, 0.0, 6.977370262145996, 1.0], [-3.860344409942627, 0.0, 6.977370262145996, 1.0],
         [-2.8603439331054688, 0.0, 6.977370262145996, 1.0], [-1.860344409942627, 0.0, 6.977370262145996, 1.0],
         [-0.8603441715240479, 0.0, 6.977370262145996, 1.0], [0.13965606689453125, 0.0, 6.977370262145996, 1.0],
         [1.1396558284759521, 0.0, 6.977370262145996, 1.0], [-8.860343933105469, 0.0, 5.977370262145996, 1.0],
         [-7.860344886779785, 0.0, 5.977370262145996, 1.0], [-6.860344409942627, 0.0, 5.977370262145996, 1.0],
         [-5.860343933105469, 0.0, 5.977370262145996, 1.0], [-4.860344409942627, 0.0, 5.977370262145996, 1.0],
         [-3.860344409942627, 0.0, 5.977370262145996, 1.0], [-2.8603439331054688, 0.0, 5.977370262145996, 1.0],
         [-1.860344409942627, 0.0, 5.977370262145996, 1.0], [-0.8603441715240479, 0.0, 5.977370262145996, 1.0],
         [0.13965606689453125, 0.0, 5.977370262145996, 1.0], [1.1396558284759521, 0.0, 5.977370262145996, 1.0],
         [-8.860343933105469, 0.0, 4.977369785308838, 1.0], [-7.860344886779785, 0.0, 4.977369785308838, 1.0],
         [-6.860344409942627, 0.0, 4.977369785308838, 1.0], [-5.860343933105469, 0.0, 4.977369785308838, 1.0],
         [-4.860344409942627, 0.0, 4.977369785308838, 1.0], [-3.860344409942627, 0.0, 4.977369785308838, 1.0],
         [-2.8603439331054688, 0.0, 4.977369785308838, 1.0], [-1.860344409942627, 0.0, 4.977369785308838, 1.0],
         [-0.8603441715240479, 0.0, 4.977369785308838, 1.0], [0.13965606689453125, 0.0, 4.977369785308838, 1.0],
         [1.1396558284759521, 0.0, 4.977369785308838, 1.0], [-8.860343933105469, 0.0, 3.977370262145996, 1.0],
         [-7.860344886779785, 0.0, 3.977370262145996, 1.0], [-6.860344409942627, 0.0, 3.977370262145996, 1.0],
         [-5.860343933105469, 0.0, 3.977370262145996, 1.0], [-4.860344409942627, 0.0, 3.977370262145996, 1.0],
         [-3.860344409942627, 0.0, 3.977370262145996, 1.0], [-2.8603439331054688, 0.0, 3.977370262145996, 1.0],
         [-1.860344409942627, 0.0, 3.977370262145996, 1.0], [-0.8603441715240479, 0.0, 3.977370262145996, 1.0],
         [0.13965606689453125, 0.0, 3.977370262145996, 1.0], [1.1396558284759521, 0.0, 3.977370262145996, 1.0],
         [-8.860343933105469, 0.0, 2.977370262145996, 1.0], [-7.860344886779785, 0.0, 2.977370262145996, 1.0],
         [-6.860344409942627, 0.0, 2.977370262145996, 1.0], [-5.860343933105469, 0.0, 2.977370262145996, 1.0],
         [-4.860344409942627, 0.0, 2.977370262145996, 1.0], [-3.860344409942627, 0.0, 2.977370262145996, 1.0],
         [-2.8603439331054688, 0.0, 2.977370262145996, 1.0], [-1.860344409942627, 0.0, 2.977370262145996, 1.0],
         [-0.8603441715240479, 0.0, 2.977370262145996, 1.0], [0.13965606689453125, 0.0, 2.977370262145996, 1.0],
         [1.1396558284759521, 0.0, 2.977370262145996, 1.0], [-8.860343933105469, 0.0, 1.9773693084716797, 1.0],
         [-7.860344886779785, 0.0, 1.9773693084716797, 1.0], [-6.860344409942627, 0.0, 1.9773693084716797, 1.0],
         [-5.860343933105469, 0.0, 1.9773693084716797, 1.0], [-4.860344409942627, 0.0, 1.9773693084716797, 1.0],
         [-3.860344409942627, 0.0, 1.9773693084716797, 1.0], [-2.8603439331054688, 0.0, 1.9773693084716797, 1.0],
         [-1.860344409942627, 0.0, 1.9773693084716797, 1.0], [-0.8603441715240479, 0.0, 1.9773693084716797, 1.0],
         [0.13965606689453125, 0.0, 1.9773693084716797, 1.0], [1.1396558284759521, 0.0, 1.9773693084716797, 1.0],
         [-8.860343933105469, 0.0, 0.9773702621459961, 1.0], [-7.860344886779785, 0.0, 0.9773702621459961, 1.0],
         [-6.860343933105469, 0.0, 0.9773702621459961, 1.0], [-5.860343933105469, 0.0, 0.9773702621459961, 1.0],
         [-4.860343933105469, 0.0, 0.9773702621459961, 1.0], [-3.860344409942627, 0.0, 0.9773702621459961, 1.0],
         [-2.8603439331054688, 0.0, 0.9773702621459961, 1.0], [-1.860344409942627, 0.0, 0.9773702621459961, 1.0],
         [-0.8603441715240479, 0.0, 0.9773702621459961, 1.0], [0.13965630531311035, 0.0, 0.9773702621459961, 1.0],
         [1.1396558284759521, 0.0, 0.9773702621459961, 1.0], [-8.860343933105469, 0.0, -0.022629737854003906, 1.0],
         [-7.860343933105469, 0.0, -0.022629737854003906, 1.0], [-6.860343933105469, 0.0, -0.022629737854003906, 1.0],
         [-5.860343933105469, 0.0, -0.022629737854003906, 1.0], [-4.860343933105469, 0.0, -0.022629737854003906, 1.0],
         [-3.860344171524048, 0.0, -0.022629737854003906, 1.0], [-2.8603439331054688, 0.0, -0.022629737854003906, 1.0],
         [-1.8603442907333374, 0.0, -0.022629737854003906, 1.0], [-0.8603441715240479, 0.0, -0.022629737854003906, 1.0],
         [0.13965630531311035, 0.0, -0.022629737854003906, 1.0], [1.1396558284759521, 0.0, -0.022629737854003906, 1.0],
         [-8.860343933105469, 0.0, -1.022629737854004, 1.0], [-7.860343933105469, 0.0, -1.022629737854004, 1.0],
         [-6.860343933105469, 0.0, -1.022629737854004, 1.0], [-5.860343933105469, 0.0, -1.022629737854004, 1.0],
         [-4.860343933105469, 0.0, -1.022629737854004, 1.0], [-3.860344171524048, 0.0, -1.022629737854004, 1.0],
         [-2.8603439331054688, 0.0, -1.022629737854004, 1.0], [-1.8603442907333374, 0.0, -1.022629737854004, 1.0],
         [-0.8603441715240479, 0.0, -1.022629737854004, 1.0], [0.13965630531311035, 0.0, -1.022629737854004, 1.0],
         [1.1396558284759521, 0.0, -1.022629737854004, 1.0], [-8.860343933105469, 0.0, -2.022629737854004, 1.0],
         [-7.860343933105469, 0.0, -2.022629737854004, 1.0], [-6.860343933105469, 0.0, -2.022629737854004, 1.0],
         [-5.860343933105469, 0.0, -2.022629737854004, 1.0], [-4.860343933105469, 0.0, -2.022629737854004, 1.0],
         [-3.860344171524048, 0.0, -2.022629737854004, 1.0], [-2.8603439331054688, 0.0, -2.022629737854004, 1.0],
         [-1.8603442907333374, 0.0, -2.022629737854004, 1.0], [-0.8603441715240479, 0.0, -2.022629737854004, 1.0],
         [0.13965630531311035, 0.0, -2.022629737854004, 1.0], [1.1396558284759521, 0.0, -2.022629737854004, 1.0],
         [-8.860343933105469, 0.0, -3.022629737854004, 1.0], [-7.860343933105469, 0.0, -3.022629737854004, 1.0],
         [-6.860343933105469, 0.0, -3.022629737854004, 1.0], [-5.860343933105469, 0.0, -3.022629737854004, 1.0],
         [-4.860343933105469, 0.0, -3.022629737854004, 1.0], [-3.860344171524048, 0.0, -3.022629737854004, 1.0],
         [-2.8603439331054688, 0.0, -3.022629737854004, 1.0], [-1.8603442907333374, 0.0, -3.022629737854004, 1.0],
         [-0.8603441715240479, 0.0, -3.022629737854004, 1.0], [0.13965630531311035, 0.0, -3.022629737854004, 1.0],
         [1.1396558284759521, 0.0, -3.022629737854004, 1.0], [-8.860343933105469, 0.0, -4.022629737854004, 1.0],
         [-7.860343933105469, 0.0, -4.022629737854004, 1.0], [-6.860343933105469, 0.0, -4.022629737854004, 1.0],
         [-5.860343933105469, 0.0, -4.022629737854004, 1.0], [-4.860343933105469, 0.0, -4.022629737854004, 1.0],
         [-3.860344171524048, 0.0, -4.022629737854004, 1.0], [-2.8603439331054688, 0.0, -4.022629737854004, 1.0],
         [-1.8603442907333374, 0.0, -4.022629737854004, 1.0], [-0.8603441715240479, 0.0, -4.022629737854004, 1.0],
         [0.13965630531311035, 0.0, -4.022629737854004, 1.0], [1.1396558284759521, 0.0, -4.022629737854004, 1.0],
         [-8.860343933105469, 0.0, -5.022629737854004, 1.0], [-7.860343933105469, 0.0, -5.022629737854004, 1.0],
         [-6.860343933105469, 0.0, -5.022629737854004, 1.0], [-5.860343933105469, 0.0, -5.022629737854004, 1.0],
         [-4.860343933105469, 0.0, -5.022629737854004, 1.0], [-3.860344171524048, 0.0, -5.022629737854004, 1.0],
         [-2.8603439331054688, 0.0, -5.022629737854004, 1.0], [-1.8603442907333374, 0.0, -5.022629737854004, 1.0],
         [-0.8603441715240479, 0.0, -5.022629737854004, 1.0], [0.13965630531311035, 0.0, -5.022629737854004, 1.0],
         [1.1396558284759521, 0.0, -5.022629737854004, 1.0], [-8.860343933105469, 0.0, -6.022629737854004, 1.0],
         [-7.860343933105469, 0.0, -6.022629737854004, 1.0], [-6.860343933105469, 0.0, -6.022629737854004, 1.0],
         [-5.860343933105469, 0.0, -6.022629737854004, 1.0], [-4.860343933105469, 0.0, -6.022629737854004, 1.0],
         [-3.860344171524048, 0.0, -6.022629737854004, 1.0], [-2.8603439331054688, 0.0, -6.022629737854004, 1.0],
         [-1.8603442907333374, 0.0, -6.022629737854004, 1.0], [-0.8603441715240479, 0.0, -6.022629737854004, 1.0],
         [0.13965630531311035, 0.0, -6.022629737854004, 1.0], [1.1396558284759521, 0.0, -6.022629737854004, 1.0],
         [-8.860343933105469, 0.0, -7.022629737854004, 1.0], [-7.860343933105469, 0.0, -7.022629737854004, 1.0],
         [-6.860343933105469, 0.0, -7.022629737854004, 1.0], [-5.860343933105469, 0.0, -7.022629737854004, 1.0],
         [-4.860343933105469, 0.0, -7.022629737854004, 1.0], [-3.860344171524048, 0.0, -7.022629737854004, 1.0],
         [-2.8603439331054688, 0.0, -7.022629737854004, 1.0], [-1.8603442907333374, 0.0, -7.022629737854004, 1.0],
         [-0.8603441715240479, 0.0, -7.022629737854004, 1.0], [0.13965630531311035, 0.0, -7.022629737854004, 1.0],
         [1.1396558284759521, 0.0, -7.022629737854004, 1.0], [-8.860343933105469, 0.0, -8.022631645202637, 1.0],
         [-7.860343933105469, 0.0, -8.022631645202637, 1.0], [-6.860343933105469, 0.0, -8.022631645202637, 1.0],
         [-5.860343933105469, 0.0, -8.022631645202637, 1.0], [-4.860343933105469, 0.0, -8.022631645202637, 1.0],
         [-3.860344171524048, 0.0, -8.022631645202637, 1.0], [-2.8603439331054688, 0.0, -8.022631645202637, 1.0],
         [-1.8603442907333374, 0.0, -8.022631645202637, 1.0], [-0.8603441715240479, 0.0, -8.022631645202637, 1.0],
         [0.13965630531311035, 0.0, -8.022631645202637, 1.0], [1.1396558284759521, 0.0, -8.022631645202637, 1.0],
         [-8.860343933105469, 0.0, -9.022629737854004, 1.0], [-7.860343933105469, 0.0, -9.022629737854004, 1.0],
         [-6.860343933105469, 0.0, -9.022629737854004, 1.0], [-5.860343933105469, 0.0, -9.022629737854004, 1.0],
         [-4.860343933105469, 0.0, -9.022629737854004, 1.0], [-3.860344171524048, 0.0, -9.022629737854004, 1.0],
         [-2.8603439331054688, 0.0, -9.022629737854004, 1.0], [-1.8603442907333374, 0.0, -9.022629737854004, 1.0],
         [-0.8603441715240479, 0.0, -9.022629737854004, 1.0], [0.13965630531311035, 0.0, -9.022629737854004, 1.0],
         [1.1396558284759521, 0.0, -9.022629737854004, 1.0],
         [-8.860343933105469, 1.100000023841858, 10.977370262145996, 1.0],
         [-7.860344886779785, 1.100000023841858, 10.977370262145996, 1.0],
         [-8.860343933105469, 1.100000023841858, 9.977370262145996, 1.0],
         [-6.860344409942627, 1.100000023841858, 10.977370262145996, 1.0],
         [-5.860343933105469, 1.100000023841858, 10.977370262145996, 1.0],
         [-4.860344409942627, 1.100000023841858, 10.977370262145996, 1.0],
         [-3.860344409942627, 1.100000023841858, 10.977370262145996, 1.0],
         [-2.8603439331054688, 1.100000023841858, 10.977370262145996, 1.0],
         [-1.860344409942627, 1.100000023841858, 10.977370262145996, 1.0],
         [-0.8603441715240479, 1.100000023841858, 10.977370262145996, 1.0],
         [0.13965606689453125, 1.100000023841858, 10.977370262145996, 1.0],
         [1.1396558284759521, 1.100000023841858, 10.977370262145996, 1.0],
         [1.1396558284759521, 1.100000023841858, 9.977370262145996, 1.0],
         [-8.860343933105469, 1.100000023841858, 8.977370262145996, 1.0],
         [1.1396558284759521, 1.100000023841858, 8.977370262145996, 1.0],
         [-8.860343933105469, 1.100000023841858, 7.977370262145996, 1.0],
         [1.1396558284759521, 1.100000023841858, 7.977370262145996, 1.0],
         [-8.860343933105469, 1.100000023841858, 6.977370262145996, 1.0],
         [1.1396558284759521, 1.100000023841858, 6.977370262145996, 1.0],
         [-8.860343933105469, 1.100000023841858, 5.977370262145996, 1.0],
         [1.1396558284759521, 1.100000023841858, 5.977370262145996, 1.0],
         [-8.860343933105469, 1.100000023841858, 4.977369785308838, 1.0],
         [1.1396558284759521, 1.100000023841858, 4.977369785308838, 1.0],
         [-8.860343933105469, 1.100000023841858, 3.977370262145996, 1.0],
         [1.1396558284759521, 1.100000023841858, 3.977370262145996, 1.0],
         [-8.860343933105469, 1.100000023841858, 2.977370262145996, 1.0],
         [1.1396558284759521, 1.100000023841858, 2.977370262145996, 1.0],
         [-8.860343933105469, 1.100000023841858, 1.9773693084716797, 1.0],
         [1.1396558284759521, 1.100000023841858, 1.9773693084716797, 1.0],
         [-8.860343933105469, 1.100000023841858, 0.9773702621459961, 1.0],
         [1.1396558284759521, 1.100000023841858, 0.9773702621459961, 1.0],
         [-8.860343933105469, 1.100000023841858, -0.022629737854003906, 1.0],
         [1.1396558284759521, 1.100000023841858, -0.022629737854003906, 1.0],
         [-8.860343933105469, 1.100000023841858, -1.022629737854004, 1.0],
         [1.1396558284759521, 1.100000023841858, -1.022629737854004, 1.0],
         [-8.860343933105469, 1.100000023841858, -2.022629737854004, 1.0],
         [1.1396558284759521, 1.100000023841858, -2.022629737854004, 1.0],
         [-8.860343933105469, 1.100000023841858, -3.022629737854004, 1.0],
         [1.1396558284759521, 1.100000023841858, -3.022629737854004, 1.0],
         [-8.860343933105469, 1.100000023841858, -4.022629737854004, 1.0],
         [1.1396558284759521, 1.100000023841858, -4.022629737854004, 1.0],
         [-8.860343933105469, 1.100000023841858, -5.022629737854004, 1.0],
         [1.1396558284759521, 1.100000023841858, -5.022629737854004, 1.0],
         [-8.860343933105469, 1.100000023841858, -6.022629737854004, 1.0],
         [1.1396558284759521, 1.100000023841858, -6.022629737854004, 1.0],
         [-8.860343933105469, 1.100000023841858, -7.022629737854004, 1.0],
         [1.1396558284759521, 1.100000023841858, -7.022629737854004, 1.0],
         [-8.860343933105469, 1.100000023841858, -8.022631645202637, 1.0],
         [1.1396558284759521, 1.100000023841858, -8.022631645202637, 1.0],
         [-8.860343933105469, 1.100000023841858, -9.022629737854004, 1.0],
         [1.1396558284759521, 1.100000023841858, -9.022629737854004, 1.0]]

    polygon_count = 250

    transformation_matrix = \
        [[1.0, 0.0, 0.0, 0.0], [0.0, 2.220446049250319e-16, 1.0000000000000029, 0.0],
         [0.0, -1.0000000000000029, 2.220446049250319e-16, 0.0],
         [3.83007495075029, 10.974514930158847, 0.9773701434547, 1.0]]

    def __init__(self):
        self.field_mobject = OpenMayaUtils.create_mesh(self.polygon_count, self.vertex_positions_raw_data,
                                                       self.number_of_vertices_per_polygon,
                                                       self.vertex_indexes_per_polygon)

    def apply_transformation_matrix(self):
        new_mmatrix = OpenMayaUtils.convert_floats_matrix_to_MMatrix(self.transformation_matrix)
        new_mtransformation_matrix = OpenMaya.MTransformationMatrix(new_mmatrix)
        mfn_transform = OpenMaya.MFnTransform(self.field_mobject)
        mfn_transform.set(new_mtransformation_matrix)

    def apply_default_shader(self):
        mfn_dag = OpenMaya.MFnDagNode(self.field_mobject)
        shape_mobj = mfn_dag.child(0)

        field_shape_obj_grups_mplug = OpenMayaUtils.get_plug_by_name(shape_mobj, "instObjGroups")
        field_shape_grups_mplug_zero_index = field_shape_obj_grups_mplug.elementByLogicalIndex(0)

        shading_group_mobj = OpenMayaUtils.make_depend_node("initialShadingGroup")
        dag_set_memb_mplug = OpenMayaUtils.get_plug_by_name(shading_group_mobj, "dagSetMembers")
        free_index = int(dag_set_memb_mplug.numElements()) + 1
        dag_set_memb_mplug_zero_index = dag_set_memb_mplug.elementByLogicalIndex(free_index)

        MDGMod = OpenMaya.MDGModifier()
        MDGMod.connect(field_shape_grups_mplug_zero_index, dag_set_memb_mplug_zero_index)
        MDGMod.doIt()


def setup_viewport_lights():
    global mfn_transform
    dagModifier = OpenMaya.MDagModifier()
    light_mobj = dagModifier.createNode('transform')
    dagModifier.renameNode(light_mobj, 'pointLight1')
    dagModifier.doIt()
    # create and setup point light
    mfn_point_light = OpenMaya.MFnPointLight()
    mfn_point_light.create(light_mobj)
    mfn_point_light.setIntensity(2)
    mlight_tranformation_matrix = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0],
                                   [3.369167279610191, 22.611715134569895, 4.389972436762605, 1.0]]
    mlight_m_matrix = OpenMayaUtils.convert_floats_matrix_to_MMatrix(mlight_tranformation_matrix)
    mlight_mtrasformation_matrix = OpenMaya.MTransformationMatrix(mlight_m_matrix)
    mfn_transform = OpenMaya.MFnTransform(light_mobj)
    mfn_transform.set(mlight_mtrasformation_matrix)

    ambient_light_mobj = dagModifier.createNode('transform')
    dagModifier.renameNode(ambient_light_mobj, 'ambientLight1')
    dagModifier.doIt()

    # create and setup ambient light
    mfn_ambient_light = OpenMaya.MFnAmbientLight ()
    mfn_ambient_light.create(ambient_light_mobj)
    mfn_ambient_light.setIntensity(0.200)


def setup_camera():

    # create camera
    mfn_cam_obj = OpenMaya.MFnCamera()
    transform_cam_mobj = mfn_cam_obj.create()

    # setup camera params
    mfn_cam_obj.setFocalLength(154)
    cam_transformation_matrix = [[0.9477684100095842, 0.0, -0.3189593092980744, 0.0],
                                [-0.08437068513613653, 0.9643805706617643, -0.2507024180572432, 0.0],
                                [0.3075981607187592, 0.26451864760369886, 0.9140094401002359, 0.0],
                                [48.080564005866556, 51.558463195211445, 144.48540158432039, 1.0]]
    cam_m_matrix = OpenMayaUtils.convert_floats_matrix_to_MMatrix(cam_transformation_matrix)
    cam_mtransformation_matrix = OpenMaya.MTransformationMatrix(cam_m_matrix)
    mfn_transform = OpenMaya.MFnTransform(transform_cam_mobj)
    mfn_transform.set(cam_mtransformation_matrix)

    # get mdag path from camera shape
    mdag_node = OpenMaya.MFnDagNode(transform_cam_mobj)
    cam_mobj = mdag_node.child(0)
    cam_m_dagPath = OpenMaya.MDagPath()
    OpenMaya.MDagPath.getAPathTo(cam_mobj, cam_m_dagPath)

    # get current active view and set params
    m3d_view = OpenMayaUI.M3dView.active3dView()
    m3d_view.setCamera(cam_m_dagPath)
    m3d_view.refresh()

    cam_name = mdag_node.fullPathName()
    cmds.select(cam_name)
    cmds.viewFit()


def setup_viewport():

    cur_mp = None
    for mp in cmds.getPanel(type="modelPanel"):
        if cmds.modelEditor(mp, q=1, av=1):
            cur_mp = mp
            break
    if cur_mp:
        # do your stuff
        new_rndr = "ogsRenderer"
        cmds.modelEditor(cur_mp, e=1, rnm=new_rndr, displayLights="all", wireframeOnShaded=True, shadows=True)
        commands = "setAttr \"hardwareRenderingGlobals.lineAAEnable\" 1;" \
                   "setAttr \"hardwareRenderingGlobals.multiSampleEnable\" 1;" \
                   "setAttr \"hardwareRenderingGlobals.ssaoEnable\" 1;" \
                   "setAttr \"hardwareRenderingGlobals.ssaoRadius\" 10;"
        mel.eval(commands)


def create_shader(name, node_type="lambert"):
    material = cmds.shadingNode(node_type, name=name, asShader=True)
    sg = cmds.sets(name="%sSG" % name, empty=True, renderable=True, noSurfaceShader=True)
    cmds.connectAttr("%s.outColor" % material, "%s.surfaceShader" % sg)
    return material, sg


def create_shader_with_color(color, shader_name):
    material_name, sg_name = create_shader(shader_name)
    cmds.setAttr(material_name + ".color", color[0], color[1], color[2], type="double3")
    return material_name, sg_name


def generate_all_shaders():

    shading_groups_list = []

    blue_color = [0.01, 0.25, 0.68]
    blue_lambert_name, blue_sg_name = create_shader_with_color(blue_color, "blue_color")
    shading_groups_list.append(blue_sg_name)

    green_color = [0, 0.9, 0]
    green_lambert_name, green_sg_name = create_shader_with_color(green_color, "green_color")
    shading_groups_list.append(green_sg_name)

    yellow_color = [1, 0.83, 0]
    yellow_lambert_name, yellow_sg_name = create_shader_with_color(yellow_color, "yellow_color")
    shading_groups_list.append(yellow_sg_name)

    orange_color = [1, 0.14, 0]
    orange_lambert_name, orange_sg_name = create_shader_with_color(orange_color, "orange_color")
    shading_groups_list.append(orange_sg_name)

    red_color = [1, 0, 0.]
    red_lambert_name, red_sg_name = create_shader_with_color(red_color, "red_color")
    shading_groups_list.append(red_sg_name)

    return shading_groups_list


def create_figures(figures_creation_data, parent):
    if figures_creation_data:
        for data in figures_creation_data:
            number_of_vertices_per_polygon = data["number_of_vertices_per_polygon"]
            vertex_indexes_per_polygon = data["vertex_indexes_per_polygon"]
            vertex_positions_raw_data = data["vertex_positions"]
            polygon_count = data["numPolygons"]

            OpenMayaUtils.create_mesh(polygon_count,
                                      vertex_positions_raw_data,
                                      number_of_vertices_per_polygon,
                                      vertex_indexes_per_polygon,
                                      parent.object()
                                      )


def generate_random_figure():
    rand_mesh_index = randint(0, len(figures_mesh_creation_data) - 1)
    figure_transform_mfn_dag = OpenMaya.MFnDagNode()
    figure_transform_mfn_dag.create("transform", "figure_%s" % str(rand_mesh_index))
    figure_dag_name = figure_transform_mfn_dag.fullPathName()
    figure_random_key = figures_mesh_keys_list[rand_mesh_index]
    figure_data = figures_mesh_creation_data[figure_random_key]
    center_shape_data = figure_data["center_shape_data"]
    if center_shape_data:
        create_figures(center_shape_data, figure_transform_mfn_dag)
        cmds.xform(figure_dag_name, centerPivots=True)
    rest_shapes_data = figure_data["rest_shape_data"]
    if rest_shapes_data:
        create_figures(rest_shapes_data, figure_transform_mfn_dag)
    rand_shader_index = randint(0, 4)
    rand_shader_shading_group = shaders_shading_groups_list[rand_shader_index]
    figure_name = figure_transform_mfn_dag.fullPathName()
    cmds.sets(figure_name, forceElement=rand_shader_shading_group)

    return figure_dag_name


def get_shape_xy_centroid(mesh_name):
    #UPDATE FOR EACH CHILD SHAPE
    if not mesh_name or not cmds.objExists(mesh_name):
        return

    points_amount = cmds.polyEvaluate(mesh_name, vertex=True)
    accumulated_x = 0.0
    accumulated_y = 0.0
    for i in range(points_amount):
        current_point_position = cmds.pointPosition("%s.vtx[%s]" % (mesh_name, str(i)), world=True)
        accumulated_x += current_point_position[0]
        accumulated_y += current_point_position[1]
    cube_center = [accumulated_x / points_amount, accumulated_y / points_amount]
    return cube_center


def check_mesh_update_allowed(mesh_name, locked_cells_list):

    global min_x, max_x, min_y

    child_shapes = cmds.listRelatives(mesh_name, children=True)
    if not child_shapes:
        return False

    for child in child_shapes:
        current_xy_centroid = get_shape_xy_centroid(child)
        if not min_x < current_xy_centroid[0] < max_x or not min_y < current_xy_centroid[1] < max_y:
            return False
        elif tuple(current_xy_centroid) in locked_cells_list:
            return False
        
    return True


def fill_locked_cells_list(mesh_name, locked_cells_list):
    global min_x, max_x, min_y

    child_shapes = cmds.listRelatives(mesh_name, children=True, allDescendents=True, shapes=True)
    if not child_shapes:
        return

    for child in child_shapes:
        current_xy_centroid = get_shape_xy_centroid(child)
        if current_xy_centroid not in locked_cells_list:
            locked_cells_list.append(tuple(current_xy_centroid))


field_obj = Field()
field_obj.apply_transformation_matrix()
field_obj.apply_default_shader()

setup_viewport()
setup_viewport_lights()
setup_camera()
cmds.refresh()

shaders_shading_groups_list = generate_all_shaders()

figures_mesh_creation_data =  {'figure_0_mesh_data': {'center_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.030395925045013428, 19.998565673828125, 1.0007339715957642, 1.0], [0.9696040749549866, 19.998565673828125, 1.0007339715957642, 1.0], [-0.030395925045013428, 20.998565673828125, 1.0007339715957642, 1.0], [0.9696040749549866, 20.998565673828125, 1.0007339715957642, 1.0], [-0.030395925045013428, 19.998565673828125, 2.0007338523864746, 1.0], [0.9696040749549866, 19.998565673828125, 2.0007338523864746, 1.0], [0.9696040749549866, 20.998565673828125, 2.0007338523864746, 1.0], [-0.030395925045013428, 20.998565673828125, 2.0007338523864746, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.030395925045013428, 20.998565673828125, 1.0007339715957642, 1.0], [0.9696040749549866, 20.998565673828125, 1.0007339715957642, 1.0], [-0.030395925045013428, 21.998565673828125, 1.0007339715957642, 1.0], [0.9696040749549866, 21.998565673828125, 1.0007339715957642, 1.0], [-0.030395925045013428, 20.998565673828125, 2.0007338523864746, 1.0], [0.9696040749549866, 20.998565673828125, 2.0007338523864746, 1.0], [0.9696040749549866, 21.998565673828125, 2.0007338523864746, 1.0], [-0.030395925045013428, 21.998565673828125, 2.0007338523864746, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-1.0303959846496582, 19.998565673828125, 1.0007339715957642, 1.0], [-0.030395925045013428, 19.998565673828125, 1.0007339715957642, 1.0], [-1.0303959846496582, 20.998565673828125, 1.0007339715957642, 1.0], [-0.030395925045013428, 20.998565673828125, 1.0007339715957642, 1.0], [-1.0303959846496582, 19.998565673828125, 2.0007338523864746, 1.0], [-0.030395925045013428, 19.998565673828125, 2.0007338523864746, 1.0], [-0.030395925045013428, 20.998565673828125, 2.0007338523864746, 1.0], [-1.0303959846496582, 20.998565673828125, 2.0007338523864746, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-1.0303959846496582, 20.998565673828125, 1.0007339715957642, 1.0], [-0.030395925045013428, 20.998565673828125, 1.0007339715957642, 1.0], [-1.0303959846496582, 21.998565673828125, 1.0007339715957642, 1.0], [-0.030395925045013428, 21.998565673828125, 1.0007339715957642, 1.0], [-1.0303959846496582, 20.998565673828125, 2.0007338523864746, 1.0], [-0.030395925045013428, 20.998565673828125, 2.0007338523864746, 1.0], [-0.030395925045013428, 21.998565673828125, 2.0007338523864746, 1.0], [-1.0303959846496582, 21.998565673828125, 2.0007338523864746, 1.0]], 'numPolygons': 6}], 'rest_shape_data': None}, 'figure_5_mesh_data': {'center_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.030243873596191406, 21.005300521850586, 0.9831539392471313, 1.0], [0.9697561264038086, 21.005300521850586, 0.9831539392471313, 1.0], [-0.030243873596191406, 22.005300521850586, 0.9831539392471313, 1.0], [0.9697561264038086, 22.005300521850586, 0.9831539392471313, 1.0], [-0.030243873596191406, 21.005300521850586, 1.9831539392471313, 1.0], [0.9697561264038086, 21.005300521850586, 1.9831539392471313, 1.0], [0.9697561264038086, 22.005300521850586, 1.983154058456421, 1.0], [-0.030243873596191406, 22.005300521850586, 1.983154058456421, 1.0]], 'numPolygons': 6}], 'rest_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-1.0302438735961914, 21.005300521850586, 0.9831539392471313, 1.0], [-0.030243873596191406, 21.005300521850586, 0.9831539392471313, 1.0], [-1.0302438735961914, 22.005300521850586, 0.9831539392471313, 1.0], [-0.030243873596191406, 22.005300521850586, 0.9831539392471313, 1.0], [-1.0302438735961914, 21.005300521850586, 1.9831539392471313, 1.0], [-0.030243873596191406, 21.005300521850586, 1.9831539392471313, 1.0], [-0.030243873596191406, 22.005300521850586, 1.983154058456421, 1.0], [-1.0302438735961914, 22.005300521850586, 1.983154058456421, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.030243873596191406, 20.005300521850586, 0.9831539392471313, 1.0], [0.9697561264038086, 20.005300521850586, 0.9831539392471313, 1.0], [-0.030243873596191406, 21.005300521850586, 0.9831539392471313, 1.0], [0.9697561264038086, 21.005300521850586, 0.9831539392471313, 1.0], [-0.030243873596191406, 20.005300521850586, 1.9831539392471313, 1.0], [0.9697561264038086, 20.005300521850586, 1.9831539392471313, 1.0], [0.9697561264038086, 21.005300521850586, 1.983154058456421, 1.0], [-0.030243873596191406, 21.005300521850586, 1.983154058456421, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-1.0302438735961914, 22.005300521850586, 0.9831539392471313, 1.0], [-0.030243873596191406, 22.005300521850586, 0.9831539392471313, 1.0], [-1.0302438735961914, 23.005300521850586, 0.9831539392471313, 1.0], [-0.030243873596191406, 23.005300521850586, 0.9831539392471313, 1.0], [-1.0302438735961914, 22.005300521850586, 1.9831539392471313, 1.0], [-0.030243873596191406, 22.005300521850586, 1.9831539392471313, 1.0], [-0.030243873596191406, 23.005300521850586, 1.983154058456421, 1.0], [-1.0302438735961914, 23.005300521850586, 1.983154058456421, 1.0]], 'numPolygons': 6}]}, 'figure_3_mesh_data': {'center_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-0.031080782413482666, 22.002187728881836, 0.9874250888824463, 1.0], [0.9689192175865173, 22.002187728881836, 0.9874250888824463, 1.0], [-0.031080782413482666, 21.002187728881836, 0.9874250888824463, 1.0], [0.9689192175865173, 21.002187728881836, 0.9874250888824463, 1.0], [-0.031080782413482666, 22.002187728881836, 1.9874250888824463, 1.0], [0.9689192175865173, 22.002187728881836, 1.9874250888824463, 1.0], [0.9689192175865173, 21.002187728881836, 1.9874248504638672, 1.0], [-0.031080782413482666, 21.002187728881836, 1.9874248504638672, 1.0]], 'numPolygons': 6}], 'rest_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-0.031080782413482666, 21.002187728881836, 0.9874250888824463, 1.0], [0.9689192175865173, 21.002187728881836, 0.9874250888824463, 1.0], [-0.031080782413482666, 20.002187728881836, 0.9874250888824463, 1.0], [0.9689192175865173, 20.002187728881836, 0.9874250888824463, 1.0], [-0.031080782413482666, 21.002187728881836, 1.9874250888824463, 1.0], [0.9689192175865173, 21.002187728881836, 1.9874250888824463, 1.0], [0.9689192175865173, 20.002187728881836, 1.9874248504638672, 1.0], [-0.031080782413482666, 20.002187728881836, 1.9874248504638672, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-0.031080782413482666, 23.002187728881836, 0.9874250888824463, 1.0], [0.9689192175865173, 23.002187728881836, 0.9874250888824463, 1.0], [-0.031080782413482666, 22.002187728881836, 0.9874250888824463, 1.0], [0.9689192175865173, 22.002187728881836, 0.9874250888824463, 1.0], [-0.031080782413482666, 23.002187728881836, 1.9874250888824463, 1.0], [0.9689192175865173, 23.002187728881836, 1.9874250888824463, 1.0], [0.9689192175865173, 22.002187728881836, 1.9874248504638672, 1.0], [-0.031080782413482666, 22.002187728881836, 1.9874248504638672, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-1.031080722808838, 22.002187728881836, 0.9874250888824463, 1.0], [-0.031080782413482666, 22.002187728881836, 0.9874250888824463, 1.0], [-1.031080722808838, 21.002187728881836, 0.9874250888824463, 1.0], [-0.031080782413482666, 21.002187728881836, 0.9874250888824463, 1.0], [-1.031080722808838, 22.002187728881836, 1.9874250888824463, 1.0], [-0.031080782413482666, 22.002187728881836, 1.9874250888824463, 1.0], [-0.031080782413482666, 21.002187728881836, 1.9874248504638672, 1.0], [-1.031080722808838, 21.002187728881836, 1.9874248504638672, 1.0]], 'numPolygons': 6}]}, 'figure_1_mesh_data': {'center_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.03058791160583496, 21.000961303710938, 0.9876478910446167, 1.0], [0.969412088394165, 21.000961303710938, 0.9876478910446167, 1.0], [-0.03058791160583496, 22.000961303710938, 0.9876478910446167, 1.0], [0.969412088394165, 22.000961303710938, 0.9876478910446167, 1.0], [-0.03058791160583496, 21.000961303710938, 1.9876478910446167, 1.0], [0.969412088394165, 21.000961303710938, 1.9876478910446167, 1.0], [0.969412088394165, 22.000961303710938, 1.9876477718353271, 1.0], [-0.03058791160583496, 22.000961303710938, 1.9876477718353271, 1.0]], 'numPolygons': 6}], 'rest_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.030587881803512573, 20.000961303710938, 0.9876478910446167, 1.0], [0.969412088394165, 20.000961303710938, 0.9876478910446167, 1.0], [-0.030587881803512573, 21.000961303710938, 0.9876478910446167, 1.0], [0.969412088394165, 21.000961303710938, 0.9876478910446167, 1.0], [-0.030587881803512573, 20.000961303710938, 1.9876478910446167, 1.0], [0.969412088394165, 20.000961303710938, 1.9876478910446167, 1.0], [0.969412088394165, 21.000961303710938, 1.9876477718353271, 1.0], [-0.030587881803512573, 21.000961303710938, 1.9876477718353271, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.03058791160583496, 22.000961303710938, 0.9876478910446167, 1.0], [0.969412088394165, 22.000961303710938, 0.9876478910446167, 1.0], [-0.03058791160583496, 23.000961303710938, 0.9876478910446167, 1.0], [0.969412088394165, 23.000961303710938, 0.9876478910446167, 1.0], [-0.03058791160583496, 22.000961303710938, 1.9876478910446167, 1.0], [0.969412088394165, 22.000961303710938, 1.9876478910446167, 1.0], [0.969412088394165, 23.000961303710938, 1.9876477718353271, 1.0], [-0.03058791160583496, 23.000961303710938, 1.9876477718353271, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-1.030587911605835, 22.000961303710938, 0.9876478910446167, 1.0], [-0.03058791160583496, 22.000961303710938, 0.9876478910446167, 1.0], [-1.030587911605835, 23.000961303710938, 0.9876478910446167, 1.0], [-0.03058791160583496, 23.000961303710938, 0.9876478910446167, 1.0], [-1.030587911605835, 22.000961303710938, 1.9876478910446167, 1.0], [-0.03058791160583496, 22.000961303710938, 1.9876478910446167, 1.0], [-0.03058791160583496, 23.000961303710938, 1.9876477718353271, 1.0], [-1.030587911605835, 23.000961303710938, 1.9876477718353271, 1.0]], 'numPolygons': 6}]}, 'figure_6_mesh_data': {'center_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.032750993967056274, 22.00364875793457, 0.9784406423568726, 1.0], [0.9672490358352661, 22.00364875793457, 0.9784406423568726, 1.0], [-0.032750993967056274, 23.00364875793457, 0.9784406423568726, 1.0], [0.9672490358352661, 23.00364875793457, 0.9784406423568726, 1.0], [-0.032750993967056274, 22.00364875793457, 1.9784406423568726, 1.0], [0.9672490358352661, 22.00364875793457, 1.9784406423568726, 1.0], [0.9672490358352661, 23.00364875793457, 1.978440761566162, 1.0], [-0.032750993967056274, 23.00364875793457, 1.978440761566162, 1.0]], 'numPolygons': 6}], 'rest_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.032750993967056274, 20.00364875793457, 0.9784406423568726, 1.0], [0.9672490358352661, 20.00364875793457, 0.9784406423568726, 1.0], [-0.032750993967056274, 21.00364875793457, 0.9784406423568726, 1.0], [0.9672490358352661, 21.00364875793457, 0.9784406423568726, 1.0], [-0.032750993967056274, 20.00364875793457, 1.9784406423568726, 1.0], [0.9672490358352661, 20.00364875793457, 1.9784406423568726, 1.0], [0.9672490358352661, 21.00364875793457, 1.978440761566162, 1.0], [-0.032750993967056274, 21.00364875793457, 1.978440761566162, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.032750993967056274, 21.00364875793457, 0.9784406423568726, 1.0], [0.9672490358352661, 21.00364875793457, 0.9784406423568726, 1.0], [-0.032750993967056274, 22.00364875793457, 0.9784406423568726, 1.0], [0.9672490358352661, 22.00364875793457, 0.9784406423568726, 1.0], [-0.032750993967056274, 21.00364875793457, 1.9784406423568726, 1.0], [0.9672490358352661, 21.00364875793457, 1.9784406423568726, 1.0], [0.9672490358352661, 22.00364875793457, 1.978440761566162, 1.0], [-0.032750993967056274, 22.00364875793457, 1.978440761566162, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 5, 6, 7, 0, 2, 3, 1, 0, 1, 5, 4, 1, 3, 6, 5, 3, 2, 7, 6, 2, 0, 4, 7], 'vertex_positions': [[-0.032750993967056274, 23.00956916809082, 0.9784406423568726, 1.0], [0.9672490358352661, 23.00956916809082, 0.9784406423568726, 1.0], [-0.032750993967056274, 24.00956916809082, 0.9784406423568726, 1.0], [0.9672490358352661, 24.00956916809082, 0.9784406423568726, 1.0], [-0.032750993967056274, 23.00956916809082, 1.9784406423568726, 1.0], [0.9672490358352661, 23.00956916809082, 1.9784406423568726, 1.0], [0.9672490358352661, 24.00956916809082, 1.978440761566162, 1.0], [-0.032750993967056274, 24.00956916809082, 1.978440761566162, 1.0]], 'numPolygons': 6}]}, 'figure_2_mesh_data': {'center_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-0.03365015983581543, 22.004610061645508, 0.9893019199371338, 1.0], [0.9663498401641846, 22.004610061645508, 0.9893019199371338, 1.0], [-0.03365015983581543, 21.004610061645508, 0.9893019199371338, 1.0], [0.9663498401641846, 21.004610061645508, 0.9893019199371338, 1.0], [-0.03365015983581543, 22.004610061645508, 1.9893019199371338, 1.0], [0.9663498401641846, 22.004610061645508, 1.9893019199371338, 1.0], [0.9663498401641846, 21.004610061645508, 1.9893016815185547, 1.0], [-0.03365015983581543, 21.004610061645508, 1.9893016815185547, 1.0]], 'numPolygons': 6}], 'rest_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-0.03365013003349304, 23.004610061645508, 0.9893019199371338, 1.0], [0.9663498401641846, 23.004610061645508, 0.9893019199371338, 1.0], [-0.03365013003349304, 22.004610061645508, 0.9893019199371338, 1.0], [0.9663498401641846, 22.004610061645508, 0.9893019199371338, 1.0], [-0.03365013003349304, 23.004610061645508, 1.9893019199371338, 1.0], [0.9663498401641846, 23.004610061645508, 1.9893019199371338, 1.0], [0.9663498401641846, 22.004610061645508, 1.9893019199371338, 1.0], [-0.03365013003349304, 22.004610061645508, 1.9893019199371338, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-0.03365015983581543, 21.004610061645508, 0.9893019199371338, 1.0], [0.9663498401641846, 21.004610061645508, 0.9893019199371338, 1.0], [-0.03365015983581543, 20.004610061645508, 0.9893019199371338, 1.0], [0.9663498401641846, 20.004610061645508, 0.9893019199371338, 1.0], [-0.03365015983581543, 21.004610061645508, 1.9893019199371338, 1.0], [0.9663498401641846, 21.004610061645508, 1.9893019199371338, 1.0], [0.9663498401641846, 20.004610061645508, 1.9893016815185547, 1.0], [-0.03365015983581543, 20.004610061645508, 1.9893016815185547, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-1.0336501598358154, 21.004610061645508, 0.9893019199371338, 1.0], [-0.03365015983581543, 21.004610061645508, 0.9893019199371338, 1.0], [-1.0336501598358154, 20.004610061645508, 0.9893019199371338, 1.0], [-0.03365015983581543, 20.004610061645508, 0.9893019199371338, 1.0], [-1.0336501598358154, 21.004610061645508, 1.9893019199371338, 1.0], [-0.03365015983581543, 21.004610061645508, 1.9893019199371338, 1.0], [-0.03365015983581543, 20.004610061645508, 1.9893016815185547, 1.0], [-1.0336501598358154, 20.004610061645508, 1.9893016815185547, 1.0]], 'numPolygons': 6}]}, 'figure_4_mesh_data': {'center_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-0.03736519813537598, 22.007953643798828, 0.9787225127220154, 1.0], [0.962634801864624, 22.007953643798828, 0.9787225127220154, 1.0], [-0.03736519813537598, 21.007953643798828, 0.9787225723266602, 1.0], [0.962634801864624, 21.007953643798828, 0.9787225723266602, 1.0], [-0.03736519813537598, 22.007953643798828, 1.9787225723266602, 1.0], [0.962634801864624, 22.007953643798828, 1.9787225723266602, 1.0], [0.962634801864624, 21.007953643798828, 1.9787225723266602, 1.0], [-0.03736519813537598, 21.007953643798828, 1.9787225723266602, 1.0]], 'numPolygons': 6}], 'rest_shape_data': [{'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-1.037365198135376, 22.007953643798828, 0.9787225127220154, 1.0], [-0.03736519813537598, 22.007953643798828, 0.9787225127220154, 1.0], [-1.037365198135376, 21.007953643798828, 0.9787225723266602, 1.0], [-0.03736519813537598, 21.007953643798828, 0.9787225723266602, 1.0], [-1.037365198135376, 22.007953643798828, 1.9787225723266602, 1.0], [-0.03736519813537598, 22.007953643798828, 1.9787225723266602, 1.0], [-0.03736519813537598, 21.007953643798828, 1.9787225723266602, 1.0], [-1.037365198135376, 21.007953643798828, 1.9787225723266602, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-0.03736519813537598, 23.007953643798828, 0.9787225127220154, 1.0], [0.962634801864624, 23.007953643798828, 0.9787225127220154, 1.0], [-0.03736519813537598, 22.007953643798828, 0.9787225723266602, 1.0], [0.962634801864624, 22.007953643798828, 0.9787225723266602, 1.0], [-0.03736519813537598, 23.007953643798828, 1.9787225723266602, 1.0], [0.962634801864624, 23.007953643798828, 1.9787225723266602, 1.0], [0.962634801864624, 22.007953643798828, 1.9787225723266602, 1.0], [-0.03736519813537598, 22.007953643798828, 1.9787225723266602, 1.0]], 'numPolygons': 6}, {'number_of_vertices_per_polygon': [4, 4, 4, 4, 4, 4], 'vertex_indexes_per_polygon': [4, 7, 6, 5, 0, 1, 3, 2, 0, 4, 5, 1, 1, 5, 6, 3, 3, 6, 7, 2, 2, 7, 4, 0], 'vertex_positions': [[-1.037365198135376, 21.007953643798828, 0.9787225127220154, 1.0], [-0.03736519813537598, 21.007953643798828, 0.9787225127220154, 1.0], [-1.037365198135376, 20.007953643798828, 0.9787225723266602, 1.0], [-0.03736519813537598, 20.007953643798828, 0.9787225723266602, 1.0], [-1.037365198135376, 21.007953643798828, 1.9787225723266602, 1.0], [-0.03736519813537598, 21.007953643798828, 1.9787225723266602, 1.0], [-0.03736519813537598, 20.007953643798828, 1.9787225723266602, 1.0], [-1.037365198135376, 20.007953643798828, 1.9787225723266602, 1.0]], 'numPolygons': 6}]}}

counter = 0
temp_cache = []
figures_mesh_keys_list = list(figures_mesh_creation_data.keys())

continue_game = True
test_break_counter = 0
active_figure_name = ""

min_y = 0.5
max_y = 20.5
min_x = -4.5
max_x =  4.5
locked_cells_list = []

go_next_figure = True
active_figure_name = generate_random_figure()

while test_break_counter < 50:
    if go_next_figure:
        active_figure_name = generate_random_figure()
    go_next_figure=False

    current_figure_translate_y_attr_name = "%s.%s" % (active_figure_name, "translateY")
    changed_position = cmds.getAttr(current_figure_translate_y_attr_name)
    cmds.setAttr(current_figure_translate_y_attr_name, changed_position - 1)

    transform_update_allowed = check_mesh_update_allowed(active_figure_name, locked_cells_list)
    # print "transform_update_allowed:", transform_update_allowed
    if not transform_update_allowed:
        cmds.setAttr(current_figure_translate_y_attr_name, changed_position)
        go_next_figure = True

    fill_locked_cells_list(active_figure_name, locked_cells_list)

    test_break_counter += 1
    cmds.refresh()
    time.sleep(1)
#FASTER UPDATE x30 per second
#LOCK MIN Y VALUE, LOCK MAX AND MIN X VALUE


#each shape with no parent later parent
# if main parent bbox intersects then check other shapes intersection
#for each shape check boundbox intersects with other shapes and bg field

# start cycle with falling figures each iteration
# figure out moment of collision with other figures
# generate other figures on collision moment
# setup viewport ui and hotkeys
# blast all cubes, which is filled full line of box
# finish game, when after collision y coord of figure is higher than highest y position from box (with number for example)


# COLLISION CHECKING -> GET CURRENT FIGURE POSITION, TAKE LOWEST POINT, CHECK THAT IN
# RADIUS OF THAT POINT THERE IS NO GEOMETRY, IF IT IS -> THEN STOP