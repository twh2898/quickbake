# import os
import bpy
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

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


def setup_bake_image(obj, bake_nodes, bake_name, pass_name, reuse_tex, is_data=False):
    _l.info('Creating image for baking object %s', obj.name)

    image_name = obj.name + '_' + bake_name + '_' + pass_name
    _l.debug('Image name %s', image_name)

    img = bpy.data.images.get(image_name)
    if img is None or not reuse_tex:
        img = bpy.data.images.new(image_name, 1024, 1024, is_data=is_data)

    else:
        _l.debug('Using existing image')

    for node in bake_nodes:
        node.image = img

    return img


def setup_bake_material(obj, name, bake_uv_name, diffuse, roughness, normal):
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
    uv_node.location.x -= 800

    mapping_node = nodes.new(type='ShaderNodeMapping')
    mapping_node.location.x -= 600
    links.new(uv_node.outputs['UV'], mapping_node.inputs['Vector'])

    def make_tex_node(img):
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.image = img
        tex_node.location.y += 300
        tex_node.location.x -= 400

        # links.new(mapping_node.outputs[0], tex_node.inputs['Vector'])
        links.new(mapping_node.outputs['Vector'], tex_node.inputs['Vector'])

        # TODO: color space if not set by default
        # tex_node.image.colorspace_settings.name = '...'

        return tex_node

    diff_node = make_tex_node(diffuse)
    links.new(diff_node.outputs['Color'], principled_node.inputs['Base Color'])

    rough_node = make_tex_node(roughness)
    links.new(rough_node.outputs['Color'], principled_node.inputs['Roughness'])

    norm_node = make_tex_node(normal)
    norm_map_node = nodes.new(type='ShaderNodeNormalMap')
    norm_map_node.location.x -= 300
    links.new(norm_node.outputs['Color'], norm_map_node.inputs['Color'])
    links.new(norm_map_node.outputs['Normal'],
              principled_node.inputs['Normal'])

    return mat


class QuickBake_OT_bake(bpy.types.Operator):
    '''Do the bake.'''
    bl_idname = 'render.quickbake_bake'
    bl_label = 'Bake'
    bl_options = {'REGISTER', 'UNDO'}

    # material:

    @classmethod
    def poll(cls, context):
        obj: bpy.types.Object = context.active_object  # type: ignore
        return (obj is not None and obj.type == 'MESH')

    def create_material(self,
                        obj,
                        name,
                        uv_name,
                        diffuse=None,
                        roughness=None,
                        normal=None):
        _l.info('Creating bake material %s for object %s', name, obj.name)

        mat = bpy.data.materials.get(name)
        if mat is not None:
            _l.debug('Material already exists, skipping')
            self.report({'INFO'}, 'Material already exists, skipping')
            return mat

        mat = setup_bake_material(
            obj, name, uv_name, diffuse, roughness, normal)
        return mat

    def execute(self, context):
        obj = context.active_object

        if obj is None:
            self.report({'ERROR'}, 'No active object')
            return {'CANCELLED'}

        if obj.type != 'MESH':
            self.report({'ERROR'}, 'Active object must be a mesh')
            return {'CANCELLED'}

        props = context.scene.QuickBakeToolPropertyGroup

        bake_nodes = setup_bake_nodes(obj)
        bake_uv = setup_bake_uv(obj, props.bake_uv)

        passes = []
        if props.diffuse_enabled:
            passes.append('DIFFUSE')
        if props.normal_enabled:
            passes.append('NORMAL')
        if props.roughness_enabled:
            passes.append('ROUGHNESS')
        if props.ao_enabled:
            passes.append('AO')
        if props.shadow_enabled:
            passes.append('SHADOW')
        if props.position_enabled:
            passes.append('POSITION')
        if props.uv_enabled:
            passes.append('UV')
        if props.emit_enabled:
            passes.append('EMIT')
        if props.environment_enabled:
            passes.append('ENVIRONMENT')
        if props.glossy_enabled:
            passes.append('GLOSSY')
        if props.transmission_enabled:
            passes.append('TRANSMISSION')

        _l.debug('Enabled bake passes: %s', repr(passes))

        img_cache = {}

        for pass_type in passes:
            _l.info('Baking pass %s', pass_type)

            img = setup_bake_image(obj,
                                   bake_nodes,
                                   props.bake_name,
                                   pass_type.lower(),
                                   props.reuse_tex,
                                   pass_type == 'NORMAL')

            img_cache[pass_type] = img

            self.report({'INFO'}, 'Baking pass %s' % pass_type)

            _l.debug('Making object %s active', obj.name)
            bpy.context.view_layer.objects.active = obj

            save_mode = 'INTERNAL'
            filepath = ''

            # if props.save_img:
            #     _l.debug('Saving image externally')

            #     img_base_path = bpy.path.abspath(props.image_path)

            #     save_mode = 'EXTERNAL'
            #     filepath = os.path.join(img_base_path, img.name + '.png')
            #     _l.debug('Filepath %s', filepath)

            self.report({'INFO'}, 'Save mode %s' % save_mode)

            bpy.ops.object.bake(type=pass_type,
                                pass_filter={'COLOR'},
                                uv_layer='bake_uv',
                                use_clear=True,
                                # save_mode='INTERNAL',
                                # save_mode=save_mode,
                                # filepath=filepath,
                                )

            # if props.save_img:
            #     _l.debug('Saving image externally %s', img.name)

            #     # filepath = os.path.join(props.image_path, img.name + '.png')
            #     img.filepath = filepath
            #     img.file_format = 'PNG'
            #     # img.save_render(filepath=filepath)
            #     img.save()

        self.report({'INFO'}, 'Baking complete')

        if props.clean_up and not props.create_mat:
            cleanup_bake_nodes(obj)

        if props.create_mat:
            self.create_material(obj,
                                 props.mat_name,
                                 props.bake_uv,
                                 img_cache.get('DIFFUSE'),
                                 img_cache.get('ROUGHNESS'),
                                 img_cache.get('NORMAL'))

        return {'FINISHED'}
