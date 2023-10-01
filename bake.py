"""Baking helper functions."""

import bpy

import logging

_l = logging.getLogger(__name__)


def setup_bake_nodes(obj):
    '''Create material nodes required for baking.'''
    _l.info('Creating bake nodes for object %s', obj.name)

    bake_nodes = []
    for mat in obj.data.materials:
        _l.debug('Creating nodes for material %s', mat.name)

        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        texture_node = nodes.new('ShaderNodeTexImage')
        texture_node.name = 'Bake_node'
        texture_node.select = True
        nodes.active = texture_node
        bake_nodes.append(texture_node)

    return bake_nodes


def cleanup_bake_nodes(obj):
    '''Remove material nodes created for baking by setup_bake_nodes.'''
    _l.info('Cleaning up bake nodes for object %s', obj.name)

    for mat in obj.data.materials:
        _l.debug('Clean up nodes for material %s', mat.name)

        for n in mat.node_tree.nodes:
            if n.name == 'Bake_node':
                _l.debug('Remove bake node %s', n.name)
                mat.node_tree.nodes.remove(n)


def setup_bake_uv(obj, name):
    '''Create a uv layer to unwrap obj for baking.'''
    _l.info('Creating uv layer %s for baking', name)

    def unwrap_uv(obj, uv):
        _l.info('Unwrapping object %s to layer %s', obj.name, uv.name)

        active_layer = None
        for layer in obj.data.uv_layers:
            if layer.active:
                _l.debug('Found active layer %s', layer.name)
                active_layer = layer
                break

        uv.active = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(island_margin=0.001)
        bpy.ops.object.mode_set(mode='OBJECT')
        uv.active = False

        if active_layer is not None:
            _l.debug('Restoring active layer %s', active_layer.name)
            active_layer.active = True  # type: ignore

    bake_uv = obj.data.uv_layers.get(name)
    if bake_uv is None:
        bake_uv = obj.data.uv_layers.new(name=name)
        unwrap_uv(obj, bake_uv)

    else:
        _l.debug('Using existing uv layer')

    return bake_uv


def setup_bake_image(obj, bake_nodes, bake_name, bake_size, pass_name, reuse_tex, is_data=False):
    _l.info('Creating image for baking object %s', obj.name)

    image_name = obj.name + '_' + bake_name + '_' + pass_name
    _l.debug('Image name %s', image_name)

    img = bpy.data.images.get(image_name)
    if img is None or not reuse_tex:
        img = bpy.data.images.new(image_name, bake_size, bake_size, is_data=is_data)

    else:
        _l.debug('Using existing image')

    for node in bake_nodes:
        node.image = img

    return img
