# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

bl_info = {
    "name": "quickbake",
    "author": "Thomas Harrison",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Object"
}


class MY_OT_rem_doubles_bmesh(bpy.types.Operator):
    """Remove Doubles on Objects in Selection"""
    bl_idname = "object.remove_doubles_bmesh"
    bl_label = "Remove Doubles (bmesh)"
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
        meshes = set(
            o.data for o in context.selected_objects if o.type == 'MESH')
        verts_before = sum(len(o.vertices) for o in meshes)

        return {'FINISHED'}


class MY_PT_custom(bpy.types.Panel):
    """Creates a Sub-Panel in the Property Area of the 3D View"""
    bl_label = "My Tools"
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
        row.operator(MY_OT_rem_doubles_bmesh.bl_idname)
        layout.separator()

        row = layout.row()
        row.label(text="{} Objects in Selection".format(len(sel_objs)))

        row = layout.row()
        row.label(text="Vertex Count: {}".format(sel_vert_count))


def register():
    bpy.utils.register_class(MY_OT_rem_doubles_bmesh)
    bpy.utils.register_class(MY_PT_custom)


def unregister():
    bpy.utils.unregister_class(MY_OT_rem_doubles_bmesh)
    bpy.utils.unregister_class(MY_PT_custom)


if __name__ == "__main__":
    register()
