#
#Autosave after each render to: //auto_saves/[filename]_[filenumber]-f[frame number].[extension]
#For Blender 2.79.
#Blender 2.8 version here: https://github.com/tomlechner/blender-stuff/tree/master/render-autosave
#
#
#Simplified BSD License
#
#Copyright (c) 2012, Florian Meyer, tstscr@web.de
#original version: http://projects.blender.org/tracker/index.php?func=detail&aid=32491
#Modified to include frame number.
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
#modification, are permitted provided that the following conditions are met: 
#
#1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer. 
#2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution. 
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#################################################################
bl_info = {
    "name": "Auto Save Render",
    "author": "tstscr",
    "version": (1, 0),
    "blender": (2, 63, 0),
    "location": "Rendertab -> Render Panel",
    "description": "Automatically save the image after rendering",
    "warning": "",
    "wiki_url":    "https://github.com/tomlechner/blender-stuff/tree/master/render-autosave"
    "tracker_url": "https://github.com/tomlechner/blender-stuff/issues",
    "category": "Render"}
###########################################################################
import bpy
from bpy.props import BoolProperty, EnumProperty
from bpy.app.handlers import persistent
from os.path import dirname, exists, join
from bpy.path import basename
from os import mkdir, listdir
from re import findall


@persistent
def auto_save_render(scene):
    if not scene.save_after_render or not bpy.data.filepath:
        return
    rndr = scene.render
    original_format = rndr.image_settings.file_format

    format = rndr.image_settings.file_format
    if   format == 'BMP': extension = '.bmp'
    elif format == 'OPEN_EXR_MULTILAYER': extension = '.exr'
    elif format == 'JPEG': extension = '.jpg'
    elif format == 'PNG': extension = '.png'
    elif format == 'IRIS': extension = '.iris'
    elif format == 'JPEG2000': extension = '.jpg'
    elif format == 'TARGA': extension = '.tga'
    elif format == 'TARGA_RAW': extension = '.tga'
    elif format == 'CINEON': extension = '.cineon'
    elif format == 'DPX': extension = '.dpx'
    elif format == 'OPEN_EXR': extension = '.exr'
    elif format == 'HDR': extension = '.hdr'
    elif format == 'TIFF': extension = '.tif'

#    format = rndr.image_settings.file_format = scene.auto_save_format
#    if format == 'OPEN_EXR_MULTILAYER': extension = '.exr'
#    if format == 'JPEG': extension = '.jpg'
#    if format == 'PNG': extension = '.png'
    
    blendname = basename(bpy.data.filepath).rpartition('.')[0]
    filepath = dirname(bpy.data.filepath) + '/auto_saves'
    
    if not exists(filepath):
        mkdir(filepath)
        
    if scene.auto_save_subfolders:
        filepath = join(filepath, blendname)
        if not exists(filepath):
            mkdir(filepath)

    #imagefiles starting with the blendname
    files = [f for f in listdir(filepath) \
            if f.startswith(blendname) \
            and f.lower().endswith(('.png', '.jpg', '.jpeg', '.exr'))]
    
    highest = 0
    if files:
        for f in files:
            #find last numbers in the filename after the blendname
            suffix = findall('\d+', f.split(blendname)[-1])
            if suffix:
                if int(suffix[0]) > highest:
                    highest = int(suffix[0])
    
    framenum = bpy.context.scene.frame_current
    save_name = join(filepath, blendname) + '_' + str(highest+1).zfill(3) + "-f" + str(framenum) + extension

    image = bpy.data.images['Render Result']
    if not image:
        print('Auto Save: Render Result not found. Image not saved')
        return
    
    print('Auto_Save:', save_name)
    image.save_render(save_name, scene=bpy.context.scene)

    rndr.image_settings.file_format = original_format

###########################################################################
def auto_save_UI(self, context):
    layout = self.layout
    
    row = layout.row()
    row.prop(context.scene, 'save_after_render', text='Auto Save', toggle=False)
    row.prop(context.scene, 'auto_save_subfolders', toggle=False)
    
def register():
    bpy.types.Scene.save_after_render = BoolProperty(
                    name='Save after render',
                    default=True,
                    description='Automatically save rendered images into: //auto_save/')
#    bpy.types.Scene.auto_save_format = EnumProperty(
#                    name='Auto Save File Format',
#                    description='File Format for the auto saves.',
#                    items={
#                    ('PNG', 'png', 'Save as png'),
#                    ('JPEG', 'jpg', 'Save as jpg'),
#                    ('OPEN_EXR_MULTILAYER', 'exr', 'Save as multilayer exr')},
#                    default='PNG')
    bpy.types.Scene.auto_save_subfolders = BoolProperty(
                    name='subfolder',
                    default=False,
                    description='Save into individual subfolders per blend name')
    bpy.app.handlers.render_post.append(auto_save_render)
    bpy.types.RENDER_PT_render.append(auto_save_UI)
    
def unregister():
    del(bpy.types.Scene.save_after_render)
#    del(bpy.types.Scene.auto_save_format)
    del(bpy.types.Scene.auto_save_subfolders)
    bpy.app.handlers.render_post.remove(auto_save_render)
    bpy.types.RENDER_PT_render.remove(auto_save_UI)

if __name__ == "__main__":
    register()
