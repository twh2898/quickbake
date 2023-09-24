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
    merge_dist: bpy.props.FloatProperty(  # type: ignore
        name="Merge Distance",
        description="Merge Distance",
        min=0.0,
        step=0.1,
        default=0.02
    )


class QuickBake_OT_bake(bpy.types.Operator):
    """Do the bake."""
    bl_idname = "render.quickbake_bake"
    bl_label = "Bake"
    bl_options = {'REGISTER', 'UNDO'}

    merge_dist: bpy.props.FloatProperty(  # type: ignore
        name="Merge Distance",
        description="Merge Distance",
        min=0.0,
        step=0.1,
        default=0.02
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'MESH')

    def execute(self, context):
        obj = context.active_object
        props = context.scene.QuickBakeToolPropertyGroup
        self.merge_dist = props.merge_dist


        if obj is None:
            self.report({'ERROR'}, 'No active object')
            return {'CANCELLED'}

        if obj.type != 'MESH':
            self.report({'ERROR'}, 'Active object must be a mesh')
            return {'CANCELLED'}

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
        row.prop(props, "merge_dist")

        row = layout.row()
        row.label(text="{} Objects in Selection".format(len(sel_objs)))

        row = layout.row()
        row.label(text="Vertex Count: {}".format(sel_vert_count))


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
