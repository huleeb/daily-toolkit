import bpy
import rna_keymap_ui
from . import addon_updater_ops

bl_info = {
    "name": "StupidGiant Toolkit",
    "author": "huleeb",
    "blender": (4, 0, 0),
    "version": (0, 0, 3),
    "category": "3D View"
}

class ToggleOrbitAroundSelectionOperator(bpy.types.Operator):
    """Toggle Orbit Around Selection"""
    bl_idname = "toolkit.toggle_orbit"
    bl_label = "Toggle Orbit Around Selection"

    def execute(self, context):
        current_state = bpy.context.preferences.inputs.use_rotate_around_active
        
        bpy.context.preferences.inputs.use_rotate_around_active = not current_state
        
        if not current_state:
            self.report({'INFO'}, 'Toggle Orbit Around Selection: ON')
        else:
            self.report({'INFO'}, 'Toggle Orbit Around Selection: OFF')
        return {'FINISHED'}
    

class EasyDecimate(bpy.types.Operator):
	"""Decimate and hide new object"""
	bl_idname = "toolkit.easy_decimate"
	bl_label = "Decimate and hide new object"

	def execute(self, context):
		if bpy.context.selected_objects:
			obj = bpy.context.selected_objects[0]
            
			new_obj = obj.copy()
			new_obj.name = obj.name + "_decimated"
			new_obj.data = obj.data.copy()
			bpy.context.collection.objects.link(new_obj)
            
			obj.parent = new_obj
			obj.display_type = 'BOUNDS'
            
			bpy.context.view_layer.objects.active = new_obj
            
			mod_dec = new_obj.modifiers.new(type='DECIMATE', name='Decimate')
			new_obj.modifiers["Decimate"].ratio = 0.1
			bpy.ops.object.modifier_apply(modifier=mod_dec.name)
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_all(action='SELECT')
			bpy.ops.uv.smart_project(angle_limit=66)
			bpy.ops.object.mode_set(mode='OBJECT')
			
			new_obj.visible_camera = False
			new_obj.visible_diffuse = False
			new_obj.visible_glossy = False
			new_obj.visible_transmission = False
			new_obj.visible_volume_scatter = False
			new_obj.visible_shadow = False
		return {'FINISHED'}


addon_keymaps = []

# Addon preference panel
class AddonPreference(bpy.types.AddonPreferences):
	bl_idname = __name__
    
	auto_check_update = bpy.props.BoolProperty(name="Auto-check for Update", description="If enabled, auto-check for updates using an interval", default=False)
	updater_interval_months = bpy.props.IntProperty( name='Months', description="Number of months between checking for updates", default=0, min=0)
	updater_interval_days = bpy.props.IntProperty( name='Days', description="Number of days between checking for updates", default=7, min=0, max=31)
	updater_interval_hours = bpy.props.IntProperty( name='Hours', description="Number of hours between checking for updates", default=0, min=0, max=23)
	updater_interval_minutes = bpy.props.IntProperty( name='Minutes', description="Number of minutes between checking for updates", default=0, min=0, max=59)
    
	def draw(self, context):
		layout = self.layout
		# Works best if a column, or even just self.layout.
		mainrow = layout.row()
		col = mainrow.column()

		addon_updater_ops.update_settings_ui(self, context)
          
		wm = bpy.context.window_manager
		kc = wm.keyconfigs.addon
		if kc:
			layout.label(text="Shortcuts:", icon='OPTIONS')
			for km, kmi in addon_keymaps:
				row = layout.row()
				rna_keymap_ui.draw_kmi([], kc, km, kmi, row, 0)

class UpdaterPanel(bpy.types.Panel):
	"""Panel to popup notice and ignoring functionality"""
	bl_label = "Updater Panel"
	bl_idname = "OBJECT_PT_UpdaterPanel_hello"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS' if bpy.app.version < (2, 80) else 'UI'
	bl_context = "objectmode"
	bl_category = "Tools"

	def draw(self, context):
		layout = self.layout

		# Call to check for update in background.
		# Note: built-in checks ensure it runs at most once, and will run in
		# the background thread, not blocking or hanging blender.
		# Internally also checks to see if auto-check enabled and if the time
		# interval has passed.
		addon_updater_ops.check_for_update_background()

		layout.label(text="Updater Addon")
		layout.label(text="")

		col = layout.column()
		col.scale_y = 0.7
		col.label(text="If an update is ready,")
		col.label(text="popup triggered by opening")
		col.label(text="this panel, plus a box ui")

		# Could also use your own custom drawing based on shared variables.
		if addon_updater_ops.updater.update_ready:
			layout.label(text="Custom update message", icon="INFO")
		layout.label(text="")

		# Call built-in function with draw code/checks.
		addon_updater_ops.update_notice_box_ui(self, context)


classes = (
	AddonPreference,
	UpdaterPanel,
    ToggleOrbitAroundSelectionOperator,
    EasyDecimate
)

def register():
    addon_updater_ops.register(bl_info)

    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymap()
    
def unregister():
    addon_updater_ops.unregister()
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
             continue
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
    
	# Every addon shortcuts:
    add_key_to_map(kc,config='3D View',cls='toolkit.toggle_orbit',key='X',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,config='3D View',cls='toolkit.easy_decimate',key='D',shift=True,alt=True,ctrl=True)
    


def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()