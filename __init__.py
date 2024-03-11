import bpy
import rna_keymap_ui
from . import addon_updater_ops

bl_info = {
    "name": "Daily Toolkit",
    "author": "huleeb & stupidgiant",
    "blender": (4, 0, 0),
    "version": (0, 0, 3),
    "location": "View3D > Tools > daily",
    "category": "Generic",
    "description": "utility functions to speed up workflow"
}

#TODO:
#   - add undo feature in all classes
#
#	- when mouse is over modifier window 
#   	have shortcuts specific:
#		- ctrl-m for mask modifier and create Vertex Group 'Group'
#	- Toggle with F2 'Black and White' ColorRamp from compositor
#       - get last item from tree of compositor, if colorramp, toggle on/off?
#
#
#
#
#
#

def disable_outline_options():
    for area in bpy.context.screen.areas:
        if area.type == 'OUTLINER':
            space = area.spaces.active

            space.show_restrict_column_viewport = False
            space.show_restrict_select = False

def execute_outliner_filter_restricted():
    for area in bpy.context.screen.areas:
        if area.type == 'OUTLINER':
            space = area.spaces.active

            space.show_restrict_column_viewport = False
            space.show_restrict_column_select = False

class outliner_filter_restricted(bpy.types.Operator):
    """Removes Viewport and Selectable restricted filters in outliner"""
    bl_label = "Outliner Filter"
    bl_idname = "toolkit.outliner_filter_restricted"

    def execute(self, context):
        execute_outliner_filter_restricted()
        return {'FINISHED'}

class flip_aspect_ratio(bpy.types.Operator):
    """Toggles aspect ratio between portrait to landscape"""
    bl_label = "Flip Aspect Ratio"
    bl_idname = "toolkit.flip_aspect_ratio"

    def execute(self, context):
        x = bpy.context.scene.render.resolution_x
        y = bpy.context.scene.render.resolution_y
        bpy.context.scene.render.resolution_x = y
        bpy.context.scene.render.resolution_y = x
        return {'FINISHED'}

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

class material_setting_to_bump_only(bpy.types.Operator):
    bl_label = "Bump Only"
    bl_idname = "toolkit.material_setting_to_bump_only"

    def set_material_displacement_to_bump_only(material):
        if material.use_nodes:
            principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
            if principled_bsdf:
                material.cycles.displacement_method = 'BUMP'
                
                # Remove existing displacement node if any
                # displacement_node = None
                # for node in material.node_tree.nodes:
                #     if node.type == 'DISPLACEMENT':
                #         displacement_node = node
                #         break
                # if displacement_node:
                #     material.node_tree.nodes.remove(displacement_node)
    
    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data.materials:
                for material_slot in obj.material_slots:
                    if material_slot.material:
                        material_setting_to_bump_only.set_material_displacement_to_bump_only(material_slot.material)
        self.report({'INFO'}, 'Set all material displacement method to: Bump')
        return {'FINISHED'}

class modifier_mask(bpy.types.Operator):
    """Adds a Mask modifier to every selected object. Along with an empty Vertex Group"""
    bl_label = "Mask Modifier"
    bl_idname = "toolkit.modifier_mask"

    def execute(self, context):
        if bpy.context.selected_objects:
            if bpy.context.area == 'PROPERTIES':
                for obj in bpy.context.selected_objects:
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.vertex_group_add()
                    mod_dec = obj.modifiers.new(type='MASK', name='Mask')
            bpy.ops.ed.undo_push()
        return {'FINISHED'}

addon_keymaps_view3d = []
addon_keymaps_properties = []

# Addon preference panel
@addon_updater_ops.make_annotations
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
			layout.label(text="Viewport:", icon='OPTIONS')
			for km, kmi in addon_keymaps_view3d:
				row = layout.row()
				rna_keymap_ui.draw_kmi([], kc, km, kmi, row, 0)
			layout.label(text="Properties:", icon='OPTIONS')
			for km, kmi in addon_keymaps_properties:
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

class DAILY_PT_toolkit_panel(bpy.types.Panel):
    bl_label = "daily"
    bl_idname = "DAILY_PT_toolkit_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'daily'

    def draw(self, context):
        layout = self.layout
        layout.operator("toolkit.outliner_filter_restricted")
        layout.operator("toolkit.material_setting_to_bump_only")
        layout.operator("toolkit.flip_aspect_ratio")
        layout.operator("toolkit.toggle_orbit")
        layout.operator("toolkit.easy_decimate")

classes = (
	AddonPreference,
	UpdaterPanel,
    ToggleOrbitAroundSelectionOperator,
    EasyDecimate,
    DAILY_PT_toolkit_panel,
    material_setting_to_bump_only,
    outliner_filter_restricted,
    flip_aspect_ratio,
    modifier_mask
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
    if space_type == 'VIEW_3D':
        addon_keymaps_view3d.append((km, kmi))
    if space_type == 'PROPERTIES':
        addon_keymaps_properties.append((km, kmi))

def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon.keymaps
    
	# Viewport shortcuts:
    add_key_to_map(kc,config='3D View',cls='toolkit.toggle_orbit',key='X',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,config='3D View',cls='toolkit.easy_decimate',key='D',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,config='3D View',cls='toolkit.outliner_filter_restricted',key='K',shift=False,alt=False,ctrl=False)
    add_key_to_map(kc,config='3D View',cls='toolkit.material_setting_to_bump_only',key='B',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,config='3D View',cls='toolkit.flip_aspect_ratio',key='P',shift=True,alt=True,ctrl=True)

	# Properties shortcuts:
    add_key_to_map(kc,config='Properties',space_type='PROPERTIES',cls='toolkit.modifier_mask',key='M',shift=False,alt=False,ctrl=True)


def unregister_keymaps():
    for km, kmi in addon_keymaps_view3d:
        km.keymap_items.remove(kmi)
    addon_keymaps_view3d.clear()
    for km, kmi in addon_keymaps_properties:
        km.keymap_items.remove(kmi)
    addon_keymaps_properties.clear()

if __name__ == "__main__":
    register()