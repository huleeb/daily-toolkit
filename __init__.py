import bpy
import rna_keymap_ui
import json
from . import addon_updater_ops

bl_info = {
    "name": "Daily Toolkit",
    "author": "huleeb & stupidgiant",
    "blender": (4, 0, 0),
    "version": (0, 2, 1),
    "location": "View3D > Tools > daily",
    "category": "Generic",
    "description": "utility functions to speed up workflow"
}

#TODO:
#	- when mouse is over modifier window 
#   	have shortcuts specific:
#		- ctrl-m for mask modifier and create Vertex Group 'Group'
#   - EasyBake
#   - Feature:
#       - shortcut for mask modifier to selected object [0]
#           - vertex group called 'mask'
#           - add mask modifier and vertex group to 'mask'
#           - go in edit mode
#   - Custom plan
#       - backdrop stupidgiant
#   - shortcut to hide all visibility on selected objects
#
#   - Shortcut to UV Cube unwrap

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

# add light menu items
def draw_light_menu(self, context):
    layout = self.layout
    layout.operator("toolkit.area_no_scatter", text="Area no scatter", icon='LIGHT_HEMI')

# add mesh menu items
def draw_mesh_menu(self, context):
    layout = self.layout
    layout.operator("toolkit.subdivplane", text="Subdivided Plane", icon='MESH_PLANE')
    layout.operator("toolkit.backdroplane", text="Backdrop Plane", icon='MESH_PLANE')
    

def draw_volume_menu(self, context):
    layout = self.layout
    layout.operator("toolkit.fog_cube", text="Fog Cube", icon='SNAP_VOLUME')

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
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if bpy.context.selected_objects:
            obj = bpy.context.selected_objects[0]
            
            new_obj = obj.copy()
            new_obj.name = obj.name + "_decimated"
            new_obj.data = obj.data.copy()
            bpy.context.collection.objects.link(new_obj)
            
            # reset transform of original object to prevent offsets
            obj.location = (0.0, 0.0, 0.0)
            obj.rotation_euler = (0.0, 0.0, 0.0)
            obj.scale = (1.0, 1.0, 1.0)
            
            obj.parent = new_obj
            obj.display_type = 'BOUNDS'
            
            bpy.context.view_layer.objects.active = new_obj
            
            mod_dec = new_obj.modifiers.new(type='DECIMATE', name='Decimate')
            new_obj.modifiers["Decimate"].ratio = 0.1
            bpy.ops.object.modifier_apply(modifier=mod_dec.name)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.mark_seam(clear=False)
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0)
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
            
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
    bl_options = {'REGISTER', 'UNDO'}

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
    bl_options = {'REGISTER', 'UNDO'}

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

class AreaLightNoScatter(bpy.types.Operator):
    """Area light without volume scatter visibility"""
    bl_idname = "toolkit.area_no_scatter"
    bl_label = "Area Light Scatter"

    def execute(self, context):
        bpy.ops.object.light_add(type='AREA', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        bpy.context.object.visible_volume_scatter = False
        bpy.context.object.visible_volume_scatter = False
        bpy.context.object.data.shape = 'DISK'
        return {'FINISHED'}

class AddSubDividedPlane(bpy.types.Operator):
    """Add subdivided plane"""
    bl_idname = "toolkit.subdivplane"
    bl_label = "Subdivided Plane"

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=10, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=15)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.subdivision_set(level=1, relative=False)
        bpy.ops.object.shade_smooth()

        return {'FINISHED'}
    
class AddBackDropPlane(bpy.types.Operator):
    """Add backdrop plane"""
    bl_idname = "toolkit.backdroplane"
    bl_label = "Backdrop Plane"

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=10, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        # bpy.ops.mesh.select_all(action='DESELECT')

        selected_edge = None
        for edge in bpy.context.active_object.data.edges:
            if (edge.vertices[0] == 0 and edge.vertices[1] == 1) or (edge.vertices[0] == 1 and edge.vertices[1] == 0):
                edge.select = True
                selected_edge = edge
                break
        
        #bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 10), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":7.40025, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "use_duplicated_keyframes":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "alt_navigation":True, "use_automerge_and_split":False})
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, 10)})
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.object.modifier_add(type='BEVEL')
        bpy.context.object.modifiers["Bevel"].width = 3
        bpy.context.object.modifiers["Bevel"].segments = 15
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.shade_smooth()

        return {'FINISHED'}

class CamCenterGuide(bpy.types.Operator):
    bl_label = "Camera Center Guide"
    bl_idname = "toolkit.camcenterguide"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        global cam_x_og
        if bpy.context.scene.render.resolution_x is not 250:
            cam_x_og = bpy.context.scene.render.resolution_x
            bpy.context.scene.render.resolution_x = 250
        else:
            bpy.context.scene.render.resolution_x = cam_x_og
        return {'FINISHED'}
    
