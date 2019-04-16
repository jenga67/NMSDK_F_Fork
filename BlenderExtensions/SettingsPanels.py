import bpy
from bpy.props import (StringProperty, BoolProperty, EnumProperty, IntProperty,
                       FloatProperty, PointerProperty, CollectionProperty)


class ImportSettings(bpy.types.PropertyGroup):
    cache_exml = BoolProperty(
        name='Cache converted EXML files',
        description='Whether to save the converted .EXML files in the same '
                    'directory as the source .MBIN files.\n'
                    'If this is checked, viewing models that have previously '
                    'been viewed will be faster.',
        default=True)


class ImportSettingsPanel(bpy.types.Panel):
    bl_idname = 'ImportSettingsPanel'
    bl_label = 'Import Settings'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'NMSDK'
    bl_context = 'objectmode'

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.prop(scene.NMSDK_import_settings, "cache_exml")


class SettingsPanels():

    @staticmethod
    def register():
        # Register properties
        bpy.utils.register_class(ImportSettings)
        # Register the internal variables
        bpy.types.Scene.NMSDK_import_settings = bpy.props.PointerProperty(
            type=ImportSettings)
        # Register panels
        bpy.utils.register_class(ImportSettingsPanel)

    @staticmethod
    def unregister():
        # Unregister properties
        bpy.utils.unregister_class(ImportSettings)
        # Remove the internal variables
        del bpy.types.Scene.NMSDK_import_settings
        # Unregister panels
        bpy.utils.unregister_class(ImportSettingsPanel)
