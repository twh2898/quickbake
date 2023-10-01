# import os
import bpy
from .bake import setup_bake_image, setup_bake_nodes, setup_bake_uv
from .material import setup_bake_material

import logging

_l = logging.getLogger(__name__)


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
