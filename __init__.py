import os
import bpy

bl_info = {
    "name": "Quick Bake",
    "author": "Thomas Harrison",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Render"
}


class QuickBakeToolPropertyGroup(bpy.types.PropertyGroup):
    reuse_tex: bpy.props.BoolProperty(  # type: ignore
        name="Re-use Texture",
        description="Use the texture from previous bakes",
        default=True
    )

    clean_up: bpy.props.BoolProperty(  # type: ignore
        name="Clean Up",
        description="Remove generated nodes after baking",
        default=True
    )

    save_img: bpy.props.BoolProperty(  # type: ignore
        name="Save Images",
        description="Write images to file after baking",
        default=False
    )

    image_path: bpy.props.StringProperty(  # type: ignore
        name="Texture Path",
        description="Directory for baking output",
        default='',
        subtype='DIR_PATH'
    )

    bake_name: bpy.props.StringProperty(  # type: ignore
        name="Name",
        description="Name used fot the baked texture images",
        default="BakeTexture"
    )

    bake_uv: bpy.props.StringProperty(  # type: ignore
        name="UV",
        description="Name used fot the uv bake layer",
        default="bake_uv"
    )

    diffuse_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Diffuse",
        description="Bake the diffuse map",
        default=True
    )

    normal_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Normal",
        description="Bake the normal map",
        default=True
    )

    roughness_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Roughness",
        description="Bake the roughness map",
        default=True
    )

    ao_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Ao",
        description="Bake the Ao map",
        default=False
    )

    shadow_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Shadow",
        description="Bake the Shadow map",
        default=False
    )

    position_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Position",
        description="Bake the Position map",
        default=False
    )

    uv_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Uv",
        description="Bake the Uv map",
        default=False
    )

    emit_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Emit",
        description="Bake the Emit map",
        default=False
    )

    environment_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Environment",
        description="Bake the Environment map",
        default=False
    )

    glossy_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Glossy",
        description="Bake the Glossy map",
        default=False
    )

    transmission_enabled: bpy.props.BoolProperty(  # type: ignore
        name="Transmission",
        description="Bake the Transmission map",
        default=False
    )


class QuickBake_OT_bake(bpy.types.Operator):
    """Do the bake."""
    bl_idname = "render.quickbake_bake"
    bl_label = "Bake"
    bl_options = {'REGISTER', 'UNDO'}

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
            if layer.active:
                active_layer = layer
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
                                uv_layer='bake_uv',
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
            obj.data.uv_layers.remove(bake_uv)

        return {'FINISHED'}


class QuickBake_PT_main(bpy.types.Panel):
    """Creates a Sub-Panel in the Property Area of the 3D View"""
    bl_label = "Quick Bake"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_context = "objectmode"

    def draw(self, context):
        sel_objs = context.selected_objects
        sel_vert_count = sum(len(o.data.vertices)
                             for o in sel_objs if o.type == 'MESH')

        layout = self.layout

        row = layout.row()
        row.operator(QuickBake_OT_bake.bl_idname)
        layout.separator()

        props = context.scene.QuickBakeToolPropertyGroup

        row = layout.row()
        row.prop(props, "bake_name")

        row = layout.row()
        row.prop(props, "bake_uv")

        layout.separator()
        layout.label(text='Options')
        row = layout.row()
        row.prop(props, "reuse_tex")

        row = layout.row()
        row.prop(props, "clean_up")

        layout.separator()
        layout.label(text='Output')
        row = layout.row()
        row.prop(props, "save_img")

        row = layout.row()
        row.prop(props, "image_path")

        layout.separator()
        layout.label(text='Layers')
        row = layout.row()
        row.prop(props, 'diffuse_enabled')

        row = layout.row()
        row.prop(props, 'normal_enabled')

        row = layout.row()
        row.prop(props, 'roughness_enabled')

        row = layout.row()
        row.prop(props, 'ao_enabled')

        row = layout.row()
        row.prop(props, 'shadow_enabled')

        row = layout.row()
        row.prop(props, 'position_enabled')

        row = layout.row()
        row.prop(props, 'uv_enabled')

        row = layout.row()
        row.prop(props, 'emit_enabled')

        row = layout.row()
        row.prop(props, 'environment_enabled')

        row = layout.row()
        row.prop(props, 'glossy_enabled')

        row = layout.row()
        row.prop(props, 'transmission_enabled')

        row = layout.row()


def register():
    bpy.utils.register_class(QuickBake_OT_bake)
    bpy.utils.register_class(QuickBake_PT_main)
    bpy.utils.register_class(QuickBakeToolPropertyGroup)
    bpy.types.Scene.QuickBakeToolPropertyGroup = bpy.props.PointerProperty(
        type=QuickBakeToolPropertyGroup)


def unregister():
    bpy.utils.unregister_class(QuickBake_OT_bake)
    bpy.utils.unregister_class(QuickBake_PT_main)
    bpy.utils.unregister_class(QuickBakeToolPropertyGroup)
    del bpy.types.Scene.QuickBakeToolPropertyGroup


if __name__ == "__main__":
    register()
