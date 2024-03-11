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
#   - Fix EasyDecimate Rotation
#        - When an object is not at center and rotated the low poly object doesn't match the original transform
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

class OutlinerFilterRestricted(bpy.types.Operator):
    """Removes Viewport and Selectable restricted filters in outliner"""
    bl_label = "Outliner Filter"
    bl_idname = "toolkit.outliner_filter_restricted"

    def execute(self, context):
        execute_outliner_filter_restricted()
        return {'FINISHED'}

class FlipAspectRatio(bpy.types.Operator):
    """Toggles aspect ratio between portrait to landscape"""
    bl_label = "Flip Aspect Ratio"
    bl_idname = "toolkit.flip_aspect_ratio"

    def execute(self, context):
        x = bpy.context.scene.render.resolution_x
        y = bpy.context.scene.render.resolution_y
        bpy.context.scene.render.resolution_x = y
        bpy.context.scene.render.resolution_y = x
        return {'FINISHED'}

is_orbit_around_selection = False

class ToggleOrbitAroundSelectionOperator(bpy.types.Operator):
    """Orbit Around Selection"""
    bl_idname = "toolkit.toggle_orbit"
    bl_label = "Orbit Around Selection"

    def execute(self, context):
        global is_orbit_around_selection
        current_state = bpy.context.preferences.inputs.use_rotate_around_active
        
        bpy.context.preferences.inputs.use_rotate_around_active = not current_state

        is_orbit_around_selection = not is_orbit_around_selection
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        
        if not current_state:
            self.report({'INFO'}, 'Orbit Around Selection: ON')
        else:
            self.report({'INFO'}, 'Orbit Around Selection: OFF')
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

class MaterialSettingToBumpOnly(bpy.types.Operator):
    bl_label = "Bump Only"
    bl_idname = "toolkit.material_setting_to_bump_only"

    def set_material_displacement_to_bump_only(self,material):
        if material.use_nodes:
            principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
            if principled_bsdf:
                material.cycles.displacement_method = 'BUMP'
    
    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data.materials:
                for material_slot in obj.material_slots:
                    if material_slot.material:
                        self.set_material_displacement_to_bump_only(material_slot.material)
        self.report({'INFO'}, 'Set all material displacement method to: Bump')
        return {'FINISHED'}

class ModifierMask(bpy.types.Operator):
    """Adds a Mask modifier to every selected object. Along with an empty Vertex Group"""
    bl_label = "Mask Modifier"
    bl_idname = "toolkit.modifier_mask" 

#     if bpy.context.space_data.context == 'MODIFIER':
# AttributeError: 'SpaceView3D' object has no attribute 'context'

    def execute(self, context):
        if bpy.context.selected_objects:
            try:
                self.report({'INFO'}, str(bpy.context.selected_objects))
                if bpy.context.space_data.context == 'MODIFIER':
                    for obj in bpy.context.selected_objects:
                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.vertex_group_add()
                        mod_dec = obj.modifiers.new(type='MASK', name='Mask')
                bpy.ops.ed.undo_push()
            except:
                pass
        return {'FINISHED'}

is_gray_scale = False

class ToggleGrayScale(bpy.types.Operator):
    """Gray Scale"""
    bl_label = "Gray Scale"
    bl_idname = "toolkit.gray_scale"

    def execute(self, context):
        bpy.context.space_data.shading.use_compositor = 'ALWAYS'
        tree = context.scene.node_tree

        composite_node = None
        last_node = None
        grayscale_node = None
        grayscale_node_name = 'toolkit.grayscale'
        global is_gray_scale

        for node in tree.nodes:
            if node.type == 'COMPOSITE':
                composite_node = node
                input_socket = node.inputs[0] 
                if input_socket.is_linked:
                    linked_socket = input_socket.links[0].from_socket
                    last_node = linked_socket.node
            if node.label == grayscale_node_name:
                 grayscale_node = node

        if grayscale_node == None:
            color_ramp_node = tree.nodes.new('CompositorNodeValToRGB')
            color_ramp_node.location = (last_node.location.x + 200, last_node.location.y)
            color_ramp_node.label = color_ramp_node.name = grayscale_node_name

            if last_node:
                tree.links.new(last_node.outputs[0], color_ramp_node.inputs[0])
            if composite_node:
                tree.links.new(color_ramp_node.outputs[0], composite_node.inputs[0])
        else:
            grayscale_node.mute = not grayscale_node.mute
            is_gray_scale = not is_gray_scale
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

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
        layout.label(text="Viewport:")
        layout.operator("toolkit.material_setting_to_bump_only")
        layout.operator("toolkit.flip_aspect_ratio")
        layout.operator("toolkit.toggle_orbit", depress=is_orbit_around_selection)
        layout.operator("toolkit.easy_decimate")

        layout.label(text="Compositor:")
        layout.operator("toolkit.gray_scale", depress=is_gray_scale)
        
        layout.label(text="Outliner:")
        layout.operator("toolkit.outliner_filter_restricted")


classes = (
	AddonPreference,
	UpdaterPanel,
    ToggleOrbitAroundSelectionOperator,
    EasyDecimate,
    DAILY_PT_toolkit_panel,
    MaterialSettingToBumpOnly,
    OutlinerFilterRestricted,
    FlipAspectRatio,
    ModifierMask,
    ToggleGrayScale
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
    if space_type == 'EMPTY':
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
    add_key_to_map(kc,config='3D View',cls='toolkit.gray_scale',key='L',shift=True,alt=True,ctrl=True)

	# Properties shortcuts:
    #add_key_to_map(kc,config='Object Mode',space_type='EMPTY',cls='toolkit.modifier_mask',key='M',shift=False,alt=False,ctrl=True)


def unregister_keymaps():
    for km, kmi in addon_keymaps_view3d:
        km.keymap_items.remove(kmi)
    addon_keymaps_view3d.clear()
    for km, kmi in addon_keymaps_properties:
        km.keymap_items.remove(kmi)
    addon_keymaps_properties.clear()

if __name__ == "__main__":
    register()