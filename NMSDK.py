from bpy.props import StringProperty, BoolProperty  # noqa pylint: disable=import-error, no-name-in-module
import bpy

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper, ImportHelper  # noqa pylint: disable=import-error
from bpy.types import Operator, PropertyGroup  # noqa pylint: disable=import-error, no-name-in-module

from .ModelImporter.import_scene import ImportScene
from .ModelExporter.addon_script import Exporter

from .utils.settings import read_settings, write_settings


# operators to be used for the public API


class ImportSceneOperator(Operator):
    """ Import an entire scene into the current blender context."""
    bl_idname = "nmsdk.import_scene"
    bl_label = "Import NMS Scene file"

    path = StringProperty(default="")

    def execute(self, context):
        importer = ImportScene(self.path, parent_obj=None, ref_scenes=dict())
        importer.render_scene()
        return importer.state


class ImportMeshOperator(Operator):
    """ Import one or more individual meshes from a single scene into the
    current blender context. """
    bl_idname = "nmsdk.import_mesh"
    bl_label = "Import NMS meshes"

    path = StringProperty(default="")
    mesh_id = StringProperty(default="")

    def execute(self, context):
        importer = ImportScene(self.path, parent_obj=None, ref_scenes=dict())
        importer.render_mesh(str(self.mesh_id))
        return importer.state


# Private operators for internal use


class _FixOldFormat(Operator):
    """Change the type of node an object has"""
    bl_idname = "nmsdk._fix_old_format"
    bl_label = "Change NMS Node type"

    def execute(self, context):
        try:
            context.scene.objects[
                'NMS_SCENE'].NMSNode_props.node_types = 'Reference'
            return {'FINISHED'}
        except KeyError:
            return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class _ToggleCollisionVisibility(Operator):
    """Toggle whether the collision objects are visible or not"""
    bl_idname = "nmsdk._toggle_collision_visibility"
    bl_label = "Toggle collision visibility"

    def execute(self, context):
        nmsdk_settings = context.scene.nmsdk_settings
        nmsdk_settings.toggle_collision_visibility()
        # For every collision object in the scene, set its visibility to the
        # value specified by the `show_collisions` button.
        for obj in bpy.context.scene.objects:
            if obj.NMSNode_props.node_types == 'Collision':
                obj.hide = not nmsdk_settings.show_collisions
        return {'FINISHED'}


class _SaveDefaultSettings(Operator):
    """Save any default settings"""
    bl_idname = "nmsdk._save_default_settings"
    bl_label = "Save Settings"

    def execute(self, context):
        default_settings = context.scene.default_settings
        default_settings.save()


class NMSDKSettings(PropertyGroup):
    show_collisions = BoolProperty(
        name='Draw collisions',
        description='Whether or not to draw the collision objects.',
        default=False)

    def toggle_collision_visibility(self):
        """ Toggle the collision visibility state. """
        self.show_collisions = not self.show_collisions


class NMSDKDefaultSettings(PropertyGroup):

    default_settings = read_settings()

    export_directory = StringProperty(
        name="Export Directory",
        description="The base path under which all models will be exported.",
        default=default_settings['export_directory'])
    group_name = StringProperty(
        name="Group Name",
        description="Group name so that models that all belong in the same "
                    "folder are placed there (path becomes group_name/name)",
        default=default_settings['group_name'])

    def save(self):
        """ Save the current settings. """
        settings = {'export_directory': self.export_directory,
                    'group_name': self. group_name}
        write_settings(settings)
    # TODO: add load method?


# operators to be added to the blender UI for various tasks


class NMS_Export_Operator(Operator, ExportHelper):
    """Export scene to NMS compatible files"""
    # important since its how bpy.ops.import_test.some_data is constructed
    bl_idname = "export_mesh.nms"
    bl_label = "Export to NMS XML Format"

    export_directory = StringProperty(
        name="Export Directory",
        description="The base path under which all models will be exported.",
        default="CUSTOMMODELS")
    group_name = StringProperty(
        name="Group Name",
        description="Group name so that models that all belong in the same "
                    "folder are placed there (path becomes group_name/name)")
    AT_only = BoolProperty(
        name="ActionTriggers Only",
        description="If this box is ticked, all the action trigger data will "
                    "be exported directly to an ENTITY file in the specified "
                    "location with the project name. Anything else in the "
                    "project is ignored",
        default=False)
    no_vert_colours = BoolProperty(
        name="Don't export vertex colours",
        description="Ticking this box will force vertex colours to not be "
                    "exported. Use this if you have accidentally added vertex "
                    "colours to a mesh and don't know how to get rid of them.",
        default=False)

    # ExportHelper mixin class uses this
    filename_ext = ""

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'export_directory')
        layout.prop(self, 'group_name')
        layout.prop(self, 'AT_only')
        layout.prop(self, 'no_vert_colours')

    def execute(self, context):
        keywords = self.as_keywords()
        main_exporter = Exporter(self.filepath, settings=keywords)
        status = main_exporter.state
        self.report({'INFO'}, "Models Exported Successfully")
        if status:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class NMS_Import_Operator(Operator, ImportHelper):
    """Import NMS Scene files"""
    # important since its how bpy.ops.import_test.some_data is constructed
    bl_idname = "import_mesh.nms"
    bl_label = "Import from SCENE.EXML"

    # ExportHelper mixin class uses this
    filename_ext = ".EXML"

    clear_scene = BoolProperty(
        name='Clear scene',
        description='Whether or not to clear the currently exiting scene in '
                    'blender.',
        default=True)

    draw_hulls = BoolProperty(
        name='Draw bounded hulls',
        description='Whether or not to draw the points that make up the '
                    'bounded hulls of the materials. This is only for research'
                    '/debugging, so can safely be left as False.',
        default=False)
    import_collisions = BoolProperty(
        name='Import collisions',
        description='Whether or not to import the collision objects.',
        default=True)
    show_collisions = BoolProperty(
        name='Draw collisions',
        description='Whether or not to draw the collision objects.',
        default=False)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'draw_hulls')
        layout.prop(self, 'clear_scene')
        coll_box = layout.box()
        coll_box.prop(self, 'import_collisions')
        coll_box.prop(self, 'show_collisions')

    def execute(self, context):
        keywords = self.as_keywords()
        # set the state of the show_collisions button from the value specified
        # when the import occurs
        context.scene.nmsdk_settings.show_collisions = self.show_collisions
        fdir = self.properties.filepath
        print(fdir)
        importer = ImportScene(fdir, parent_obj=None, ref_scenes=dict(),
                               settings=keywords)
        importer.render_scene()
        status = importer.state
        self.report({'INFO'}, "Models Imported Successfully")
        print('Scene imported!')
        if status:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
