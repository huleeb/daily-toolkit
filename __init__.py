import bpy
import rna_keymap_ui
from . import addon_updater_ops

bl_info = {
    "name": "StupidGiant Toolkit",
    "author": "huleeb",
    "blender": (4, 0, 0),
    "version": (0, 0, 1),
    "category": "3D View"
}

class ToggleOrbitAroundSelectionOperator(bpy.types.Operator):
    """Toggle Orbit Around Selection"""
    bl_idname = "toolkit.toggle_orbit"
    bl_label = "Toggle Orbit Around Selection"

    def execute(self, context):
        current_state = bpy.context.preferences.inputs.use_rotate_around_active
        
        if current_state:
            self.report({'INFO'}, 'Toggle Orbit Around Selection: ON')
        else:
            self.report({'INFO'}, 'Toggle Orbit Around Selection: OFF')
        
        bpy.context.preferences.inputs.use_rotate_around_active = not current_state
        return {'FINISHED'}
    

addon_keymaps = []

# Addon preference panel
class KeymapPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    def draw(self, context):
        layout = self.layout
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            layout.label(text="Shortcuts:", icon='OPTIONS')
            for km, kmi in addon_keymaps:
                row = layout.row()
                rna_keymap_ui.draw_kmi([], kc, km, kmi, row, 0)

classes = (
    ToggleOrbitAroundSelectionOperator,
    KeymapPreferences,
)

def register():
    addon_updater_ops.register(bl_info)

    for cls in classes:
        addon_updater_ops.make_annotations(cls)
        bpy.utils.register_class(cls)
    register_keymap()
    
def unregister():
    addon_updater_ops.unregister()
    for cls in classes:
        bpy.utils.unregister_class(cls)
    unregister_keymaps()

# Function to easily create Custom Shortcut in the preference panel
def add_key_to_map(kc,config='3D View',space_type='VIEW_3D',cls='',key='',action='PRESS',shift=False,alt=False,ctrl=False):
    km = kc.get(config)
    if km:
        km = kc.new(config, space_type=space_type)
    kmi = km.keymap_items.new(cls, key, action, shift=shift,alt=alt,ctrl=ctrl)
    addon_keymaps.append((km, kmi))

def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon.keymaps
    add_key_to_map(kc,config='3D View',cls='toolkit.toggle_orbit',key='X',shift=True,alt=True,ctrl=True)


def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()