"""Material helper functions."""

import bpy
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

import logging

_l = logging.getLogger(__name__)


def setup_bake_material(obj, name, bake_uv_name, diffuse=None, roughness=None, normal=None):
    _l.info('Creating material %s for object %s', name, obj.name)

    mat = bpy.data.materials.get(name)
    if mat is not None:
        _l.debug('Found existing material, skipping')
        return mat

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    obj.data.materials.append(mat)

    principled_mat = PrincipledBSDFWrapper(mat, is_readonly=False)
    principled_mat.roughness = 1.0

    principled_node = principled_mat.node_principled_bsdf

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    uv_node = nodes.new(type='ShaderNodeUVMap')
    uv_node.uv_map = bake_uv_name
    uv_node.location.x -= 1000
    # uv_node.location.y += 300

    mapping_node = nodes.new(type='ShaderNodeMapping')
    mapping_node.location.x -= 800
    # mapping_node.location.y += 300
    links.new(uv_node.outputs['UV'], mapping_node.inputs['Vector'])

    def make_tex_node(img, y):
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.image = img
        tex_node.location.x -= 500
        tex_node.location.y += y

        links.new(mapping_node.outputs['Vector'], tex_node.inputs['Vector'])

        # TODO: color space if not set by default
        # tex_node.image.colorspace_settings.name = '...'

        return tex_node

    if diffuse is not None:
        diff_node = make_tex_node(diffuse, 400)
        links.new(diff_node.outputs['Color'],
                  principled_node.inputs['Base Color'])

    if roughness is not None:
        rough_node = make_tex_node(roughness, 100)
        links.new(rough_node.outputs['Color'],
                  principled_node.inputs['Roughness'])

    if normal is not None:
        norm_node = make_tex_node(normal, -200)
        norm_map_node = nodes.new(type='ShaderNodeNormalMap')
        norm_map_node.location.x -= 200
        norm_map_node.location.y -= 200
        links.new(norm_node.outputs['Color'], norm_map_node.inputs['Color'])
        links.new(norm_map_node.outputs['Normal'],
                  principled_node.inputs['Normal'])

    return mat
