import bpy

from .properties import QuickBakeToolPropertyGroup
from .op import QuickBake_OT_bake
from .panel import QuickBake_PT_main

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
