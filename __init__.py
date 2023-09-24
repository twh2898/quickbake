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

        bake_nodes = self.setup_nodes(obj)

        props = context.scene.QuickBakeToolPropertyGroup

        for pass_type in ['DIFFUSE', 'NORMAL', 'ROUGHNESS']:
            img = self.setup_image(obj,
                                   bake_nodes,
                                   props.bake_name,
                                   pass_type.lower(),
                                   props.reuse_tex)

            # image_name = obj.name + '_' + props.bake_name
            # img = bpy.data.images.get(image_name)
            # if img is None or props.reuse_tex:
            #     img = bpy.data.images.new(image_name, 1024, 1024)

            # for node in bake_nodes:
            #     node.image = img

            bake_uv = self.setup_uv(obj, props.bake_uv)

            self.report({'INFO'}, 'Baking pass %s' % pass_type)

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.bake(type=pass_type,
                                pass_filter={'COLOR'},
                                save_mode='EXTERNAL',
                                uv_layer='bake_uv')

            # img.save_render(filepath='/tmp/baked.png')

        self.report({'INFO'}, 'Baking complete')

        if props.clean_up:
            self.cleanup_nodes(obj)

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

        row = layout.row()
        row.prop(props, "reuse_tex")

        row = layout.row()
        row.prop(props, "clean_up")


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
