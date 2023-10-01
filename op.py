import os
import bpy

import logging

_l = logging.getLogger(__name__)


def setup_bake_nodes(obj):
    """Create material nodes required for baking."""
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
    """Remove material nodes created for baking by setup_bake_nodes."""
    _l.info('Cleaning up bake nodes for object %s', obj.name)

    for mat in obj.data.materials:
        _l.debug('Clean up nodes for material %s', mat.name)

        for n in mat.node_tree.nodes:
            if n.name == 'Bake_node':
                _l.debug('Remove bake node %s', n.name)
                mat.node_tree.nodes.remove(n)


def setup_bake_uv(obj, name):
    """Create a uv layer to unwrap obj for baking."""
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


def setup_bake_image(obj, bake_nodes, bake_name, pass_name, reuse_tex):
    _l.info('Creating image for baking object %s', obj.name)

    image_name = obj.name + '_' + bake_name + '_' + pass_name
    _l.debug('Image name %s', image_name)

    img = bpy.data.images.get(image_name)
    if img is None or not reuse_tex:
        img = bpy.data.images.new(image_name, 1024, 1024)

    else:
        _l.debug('Using existing image')

    for node in bake_nodes:
        node.image = img

    return img


class QuickBake_OT_bake(bpy.types.Operator):
    """Do the bake."""
    bl_idname = "render.quickbake_bake"
    bl_label = "Bake"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'MESH')

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

        for pass_type in passes:
            _l.info('Baking pass %s', pass_type)

            img = setup_bake_image(obj,
                                   bake_nodes,
                                   props.bake_name,
                                   pass_type.lower(),
                                   props.reuse_tex)

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

        if props.clean_up:
            cleanup_bake_nodes(obj)

        return {'FINISHED'}
