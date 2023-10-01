"""QuickBake n Menu."""

import bpy

from .op import QuickBake_OT_bake


class QuickBake_PT_main(bpy.types.Panel):
    """Creates a Sub-Panel in the Property Area of the 3D View."""

    bl_label = "Quick Bake"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_context = "objectmode"

    def draw(self, context):
        """Override Panel draw method."""
        layout = self.layout

        row = layout.row()
        row.operator(QuickBake_OT_bake.bl_idname)
        layout.separator()

        props = context.scene.QuickBakeToolPropertyGroup

        layout.label(text='Texture')
        row = layout.row()
        row.prop(props, "bake_name")

        row = layout.row()
        row.prop(props, "bake_uv")

        row = layout.row()
        row.prop(props, "bake_size")

        layout.separator()
        layout.label(text='Material')
        row = layout.row()
        row.prop(props, "create_mat")

        row = layout.row()
        row.prop(props, "mat_name")

        layout.separator()
        layout.label(text='Options')
        row = layout.row()
        row.enabled = not props.create_mat
        row.prop(props, "reuse_tex")

        row = layout.row()
        row.enabled = not props.create_mat
        row.prop(props, "clean_up")

        # layout.separator()
        # layout.label(text='Output')
        # row = layout.row()
        # row.prop(props, "save_img")

        # row = layout.row()
        # row.prop(props, "image_path")

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
