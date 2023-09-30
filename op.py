import os
import bpy


class QuickBake_OT_bake(bpy.types.Operator):
    """Do the bake."""
    bl_idname = "render.quickbake_bake"
    bl_label = "Bake"
    bl_options = {'REGISTER', 'UNDO'}

    def _l(self, msg):
        self.report({'INFO'}, msg)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'MESH')

    def setup_nodes(self, obj):
        bake_nodes = []
        for mat in obj.data.materials:
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            texture_node = nodes.new('ShaderNodeTexImage')
            texture_node.name = 'Bake_node'
            texture_node.select = True
            nodes.active = texture_node
            bake_nodes.append(texture_node)
        return bake_nodes

    def cleanup_nodes(self, obj):
        for mat in obj.data.materials:
            for n in mat.node_tree.nodes:
                if n.name == 'Bake_node':
                    mat.node_tree.nodes.remove(n)

    def _unwrap_uv(self, obj, uv):
        active_layer = None
        for layer in obj.data.uv_layers:
            self._l('Unwrap checking layer %s' % layer.name)
            if layer.active:
                self._l('Layer %s is active' % layer.name)
                active_layer = layer
                self._last_active = active_layer
                break
        uv.active = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(island_margin=0.001)
        bpy.ops.object.mode_set(mode='OBJECT')
        uv.active = False
        active_layer.active = True

    def setup_uv(self, obj, name):
        bake_uv = obj.data.uv_layers.get(name)
        if bake_uv is None:
            bake_uv = obj.data.uv_layers.new(name=name)
            self._unwrap_uv(obj, bake_uv)
        return bake_uv

    def cleanup_uv(self, obj, name):
        bake_uv = obj.data.uv_layers.get(name)
        if bake_uv is not None:
            obj.data.uv_layers.remove(bake_uv)

        if self._last_active is not None:
            self._last_active.active = True

        for layer in obj.data.uv_layers:
            self._l('Checking layer %s' % layer.name)
            if layer.active:
                self._l('Found active layer %s' % layer.name)
                break
        else:
            self._l('Did not find active layer')

        # self.report({'INFO'}, 'Baking pass %s' % dir(obj.data.uv_layers.active))
        # obj.data.uv_layers.active = True

    def setup_image(self, obj, bake_nodes, bake_name, pass_name, reuse_tex):
        image_name = obj.name + '_' + bake_name + '_' + pass_name
        img = bpy.data.images.get(image_name)
        if img is None or not reuse_tex:
            img = bpy.data.images.new(image_name, 1024, 1024)

        for node in bake_nodes:
            node.image = img

        return img

    def execute(self, context):
        obj = context.active_object

        if obj is None:
            self.report({'ERROR'}, 'No active object')
            return {'CANCELLED'}

        if obj.type != 'MESH':
            self.report({'ERROR'}, 'Active object must be a mesh')
            return {'CANCELLED'}

        props = context.scene.QuickBakeToolPropertyGroup

        bake_nodes = self.setup_nodes(obj)
        bake_uv = self.setup_uv(obj, props.bake_uv)

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

        for pass_type in passes:
            img = self.setup_image(obj,
                                   bake_nodes,
                                   props.bake_name,
                                   pass_type.lower(),
                                   props.reuse_tex)

            self.report({'INFO'}, 'Baking pass %s' % pass_type)

            bpy.context.view_layer.objects.active = obj
            save_mode = 'INTERNAL'
            filepath = ''
            if props.save_img:
                save_mode = 'EXTERNAL'
                filepath = os.path.join(props.image_path, img.name + '.png')

            bpy.ops.object.bake(type=pass_type,
                                pass_filter={'COLOR'},
                                uv_layer=props.bake_uv,
                                save_mode=save_mode,
                                filepath=filepath,
                                )

            # if props.save_img:
            #     filepath = os.path.join(props.image_path, img.name + '.png')
            #     self.report({'INFO'}, 'Baking cwd is %s' % os.getcwd())
            #     self.report({'INFO'}, 'Baking path is %s' % filepath)
            #     img.filepath_raw = filepath
            #     img.file_format = 'PNG'
            #     img.save_render(filepath=filepath)

        self.report({'INFO'}, 'Baking complete')

        if props.clean_up:
            self.cleanup_nodes(obj)
            self.cleanup_uv(obj, props.bake_uv)

        return {'FINISHED'}