class FogCube(bpy.types.Operator):
    """Add fog cube using default node shader"""
    bl_idname = "toolkit.fog_cube"
    bl_label = "Fog Cube"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        bpy.ops.object.editmode_toggle()
        bpy.ops.transform.translate(value=(0, 0, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        bpy.ops.object.editmode_toggle()

        cube = bpy.context.active_object
        mesh = cube.data

        # deselect all
        for i in mesh.polygons:
            i.select=False
        for i in mesh.edges:
            i.select=False
        for i in mesh.vertices:
            i.select=False
        
        # top face
        minZ = float('inf')
        maxZ = float('inf') * -1
        for face in mesh.polygons:
            Z = face.center[2]
            if Z < minZ:
                minZ = Z
                bottom_face = face
            if Z > maxZ:
                maxZ = Z
                top_face = face
        top_face.select = True
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.transform.resize(value=(69.5371, 69.5371, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        bpy.ops.transform.translate(value=(0, 0, 29.1039), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        bpy.ops.object.editmode_toggle()

        # deselect all
        for i in mesh.polygons:
            i.select=False
        for i in mesh.edges:
            i.select=False
        for i in mesh.vertices:
            i.select=False

        # bottom top face
        minZ = float('inf')
        for face in mesh.polygons:
            Z = face.center[2]
            if Z < minZ:
                minZ = Z
                bottom_face = face

        bottom_face.select = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.transform.resize(value=(69.5371, 69.5371, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False)
        bpy.ops.object.editmode_toggle()

        bpy.context.object.display_type = 'BOUNDS'
        bpy.context.object.name = "VOLUME"

        cube.data.materials.append(bpy.data.materials.get("VOLUME"))
        return {'FINISHED'}

addon_keymaps = []
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
		mainrow = layout.row()
		col = mainrow.column()

		def draw_keymap(category, idname):
			km = kc.keymaps[category]
			kmi = km.keymap_items[idname]
			layout.context_pointer_set('keymap', km)
			rna_keymap_ui.draw_kmi([], kc, km, kmi, right, 0)

		addon_updater_ops.update_settings_ui(self, context)

		wm = bpy.context.window_manager
		kc = wm.keyconfigs.user
		if kc:
			layout.label(text="Shortcuts:", icon='OPTIONS')
			print(addon_keymaps)
			for cat, km, kmi, idname in addon_keymaps:
				km = kc.keymaps[cat]
				kmi = km.keymap_items[idname]
				row = layout.row()
				layout.context_pointer_set('keymap', km)
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
    ToggleGrayScale,
    AreaLightNoScatter,
    AddSubDividedPlane,
    AddBackDropPlane,
    CamCenterGuide,
    FogCube
)

def register():
    addon_updater_ops.register(bl_info)

    bpy.types.VIEW3D_MT_light_add.prepend(draw_light_menu)
    bpy.types.VIEW3D_MT_mesh_add.prepend(draw_mesh_menu)
    bpy.types.VIEW3D_MT_volume_add.prepend(draw_volume_menu)

    for cls in classes:
        addon_updater_ops.make_annotations(cls)
        bpy.utils.register_class(cls)
    register_keymap()
    
def unregister():
    addon_updater_ops.unregister()

    bpy.types.VIEW3D_MT_light_add.remove(draw_light_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(draw_mesh_menu)

    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
             continue
    unregister_keymaps()


def register_keymap():
    # Function to easily create Custom Shortcut in the preference panel
    def add_key_to_map(kc,category='3D View',space_type='VIEW_3D',cls='',key='',action='PRESS',shift=False,alt=False,ctrl=False):
        if kc:
            kmi = km.keymap_items.new(cls, key, action, shift=shift, alt=alt, ctrl=ctrl)
            addon_keymaps.append((category,km, kmi,cls))

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon.keymaps
    category = '3D View'
    km = kc[category] if kc.get(category) else kc.new(name=category)

    add_key_to_map(kc,category='3D View',cls='toolkit.toggle_orbit',key='X',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,category='3D View',cls='toolkit.easy_decimate',key='D',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,category='3D View',cls='toolkit.outliner_filter_restricted',key='K',shift=False,alt=False,ctrl=False)
    add_key_to_map(kc,category='3D View',cls='toolkit.material_setting_to_bump_only',key='B',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,category='3D View',cls='toolkit.flip_aspect_ratio',key='P',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,category='3D View',cls='toolkit.gray_scale',key='L',shift=True,alt=True,ctrl=True)
    add_key_to_map(kc,category='3D View',cls='toolkit.camcenterguide',key='C',shift=True,alt=True,ctrl=True)

def unregister_keymaps():
    for cat, km, kmi, idname in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    for cat, km, kmi, idname in addon_keymaps_properties:
        km.keymap_items.remove(kmi)
    addon_keymaps_properties.clear()

if __name__ == "__main__":
    register()