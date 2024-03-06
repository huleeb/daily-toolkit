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


@addon_updater_ops.make_annotations
class UpdaterPreferences(bpy.types.AddonPreferences):
	"""bare-bones preferences"""
	bl_idname = __package__

	# Addon updater preferences.

	auto_check_update = bpy.props.BoolProperty(
		name="Auto-check for Update",
		description="If enabled, auto-check for updates using an interval",
		default=False)

	updater_interval_months = bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0)

	updater_interval_days = bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31)

	updater_interval_hours = bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23)

	updater_interval_minutes = bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59)

	def draw(self, context):
		layout = self.layout

		# Works best if a column, or even just self.layout.
		mainrow = layout.row()
		col = mainrow.column()

		# Updater draw function, could also pass in col as third arg.
		addon_updater_ops.update_settings_ui(self, context)

		# Alternate draw function, which is more condensed and can be
		# placed within an existing draw function. Only contains:
		#   1) check for update/update now buttons
		#   2) toggle for auto-check (interval will be equal to what is set above)
		# addon_updater_ops.update_settings_ui_condensed(self, context, col)

		# Adding another column to help show the above condensed ui as one column
		# col = mainrow.column()
		# col.scale_y = 2
		# ops = col.operator("wm.url_open","Open webpage ")
		# ops.url=addon_updater_ops.updater.website

classes = (
    ToggleOrbitAroundSelectionOperator,
    KeymapPreferences,
	UpdaterPanel,
    UpdaterPreferences
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
    add_key_to_map(kc,config='3D View',cls='toolkit.toggle_orbit',key='X',shift=True,alt=True,ctrl=True)


def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()